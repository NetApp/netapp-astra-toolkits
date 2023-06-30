#!/usr/bin/env python3
"""
   Copyright 2023 NetApp, Inc

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import json
import kubernetes
import sys
import time


import astraSDK
import tkSrc


def doClone(
    cloneAppName,
    clusterID,
    oApp,
    namespaceMapping,
    cloneStorageClass,
    backupID,
    snapshotID,
    sourceAppID,
    background,
    pollTimer,
    resourceFilter,
    verbose,
    quiet,
):
    """Create a clone."""
    # Check to see if cluster-level resources are needed to be manually created
    needsIngressclass = False
    appAssets = astraSDK.apps.getAppAssets(verbose=verbose).main(oApp["id"])
    for asset in appAssets["items"]:
        if (
            "nginx-ingress-controller" in asset["assetName"]
            or "ingress-nginx-controller" in asset["assetName"]
        ) and asset["assetType"] == "Pod":
            needsIngressclass = True
            assetName = asset["assetName"]
            if namespaceMapping is None:
                cloneNamespace = asset["namespace"]
            else:
                for nsm in namespaceMapping:
                    if nsm["source"] == asset["namespace"]:
                        cloneNamespace = nsm["destination"]
    # Clone 'ingressclass' cluster object
    if needsIngressclass and oApp["clusterID"] != clusterID:
        clusters = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
        contexts, _ = kubernetes.config.list_kube_config_contexts()
        # Loop through clusters and contexts, find matches and open api_client
        for cluster in clusters["items"]:
            for context in contexts:
                if cluster["id"] == clusterID:
                    if cluster["name"] in context["name"]:
                        destClient = kubernetes.client.NetworkingV1Api(
                            api_client=kubernetes.config.new_client_from_config(
                                context=context["name"]
                            )
                        )
                elif cluster["id"] == oApp["clusterID"]:
                    if cluster["name"] in context["name"]:
                        sourceClient = kubernetes.client.NetworkingV1Api(
                            api_client=kubernetes.config.new_client_from_config(
                                context=context["name"]
                            )
                        )
        try:
            # Get the source cluster ingressclass and apply it to the dest cluster
            listResp = sourceClient.list_ingress_class(_preload_content=False, _request_timeout=5)
            for i in json.loads(listResp.data)["items"]:
                for asset in appAssets["items"]:
                    if "nginx" in i["metadata"]["name"] and asset["assetName"] == assetName:
                        for ilKey, ilValue in i["metadata"]["labels"].items():
                            for al in asset["labels"]:
                                if ilKey == al["name"] and ilValue == al["value"]:
                                    ingName = i["metadata"]["name"]
            sourceResp = sourceClient.read_ingress_class(
                ingName, _preload_content=False, _request_timeout=5
            )
            sourceIngress = json.loads(sourceResp.data)
            if sourceIngress["metadata"].get("resourceVersion"):
                del sourceIngress["metadata"]["resourceVersion"]
            if sourceIngress["metadata"].get("creationTimestamp"):
                del sourceIngress["metadata"]["creationTimestamp"]
            if sourceIngress["metadata"].get("uid"):
                del sourceIngress["metadata"]["uid"]
            if sourceIngress["metadata"]["managedFields"][0].get("time"):
                del sourceIngress["metadata"]["managedFields"][0]["time"]
            sourceIngress["metadata"]["labels"]["app.kubernetes.io/instance"] = cloneNamespace
            sourceIngress["metadata"]["annotations"]["meta.helm.sh/release-name"] = cloneNamespace
            sourceIngress["metadata"]["annotations"][
                "meta.helm.sh/release-namespace"
            ] = cloneNamespace
        except kubernetes.client.rest.ApiException:
            # In the event the sourceCluster no longer exists or isn't in kubeconfig
            sourceIngress = {
                "kind": "IngressClass",
                "apiVersion": "networking.k8s.io/v1",
                "metadata": {
                    "name": "nginx",
                    "generation": 1,
                    "labels": {
                        "app.kubernetes.io/component": "controller",
                        "app.kubernetes.io/instance": cloneNamespace,
                        "app.kubernetes.io/managed-by": "Helm",
                        "app.kubernetes.io/name": "ingress-nginx",
                        "app.kubernetes.io/version": "1.1.0",
                        "helm.sh/chart": "ingress-nginx-4.0.13",
                    },
                    "annotations": {
                        "meta.helm.sh/release-name": cloneNamespace,
                        "meta.helm.sh/release-namespace": cloneNamespace,
                    },
                    "managedFields": [
                        {
                            "manager": "helm",
                            "operation": "Update",
                            "apiVersion": "networking.k8s.io/v1",
                            "fieldsType": "FieldsV1",
                            "fieldsV1": {
                                "f:metadata": {
                                    "f:annotations": {
                                        ".": {},
                                        "f:meta.helm.sh/release-name": {},
                                        "f:meta.helm.sh/release-namespace": {},
                                    },
                                    "f:labels": {
                                        ".": {},
                                        "f:app.kubernetes.io/component": {},
                                        "f:app.kubernetes.io/instance": {},
                                        "f:app.kubernetes.io/managed-by": {},
                                        "f:app.kubernetes.io/name": {},
                                        "f:app.kubernetes.io/version": {},
                                        "f:helm.sh/chart": {},
                                    },
                                },
                                "f:spec": {"f:controller": {}},
                            },
                        }
                    ],
                },
                "spec": {"controller": "k8s.io/ingress-nginx"},
            }
            if "gitlab" in assetName:
                sourceIngress["metadata"]["name"] = "gitlab-nginx"
                sourceIngress["metadata"]["labels"]["release"] = cloneNamespace
                sourceIngress["metadata"]["labels"]["app"] = "nginx-ingress"
                sourceIngress["metadata"]["managedFields"][0]["fieldsV1"]["f:metadata"]["f:labels"][
                    "f:release"
                ] = {}
                sourceIngress["metadata"]["managedFields"][0]["fieldsV1"]["f:metadata"]["f:labels"][
                    "f:app"
                ] = {}
        try:
            # Add the ingressclass to the new cluster
            destClient.create_ingress_class(sourceIngress, _request_timeout=10)
        except NameError:
            raise SystemExit(f"Error: {clusterID} not found in kubeconfig")
        except kubernetes.client.rest.ApiException as e:
            # If the failure is due to the resource already existing, then we're all set,
            # otherwise it's more serious and we must raise an exception
            body = json.loads(e.body)
            if not (body.get("reason") == "AlreadyExists"):
                raise SystemExit(f"Error: Kubernetes resource creation failed\n{e}")

    cloneRet = astraSDK.apps.cloneApp(verbose=verbose, quiet=quiet).main(
        cloneAppName,
        clusterID,
        oApp["clusterID"],
        namespaceMapping=namespaceMapping,
        cloneStorageClass=cloneStorageClass,
        backupID=backupID,
        snapshotID=snapshotID,
        sourceAppID=sourceAppID,
        resourceFilter=resourceFilter,
    )
    if cloneRet:
        print("Submitting clone succeeded.")
        if background:
            print("Background clone flag selected, run 'list apps' to get status.")
            return True
        print("Waiting for clone to become available.", end="")
        sys.stdout.flush()
        appID = cloneRet.get("id")
        state = cloneRet.get("state")
        while state != "ready":
            apps = astraSDK.apps.getApps().main()
            for app in apps["items"]:
                if app["id"] == appID:
                    if app["state"] == "ready":
                        state = app["state"]
                        print("Cloning operation complete.")
                        sys.stdout.flush()
                    elif app["state"] == "failed":
                        sys.stdout.flush()
                        raise SystemExit(f"Error: \"{app['name']}\" in a failed state")
                    else:
                        print(".", end="")
                        sys.stdout.flush()
                        time.sleep(pollTimer)
    else:
        raise SystemExit("Submitting clone failed.")


def main(args, parser, ard):
    if (args.filterSelection and not args.filterSet) or (
        args.filterSet and not args.filterSelection
    ):
        parser.error("either both or none of --filterSelection and --filterSet should be specified")
    if args.filterSet and args.sourceAppID:
        parser.error(
            "resource filters (--filterSet) may only be specified with --backupID "
            "or --snapshotID arguments, not --sourceAppID"
        )
    if not args.cloneAppName:
        args.cloneAppName = input("App name for the clone: ")
    if not args.clusterID:
        if ard.needsattr("clusters"):
            ard.clusters = astraSDK.clusters.getClusters().main()
        print("Select destination cluster for the clone")
        print("Index\tClusterID\t\t\t\tclusterName\tclusterPlatform")
        args.clusterID = tkSrc.helpers.userSelect(ard.clusters, ["id", "name", "clusterType"])
    # Get the original app dictionary based on args.sourceAppID/args.backupID/args.snapshotID,
    # as the app dict contains sourceClusterID and namespaceScopedResources which we need
    oApp = {}
    # Handle -f/--fast/plaidMode cases
    if ard.needsattr("apps"):
        ard.apps = astraSDK.apps.getApps().main()
    if args.sourceAppID:
        for app in ard.apps["items"]:
            if app["id"] == args.sourceAppID:
                oApp = app
    elif args.backupID:
        if ard.needsattr("backups"):
            ard.backups = astraSDK.backups.getBackups().main()
        for app in ard.apps["items"]:
            for backup in ard.backups["items"]:
                if app["id"] == backup["appID"] and backup["id"] == args.backupID:
                    oApp = app
    elif args.snapshotID:
        if ard.needsattr("snapshots"):
            ard.snapshots = astraSDK.snapshots.getSnaps().main()
        for app in ard.apps["items"]:
            for snapshot in ard.snapshots["items"]:
                if app["id"] == snapshot["appID"] and snapshot["id"] == args.snapshotID:
                    oApp = app
    # Ensure appIDstr is not equal to "", if so bad values were passed in with plaidMode
    if not oApp:
        parser.error(
            "the corresponding appID was not found in the system, please check "
            + "your inputs and try again."
        )

    doClone(
        tkSrc.helpers.isRFC1123(args.cloneAppName),
        args.clusterID,
        oApp,
        tkSrc.helpers.createNamespaceMapping(oApp, args.cloneNamespace, args.multiNsMapping),
        args.cloneStorageClass,
        args.backupID,
        args.snapshotID,
        args.sourceAppID,
        args.background,
        args.pollTimer,
        tkSrc.helpers.createFilterSet(
            args.filterSelection, args.filterSet, astraSDK.apps.getAppAssets().main(oApp["id"])
        ),
        args.verbose,
        args.quiet,
    )
