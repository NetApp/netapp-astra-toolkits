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

import copy
import json
import kubernetes
import sys
import time
import yaml


import astraSDK
import tkSrc


def doClone(
    newAppName,
    clusterID,
    oApp,
    namespaceMapping,
    newStorageClass,
    backupID,
    snapshotID,
    sourceAppID,
    resourceFilter,
    pollTimer=5,
    background=False,
    verb="restore",
    verbose=False,
    quiet=False,
):
    """Create a clone/restore."""
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
        newAppName,
        clusterID,
        oApp["clusterID"],
        namespaceMapping=namespaceMapping,
        cloneStorageClass=newStorageClass,
        backupID=backupID,
        snapshotID=snapshotID,
        sourceAppID=sourceAppID,
        resourceFilter=resourceFilter,
    )
    if cloneRet:
        print(f"Submitting {verb} succeeded.")
        if background:
            print(f"Background {verb} flag selected, run 'list apps' to get status.")
            return True
        print(f"Waiting for {verb} to become available", end="")
        sys.stdout.flush()
        appID = cloneRet.get("id")
        state = cloneRet.get("state")
        while state != "ready":
            apps = astraSDK.apps.getApps().main()
            for app in apps["items"]:
                if app["id"] == appID:
                    if app["state"] == "ready":
                        state = app["state"]
                        print(f"{verb[:-1]}ing operation complete.")
                        sys.stdout.flush()
                    elif app["state"] == "failed":
                        sys.stdout.flush()
                        raise SystemExit(f"Error: \"{app['name']}\" in a failed state")
                    else:
                        time.sleep(pollTimer)
                        print(".", end="")
                        sys.stdout.flush()
    else:
        raise SystemExit(f"Submitting {verb} failed.")


def waitForAppArchivePath(dp_resp, v3):
    """Given a data protection creation response, wait for the 'status.appArchivePath' field
    to be populated in a get of the dp dict, then return that dict"""
    dp_name = dp_resp["metadata"]["name"]
    dp_plural = f"{dp_resp['kind'].lower()}s"
    get_K8s_obj = astraSDK.k8s.getResources(config_context=v3)
    dp_body = get_K8s_obj.main(dp_plural, keyFilter="metadata.name", valFilter=dp_name)["items"][0]
    counter = 0
    while not dp_body.get("status") or not dp_body["status"].get("appArchivePath"):
        if counter > 20:
            raise SystemExit(f"Could not get 'status.appArchivePath' from {dp_body=}")
        time.sleep(1)
        dp_body = get_K8s_obj.main(dp_plural, keyFilter="metadata.name", valFilter=dp_name)[
            "items"
        ][0]
        counter += 1
    return dp_body


def main(args, parser, ard):
    # Ensure proper use of resource filters
    if args.subcommand == "restore":
        if (args.filterSelection and not args.filterSet) or (
            args.filterSet and not args.filterSelection
        ):
            parser.error(
                "either both or none of --filterSelection and --filterSet should be specified"
            )

    if args.v3:
        # args.newNamespace is not required, but we do need it set for proper YAML generation
        if args.newNamespace is None and args.multiNsMapping is None:
            args.newNamespace = args.appName
        # Handle -f/--fast/plaidMode cases
        if ard.needsattr("apps"):
            ard.apps = astraSDK.k8s.getResources(config_context=args.v3).main("applications")

        # A live clone is just a snapshot (or backup for cross-cluster), and then the normal
        # restore operation. So we'll take care of the data protection operation here first,
        # then clone and restore will use the same operation after
        if args.subcommand == "clone":
            ard.buckets = astraSDK.k8s.getResources(config_context=args.v3).main("appvaults")
            bucketDict = ard.getSingleDict("buckets", "status.state", "available", parser)
            kind = "Snapshot"  # TODO: change to if/else+Backup depending on dest cluster
            appArchivePath = (
                "placeholder/this-is-a-placeholder-field-which-must-be-replaced-with/"
                + f"{kind}.status.appArchivePath"
            )
            template = tkSrc.helpers.setupJinja(kind.lower())
            v3_dp_dict = yaml.safe_load(
                template.render(
                    generateName=f"{args.sourceApp}-clone-{kind.lower()}-",
                    appName=args.sourceApp,
                    appVaultName=bucketDict["metadata"]["name"],
                )
            )
            if args.dry_run == "client":
                restoreSourceDict = v3_dp_dict
                print(yaml.dump(v3_dp_dict).rstrip("\n"))
                print("---")
            else:
                restoreSourceDict = astraSDK.k8s.createResource(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(
                    f"{v3_dp_dict['kind'].lower()}s",
                    v3_dp_dict["metadata"]["namespace"],
                    v3_dp_dict,
                    version="v1",
                    group="astra.netapp.io",
                )
                if not args.dry_run:
                    restoreSourceDict = waitForAppArchivePath(restoreSourceDict, args.v3)
            if args.dry_run:
                restoreSourceDict["status"] = {}
                restoreSourceDict["status"]["appArchivePath"] = appArchivePath

        # For restore, we need to figure out if a backup or a snapshot source was provided
        elif args.subcommand == "restore":
            if ard.needsattr("backups"):
                ard.backups = astraSDK.k8s.getResources(config_context=args.v3).main("backups")
            if ard.needsattr("snapshots"):
                ard.snapshots = astraSDK.k8s.getResources(config_context=args.v3).main("snapshots")
                ard.snapshots = astraSDK.snapshots.getSnaps().main()
            if args.restoreSource in ard.buildList("backups", "metadata.name"):
                restoreSourceDict = ard.getSingleDict(
                    "backups", "metadata.name", args.restoreSource, parser
                )
            elif args.restoreSource in ard.buildList("snapshots", "metadata.name"):
                restoreSourceDict = ard.getSingleDict(
                    "snapshots", "metadata.name", args.restoreSource, parser
                )
            else:
                parser.error(
                    f"the restoreSource '{args.restoreSource}' is not a valid backup or snapshot"
                )

        # Now we're ready to create the {kind}Restore and Application CRs
        oApp = ard.getSingleDict(
            "apps", "metadata.name", restoreSourceDict["spec"]["applicationRef"], parser
        )
        namespaceMapping = tkSrc.helpers.createNamespaceMapping(
            oApp["spec"]["includedNamespaces"], args.newNamespace, args.multiNsMapping, parser
        )
        template = tkSrc.helpers.setupJinja("restore")
        try:
            v3_gen = yaml.safe_load_all(
                template.render(
                    kind=restoreSourceDict["kind"],
                    restoreName=f"{args.appName}-restore-",
                    appArchivePath=restoreSourceDict["status"]["appArchivePath"],
                    appVaultRef=restoreSourceDict["spec"]["appVaultRef"],
                    namespaceMapping=tkSrc.helpers.prependDump(namespaceMapping, prepend=4),
                    appName=args.appName,
                    appSpec=tkSrc.helpers.prependDump(
                        tkSrc.helpers.updateNamespaceSpec(
                            namespaceMapping, copy.deepcopy(oApp["spec"])
                        ),
                        prepend=2,
                    ),
                )
            )
            if args.dry_run == "client":
                print(yaml.dump_all(v3_gen).rstrip("\n"))
            else:
                for v3_dict in v3_gen:
                    astraSDK.k8s.createResource(
                        quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                    ).main(
                        f"{v3_dict['kind'].lower()}s",
                        v3_dict["metadata"]["namespace"],
                        v3_dict,
                        version="v1",
                        group="astra.netapp.io",
                    )
        except KeyError as err:
            parser.error(
                f"{err} key not found in '{args.restoreSource}' object, please ensure "
                f"'{args.restoreSource}' is a valid backup/snapshot"
            )

    else:
        if ard.needsattr("apps"):
            ard.apps = astraSDK.apps.getApps().main()
        # Get the original app dictionary based on args.sourceApp/args.restoreSource,
        # as the app dict contains sourceCluster and namespaceScopedResources which we need
        oApp = {}
        backup = None
        snapshot = None
        if args.subcommand == "clone":
            # There are certain args that aren't available for live clones, set those to None
            args.filterSelection = None
            args.filterSet = None
            for app in ard.apps["items"]:
                if app["id"] == args.sourceApp:
                    oApp = app
        elif args.subcommand == "restore":
            args.sourceApp = None
            if ard.needsattr("backups"):
                ard.backups = astraSDK.backups.getBackups().main()
            if ard.needsattr("snapshots"):
                ard.snapshots = astraSDK.snapshots.getSnaps().main()
            if args.restoreSource in ard.buildList("backups", "id"):
                dataProtections = ard.backups
                backup = args.restoreSource
            elif args.restoreSource in ard.buildList("snapshots", "id"):
                dataProtections = ard.snapshots
                snapshot = args.restoreSource
            else:
                parser.error(
                    f"the restoreSource '{args.restoreSource}' is not a valid backup or snapshot"
                )
            for app in ard.apps["items"]:
                for dp in dataProtections["items"]:
                    if app["id"] == dp["appID"] and dp["id"] == args.restoreSource:
                        oApp = app
        # Ensure appIDstr is not equal to "", if so bad values were passed in with plaidMode
        if not oApp:
            parser.error(
                "the corresponding app was not found in the system, please check "
                + "your inputs and try again."
            )

        doClone(
            tkSrc.helpers.isRFC1123(args.appName),
            args.cluster,
            oApp,
            tkSrc.helpers.createNamespaceMapping(
                oApp["namespaceScopedResources"], args.newNamespace, args.multiNsMapping, parser
            ),
            args.newStorageClass,
            backup,
            snapshot,
            args.sourceApp,
            tkSrc.helpers.createFilterSet(
                args.filterSelection, args.filterSet, astraSDK.apps.getAppAssets().main(oApp["id"])
            ),
            pollTimer=args.pollTimer,
            background=args.background,
            verb=args.subcommand,
            verbose=args.verbose,
            quiet=args.quiet,
        )
