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

import base64
import json
import kubernetes
import sys
import time
import yaml
from datetime import datetime, timedelta

import astraSDK
import tkSrc


class ToolKit:
    def __init__(self):
        self.conf = astraSDK.common.getConfig().main()

    def doDeploy(self, chart, appName, namespace, setValues, fileValues, verbose, quiet):
        """Deploy a helm chart <chart>, naming the app <appName> into <namespace>"""

        setStr = tkSrc.helpers.createHelmStr("set", setValues)
        valueStr = tkSrc.helpers.createHelmStr("values", fileValues)

        nsObj = astraSDK.namespaces.getNamespaces(verbose=verbose)
        retval = tkSrc.helpers.run("kubectl get ns -o json", captureOutput=True)
        retvalJSON = json.loads(retval)
        for item in retvalJSON["items"]:
            if item["metadata"]["name"] == namespace:
                print(f"Namespace {namespace} already exists!")
                sys.exit(24)
        tkSrc.helpers.run(f"kubectl create namespace {namespace}")
        tkSrc.helpers.run(f"kubectl config set-context --current --namespace={namespace}")

        # If we're deploying gitlab, we need to ensure at least a premium storageclass
        # for postgresql and gitaly
        if chart.split("/")[1] == "gitlab":
            pgStorageClass = None
            scMapping = [
                ["standard-rwo", "premium-rwo"],
                ["netapp-cvs-perf-standard", "netapp-cvs-perf-premium"],
                ["azurefile", "azurefile-premium"],
                ["azurefile-csi", "azurefile-csi-premium"],
                ["managed", "managed-premium"],
                ["managed-csi", "managed-csi-premium"],
            ]
            configuration = kubernetes.config.load_kube_config()
            with kubernetes.client.ApiClient(configuration) as api_client:
                api_instance = kubernetes.client.StorageV1Api(api_client)
                api_response = api_instance.list_storage_class()
                for i in api_response.items:
                    if (
                        i.metadata.annotations.get("storageclass.kubernetes.io/is-default-class")
                        == "true"
                    ):
                        for sc in scMapping:
                            if i.metadata.name == sc[0]:
                                pgStorageClass = sc[1]
            if pgStorageClass:
                setStr += f" --set postgresql.global.storageClass={pgStorageClass}"
                setStr += f" --set gitlab.gitaly.persistence.storageClass={pgStorageClass}"

        tkSrc.helpers.run(f"helm install {appName} {chart}{setStr}{valueStr}")
        print("Waiting for Astra to discover the namespace", end="")
        sys.stdout.flush()

        appID = ""
        while not appID:
            # It takes Astra some time to realize new apps have been installed
            time.sleep(3)
            print(".", end="")
            sys.stdout.flush()
            namespaces = nsObj.main()
            # Cycle through the apps and see if one matches our new namespace
            for ns in namespaces["items"]:
                # Check to make sure our namespace name matches, it's in a discovered state,
                # and that it's a recently created namespace (less than 10 minutes old)
                if (
                    ns["name"] == namespace
                    and ns["namespaceState"] == "discovered"
                    and (
                        datetime.utcnow()
                        - datetime.strptime(
                            ns["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ"
                        )
                    )
                    < timedelta(minutes=10)
                ):
                    print(" Namespace discovered!")
                    sys.stdout.flush()
                    time.sleep(3)
                    print(f"Managing app: {ns['name']}.", end="")
                    sys.stdout.flush()
                    rc = astraSDK.apps.manageApp(verbose=verbose).main(
                        ns["name"], ns["name"], ns["clusterID"]
                    )
                    if rc:
                        appID = rc["id"]
                        print(" Success!")
                        sys.stdout.flush()
                        break
                    else:
                        sys.stdout.flush()
                        print("\nERROR managing app, trying one more time:")
                        rc = astraSDK.apps.manageApp(quiet=quiet, verbose=verbose).main(
                            ns["name"], ns["name"], ns["clusterID"]
                        )
                        if rc:
                            appID = rc["id"]
                            print("Success!")
                            break
                        else:
                            sys.exit(1)

        # Create a protection policy on that namespace (using its appID)
        time.sleep(5)
        backupRetention = "1"
        snapshotRetention = "1"
        minute = "0"
        cpp = astraSDK.protections.createProtectionpolicy(quiet=True)
        cppData = {
            "hourly": {"dayOfWeek": "*", "dayOfMonth": "*", "hour": "*"},
            "daily": {"dayOfWeek": "*", "dayOfMonth": "*", "hour": "2"},
            "weekly": {"dayOfWeek": "0", "dayOfMonth": "*", "hour": "2"},
            "monthly": {"dayOfWeek": "*", "dayOfMonth": "1", "hour": "2"},
        }
        for period in cppData:
            print(f"Setting {period} protection policy on {appID}")
            dayOfWeek = cppData[period]["dayOfWeek"]
            dayOfMonth = cppData[period]["dayOfMonth"]
            hour = cppData[period]["hour"]
            cppRet = cpp.main(
                period,
                backupRetention,
                snapshotRetention,
                dayOfWeek,
                dayOfMonth,
                hour,
                minute,
                appID,
            )
            if cppRet is False:
                raise SystemExit(f"cpp.main({period}...) returned False")

    def doClone(
        self,
        cloneAppName,
        clusterID,
        oApp,
        namespaceMapping,
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
                listResp = sourceClient.list_ingress_class(
                    _preload_content=False, _request_timeout=5
                )
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
                sourceIngress["metadata"]["annotations"][
                    "meta.helm.sh/release-name"
                ] = cloneNamespace
                sourceIngress["metadata"]["annotations"][
                    "meta.helm.sh/release-namespace"
                ] = cloneNamespace
            except:
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
                    sourceIngress["metadata"]["managedFields"][0]["fieldsV1"]["f:metadata"][
                        "f:labels"
                    ]["f:release"] = {}
                    sourceIngress["metadata"]["managedFields"][0]["fieldsV1"]["f:metadata"][
                        "f:labels"
                    ]["f:app"] = {}
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
            backupID=backupID,
            snapshotID=snapshotID,
            sourceAppID=sourceAppID,
            resourceFilter=resourceFilter,
        )
        if cloneRet:
            print("Submitting clone succeeded.")
            if background:
                print(f"Background clone flag selected, run 'list apps' to get status.")
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
                            print(f"Error: \"{app['name']}\" in a failed state")
                            sys.stdout.flush()
                            sys.exit(1)
                        else:
                            print(".", end="")
                            sys.stdout.flush()
                            time.sleep(pollTimer)
        else:
            print("Submitting clone failed.")

    def doProtectionTask(self, protectionType, appID, name, background, pollTimer, quiet, verbose):
        """Take a snapshot/backup of appID giving it name <name>
        Return the snapshotID/backupID of the backup taken or False if the protection task fails"""
        if protectionType == "backup":
            protectionID = astraSDK.backups.takeBackup(quiet=quiet, verbose=verbose).main(
                appID, name
            )
        elif protectionType == "snapshot":
            protectionID = astraSDK.snapshots.takeSnap(quiet=quiet, verbose=verbose).main(
                appID, name
            )
        if protectionID == False:
            return False

        print(f"Starting {protectionType} of {appID}")
        if background:
            print(
                f"Background {protectionType} flag selected, run 'list {protectionType}s' to get status"
            )
            return True

        print(f"Waiting for {protectionType} to complete.", end="")
        sys.stdout.flush()
        while True:
            if protectionType == "backup":
                objects = astraSDK.backups.getBackups().main()
            elif protectionType == "snapshot":
                objects = astraSDK.snapshots.getSnaps().main()
            if not objects:
                # This isn't technically true.  Trying to list the backups/snapshots after taking
                # the protection job failed.  The protection job itself may eventually succeed.
                print(f"Taking {protectionType} failed")
                return False
            for obj in objects["items"]:
                # Just because the API call to create a backup/snapshot succeeded, that doesn't
                # mean the actual backup will succeed. So loop to show completed or failed.
                if obj["id"] == protectionID:
                    if obj["state"] == "completed":
                        print("complete!")
                        sys.stdout.flush()
                        return protectionID
                    elif obj["state"] == "failed":
                        print(f"{protectionType} job failed")
                        return False
            time.sleep(pollTimer)
            print(".", end="")
            sys.stdout.flush()


def main(cmdHeader, tkParser, ard):
    tk = ToolKit()
    parser = tkParser.main()
    args = parser.parse_args()

    if args.subcommand == "deploy":
        tk.doDeploy(
            args.chart,
            tkSrc.helpers.isRFC1123(args.app),
            args.namespace,
            args.set,
            args.values,
            args.verbose,
            args.quiet,
        )

    elif args.subcommand == "list" or args.subcommand == "get":
        if args.objectType == "apiresources":
            rc = astraSDK.apiresources.getApiResources(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(cluster=args.cluster)
            if rc is False:
                print("astraSDK.apiresources.getApiResources() failed")
                sys.exit(1)
        elif args.objectType == "apps":
            rc = astraSDK.apps.getApps(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                namespace=args.namespace,
                nameFilter=args.nameFilter,
                cluster=args.cluster,
            )
            if rc is False:
                print("astraSDK.apps.getApps() failed")
                sys.exit(1)
        elif args.objectType == "assets":
            rc = astraSDK.apps.getAppAssets(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(args.appID)
            if rc is False:
                print("astraSDK.apps.getAppAssets() failed")
        elif args.objectType == "backups":
            rc = astraSDK.backups.getBackups(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.backups.getBackups() failed")
                sys.exit(1)
        elif args.objectType == "buckets":
            rc = astraSDK.buckets.getBuckets(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(nameFilter=args.nameFilter, provider=args.provider)
            if rc is False:
                print("astraSDK.buckets.getBuckets() failed")
                sys.exit(1)
        elif args.objectType == "clouds":
            rc = astraSDK.clouds.getClouds(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(cloudType=args.cloudType)
            if rc is False:
                print("astraSDK.clouds.getClouds() failed")
                sys.exit(1)
        elif args.objectType == "clusters":
            rc = astraSDK.clusters.getClusters(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                hideManaged=args.hideManaged,
                hideUnmanaged=args.hideUnmanaged,
                nameFilter=args.nameFilter,
            )
            if rc is False:
                print("astraSDK.clusters.getClusters() failed")
                sys.exit(1)
        elif args.objectType == "credentials":
            rc = astraSDK.credentials.getCredentials(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(kubeconfigOnly=args.kubeconfigOnly)
            if rc is False:
                print("astraSDK.credentials.getCredentials() failed")
                sys.exit(1)
        elif args.objectType == "hooks":
            rc = astraSDK.hooks.getHooks(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.hooks.getHooks() failed")
                sys.exit(1)
        elif args.objectType == "protections":
            rc = astraSDK.protections.getProtectionpolicies(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.protections.getProtectionpolicies() failed")
                sys.exit(1)
        elif args.objectType == "replications":
            rc = astraSDK.replications.getReplicationpolicies(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.replications.getReplicationpolicies() failed")
                sys.exit(1)
        elif args.objectType == "namespaces":
            rc = astraSDK.namespaces.getNamespaces(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                clusterID=args.clusterID,
                nameFilter=args.nameFilter,
                showRemoved=args.showRemoved,
                unassociated=args.unassociated,
                minuteFilter=args.minutes,
            )
            if rc is False:
                print("astraSDK.namespaces.getNamespaces() failed")
                sys.exit(1)
        elif args.objectType == "notifications":
            rc = astraSDK.notifications.getNotifications(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                limit=args.limit,
                skip=args.offset,
                minuteFilter=args.minutes,
                severityFilter=args.severity,
            )
            if rc is False:
                print("astraSDK.namespaces.getNotifications() failed")
                sys.exit(1)
        elif args.objectType == "rolebindings":
            rc = astraSDK.rolebindings.getRolebindings(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(idFilter=args.idFilter)
            if rc is False:
                print("astraSDK.rolebindings.getRolebindings() failed")
                sys.exit(1)
        elif args.objectType == "scripts":
            if args.getScriptSource:
                args.quiet = True
                args.output = "json"
            rc = astraSDK.scripts.getScripts(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(nameFilter=args.nameFilter)
            if rc is False:
                print("astraSDK.scripts.getScripts() failed")
                sys.exit(1)
            else:
                if args.getScriptSource:
                    if len(rc["items"]) == 0:
                        print(f"Script of name '{args.nameFilter}' not found.")
                    for script in rc["items"]:
                        print("#" * len(f"### {script['name']} ###"))
                        print(f"### {script['name']} ###")
                        print("#" * len(f"### {script['name']} ###"))
                        print(base64.b64decode(script["source"]).decode("utf-8"))
        elif args.objectType == "snapshots":
            rc = astraSDK.snapshots.getSnaps(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.snapshots.getSnaps() failed")
                sys.exit(1)
        elif args.objectType == "storageclasses":
            rc = astraSDK.storageclasses.getStorageClasses(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(cloudType=args.cloudType)
            if rc is False:
                print("astraSDK.storageclasses.getStorageClasses() failed")
                sys.exit(1)
        elif args.objectType == "users":
            rc = astraSDK.users.getUsers(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(nameFilter=args.nameFilter)
            if rc is False:
                print("astraSDK.users.getUsers() failed")
                sys.exit(1)

    elif args.subcommand == "create":
        if args.objectType == "backup":
            rc = tk.doProtectionTask(
                args.objectType,
                args.appID,
                tkSrc.helpers.isRFC1123(args.name),
                args.background,
                args.pollTimer,
                args.quiet,
                args.verbose,
            )
            if rc is False:
                print("doProtectionTask() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cluster":
            with open(args.filePath, encoding="utf8") as f:
                kubeconfigDict = yaml.load(f.read().rstrip(), Loader=yaml.SafeLoader)
                encodedStr = base64.b64encode(json.dumps(kubeconfigDict).encode("utf-8")).decode(
                    "utf-8"
                )
            rc = astraSDK.credentials.createCredential(quiet=args.quiet, verbose=args.verbose).main(
                kubeconfigDict["clusters"][0]["name"],
                "kubeconfig",
                {"base64": encodedStr},
                cloudName="private",
            )
            if rc:
                rc = astraSDK.clusters.addCluster(quiet=args.quiet, verbose=args.verbose).main(
                    args.cloudID,
                    rc["id"],
                )
                if rc is False:
                    print("astraSDK.clusters.createCluster() failed")
                else:
                    sys.exit(0)
            else:
                print("astraSDK.credentials.createCredential() failed")
                sys.exit(1)
        elif args.objectType == "hook":
            rc = astraSDK.hooks.createHook(quiet=args.quiet, verbose=args.verbose).main(
                args.appID,
                args.name,
                args.scriptID,
                args.operation.split("-")[0],
                args.operation.split("-")[1],
                tkSrc.helpers.createHookList(args.hookArguments),
                matchingCriteria=tkSrc.helpers.createCriteriaList(
                    args.containerImage,
                    args.namespace,
                    args.podName,
                    args.label,
                    args.containerName,
                ),
            )
            if rc is False:
                print("astraSDK.hooks.createHook() failed")
            else:
                sys.exit(0)
        elif args.objectType == "protection" or args.objectType == "protectionpolicy":
            if args.granularity == "hourly":
                if args.hour:
                    print("Error: 'hourly' granularity must not specify -H / --hour")
                    sys.exit(1)
                if not hasattr(args, "minute"):
                    print("Error: 'hourly' granularity requires -m / --minute")
                    sys.exit(1)
                args.hour = "*"
                args.dayOfWeek = "*"
                args.dayOfMonth = "*"
            elif args.granularity == "daily":
                if type(args.hour) != int and not args.hour:
                    print("Error: 'daily' granularity requires -H / --hour")
                    sys.exit(1)
                args.dayOfWeek = "*"
                args.dayOfMonth = "*"
            elif args.granularity == "weekly":
                if type(args.hour) != int and not args.hour:
                    print("Error: 'weekly' granularity requires -H / --hour")
                    sys.exit(1)
                if type(args.dayOfWeek) != int and not args.dayOfWeek:
                    print("Error: 'weekly' granularity requires -W / --dayOfWeek")
                    sys.exit(1)
                args.dayOfMonth = "*"
            elif args.granularity == "monthly":
                if type(args.hour) != int and not args.hour:
                    print("Error: 'monthly' granularity requires -H / --hour")
                    sys.exit(1)
                if args.dayOfWeek:
                    print("Error: 'monthly' granularity must not specify -W / --dayOfWeek")
                    sys.exit(1)
                if not args.dayOfMonth:
                    print("Error: 'monthly' granularity requires -M / --dayOfMonth")
                    sys.exit(1)
                args.dayOfWeek = "*"
            rc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.granularity,
                str(args.backupRetention),
                str(args.snapshotRetention),
                str(args.dayOfWeek),
                str(args.dayOfMonth),
                str(args.hour),
                str(args.minute),
                args.appID,
            )
            if rc is False:
                print("astraSDK.protections.createProtectionpolicy() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "replication":
            # Validate offset values and create DTSTART string
            if ":" in args.offset:
                hours = args.offset.split(":")[0].zfill(2)
                minutes = args.offset.split(":")[1].zfill(2)
            else:
                hours = "00"
                minutes = args.offset.zfill(2)
            if int(hours) < 0 or int(hours) > 23:
                print(f"Error: offset {args.offset} hours must be between 0 and 23, inclusive")
                sys.exit(1)
            elif int(minutes) < 0 or int(minutes) > 59:
                print(f"Error: offset {args.offset} minutes must be between 0 and 59, inclusive")
                sys.exit(1)
            dtstart = "DTSTART:20220101T" + hours + minutes + "00Z\n"
            # Create RRULE string
            rrule = "RRULE:FREQ=MINUTELY;INTERVAL="
            if "m" in args.replicationFrequency:
                rrule += args.replicationFrequency.strip("m")
            else:
                rrule += str(int(args.replicationFrequency.strip("h")) * 60)
            # Get Source ClusterID
            if ard.needsattr("apps"):
                ard.apps = astraSDK.apps.getApps().main()
            for app in ard.apps["items"]:
                if app["id"] == args.appID:
                    sourceClusterID = app["clusterID"]
                    sourceNamespaces = app["namespaces"]
            nsMapping = [
                {"clusterID": sourceClusterID, "namespaces": sourceNamespaces},
                {"clusterID": args.destClusterID, "namespaces": [args.destNamespace]},
            ]
            if args.destStorageClass:
                args.destStorageClass = [
                    {"storageClassName": args.destStorageClass, "clusterID": args.destClusterID}
                ]
            rc = astraSDK.replications.createReplicationpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.appID,
                args.destClusterID,
                nsMapping,
                destinationStorageClass=args.destStorageClass,
            )
            if rc:
                prc = astraSDK.protections.createProtectionpolicy(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    "custom",
                    "0",
                    "0",
                    None,
                    None,
                    None,
                    None,
                    args.appID,
                    dtstart + rrule,
                )
                if prc:
                    sys.exit(0)
                else:
                    print("astraSDK.protections.createProtectionpolicy() failed")
                    sys.exit(1)
            else:
                print("astraSDK.replications.createReplicationpolicy() failed")
                sys.exit(1)
        elif args.objectType == "script":
            with open(args.filePath, encoding="utf8") as f:
                encodedStr = base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")
            rc = astraSDK.scripts.createScript(quiet=args.quiet, verbose=args.verbose).main(
                name=args.name, source=encodedStr, description=args.description
            )
            if rc is False:
                print("astraSDK.scripts.createScript() failed")
            else:
                sys.exit(0)
        elif args.objectType == "snapshot":
            rc = tk.doProtectionTask(
                args.objectType,
                args.appID,
                tkSrc.helpers.isRFC1123(args.name),
                args.background,
                args.pollTimer,
                args.quiet,
                args.verbose,
            )
            if rc is False:
                print("doProtectionTask() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "user":
            # First create the user
            urc = astraSDK.users.createUser(quiet=args.quiet, verbose=args.verbose).main(
                args.email, firstName=args.firstName, lastName=args.lastName
            )
            if urc:
                # Next create the role binding
                rrc = astraSDK.rolebindings.createRolebinding(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    args.role,
                    userID=urc["id"],
                    roleConstraints=tkSrc.helpers.createConstraintList(
                        args.namespaceConstraint, args.labelConstraint
                    ),
                )
                if rrc:
                    # Delete+error "local" users where a tempPassword wasn't provided
                    if urc["authProvider"] == "local" and not args.tempPassword:
                        print("Error: --tempPassword is required for ACC+localAuth")
                        drc = astraSDK.rolebindings.destroyRolebinding(quiet=True).main(rrc["id"])
                        if not drc:
                            print("astraSDK.rolebindings.destroyRolebinding() failed")
                        sys.exit(1)
                    # Finally, create the credential if local user
                    if urc["authProvider"] == "local":
                        crc = astraSDK.credentials.createCredential(
                            quiet=args.quiet, verbose=args.verbose
                        ).main(
                            urc["id"],
                            "passwordHash",
                            {
                                "cleartext": base64.b64encode(
                                    args.tempPassword.encode("utf-8")
                                ).decode("utf-8"),
                                "change": base64.b64encode("true".encode("utf-8")).decode("utf-8"),
                            },
                        )
                        if not crc:
                            print("astraSDK.credentials.createCredential() failed")
                            sys.exit(1)
                else:
                    print("astraSDK.rolebindings.createRolebinding() failed")
                    sys.exit(1)
            else:
                print("astraSDK.users.createUser() failed")
                sys.exit(1)
    elif args.subcommand == "manage" or args.subcommand == "define":
        if args.objectType == "app":
            if args.additionalNamespace:
                args.additionalNamespace = tkSrc.helpers.createNamespaceList(
                    args.additionalNamespace
                )
            if args.clusterScopedResource:
                apiResourcesDict = astraSDK.apiresources.getApiResources().main(
                    cluster=args.clusterID
                )
                # Validate input as argparse+choices is unable to only validate the first input
                for csr in args.clusterScopedResource:
                    if csr[0] not in (apiRes := [a["kind"] for a in apiResourcesDict["items"]]):
                        print(
                            f"{' '.join(cmdHeader)}: error: argument -c/--clusterScopedResource: "
                            f"invalid choice: '{csr[0]}' (choose from {', '.join(apiRes)})"
                        )
                        sys.exit(1)
                args.clusterScopedResource = tkSrc.helpers.createCsrList(
                    args.clusterScopedResource, apiResourcesDict
                )
            rc = astraSDK.apps.manageApp(quiet=args.quiet, verbose=args.verbose).main(
                tkSrc.helpers.isRFC1123(args.appName),
                args.namespace,
                args.clusterID,
                args.labelSelectors,
                addNamespaces=args.additionalNamespace,
                clusterScopedResources=args.clusterScopedResource,
            )
            if rc is False:
                print("astraSDK.apps.manageApp() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "bucket":
            # Validate that both credentialID and accessKey/accessSecret were not specified
            if args.credentialID is not None and (
                args.accessKey is not None or args.accessSecret is not None
            ):
                print(
                    f"Error: if a credentialID is specified, neither accessKey nor accessSecret"
                    + " should be specified."
                )
                sys.exit(1)
            # Validate args and create credential if credentialID was not specified
            if args.credentialID is None:
                if args.accessKey is None or args.accessSecret is None:
                    print(
                        "Error: if a credentialID is not specified, both accessKey and "
                        + "accessSecret arguments must be provided."
                    )
                    sys.exit(1)
                encodedKey = base64.b64encode(args.accessKey.encode("utf-8")).decode("utf-8")
                encodedSecret = base64.b64encode(args.accessSecret.encode("utf-8")).decode("utf-8")
                crc = astraSDK.credentials.createCredential(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    args.bucketName,
                    "s3",
                    {"accessKey": encodedKey, "accessSecret": encodedSecret},
                    cloudName="s3",
                )
                if crc:
                    args.credentialID = crc["id"]
                else:
                    print("astraSDK.credentials.createCredential() failed")
                    sys.exit(1)
            # Validate serverURL and storageAccount args depending upon provider type
            if args.serverURL is None and args.provider in [
                "aws",
                "generic-s3",
                "ontap-s3",
                "storagegrid-s3",
            ]:
                print(f"Error: --serverURL must be provided for '{args.provider}' provider.")
                sys.exit(1)
            if args.storageAccount is None and args.provider == "azure":
                print("Error: --storageAccount must be provided for 'azure' provider.")
                sys.exit(1)
            # Create bucket parameters based on provider and optional arguments
            if args.provider == "azure":
                bucketParameters = {
                    "azure": {"bucketName": args.bucketName, "storageAccount": args.storageAccount}
                }
            elif args.provider == "gcp":
                bucketParameters = {"gcp": {"bucketName": args.bucketName}}
            else:
                bucketParameters = {
                    "s3": {"bucketName": args.bucketName, "serverURL": args.serverURL}
                }
            # Call manageBucket class
            rc = astraSDK.buckets.manageBucket(quiet=args.quiet, verbose=args.verbose).main(
                args.bucketName, args.credentialID, args.provider, bucketParameters
            )
            if rc is False:
                print("astraSDK.buckets.manageBucket() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cluster":
            rc = astraSDK.clusters.manageCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.clusterID, args.defaultStorageClassID
            )
            if rc is False:
                print("astraSDK.clusters.manageCluster() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cloud":
            credentialID = None
            # First create the credential
            if args.cloudType != "private":
                if args.credentialPath is None:
                    print(f"Error: --credentialPath is required for cloudType of {args.cloudType}")
                    sys.exit(1)
                with open(args.credentialPath, encoding="utf8") as f:
                    try:
                        credDict = json.loads(f.read().rstrip())
                    except json.decoder.JSONDecodeError:
                        print(f"Error: {args.credentialPath} does not seem to be valid JSON")
                        sys.exit(1)
                encodedStr = base64.b64encode(json.dumps(credDict).encode("utf-8")).decode("utf-8")
                rc = astraSDK.credentials.createCredential(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    "astra-sa@" + args.cloudName,
                    "service-account",
                    {"base64": encodedStr},
                    args.cloudType,
                )
                if rc:
                    credentialID = rc["id"]
                else:
                    print("astraSDK.credentials.createCredential() failed")
                    sys.exit(1)
            # Next manage the cloud
            rc = astraSDK.clouds.manageCloud(quiet=args.quiet, verbose=args.verbose).main(
                args.cloudName,
                args.cloudType,
                credentialID=credentialID,
                defaultBucketID=args.defaultBucketID,
            )
            if rc:
                sys.exit(0)
            else:
                print("astraSDK.clouds.manageCloud() failed")

    elif args.subcommand == "destroy":
        if args.objectType == "backup":
            rc = astraSDK.backups.destroyBackup(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.backupID
            )
            if rc:
                print(f"Backup {args.backupID} destroyed")
            else:
                print(f"Failed destroying backup: {args.backupID}")
        elif args.objectType == "credential":
            rc = astraSDK.credentials.destroyCredential(
                quiet=args.quiet, verbose=args.verbose
            ).main(args.credentialID)
            if rc:
                print(f"Credential {args.credentialID} destroyed")
            else:
                print(f"Failed destroying credential: {args.credentialID}")
        elif args.objectType == "hook":
            rc = astraSDK.hooks.destroyHook(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.hookID
            )
            if rc:
                print(f"Hook {args.hookID} destroyed")
            else:
                print(f"Failed destroying hook: {args.hookID}")
        elif args.objectType == "protection":
            rc = astraSDK.protections.destroyProtectiontionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(args.appID, args.protectionID)
            if rc:
                print(f"Protection policy {args.protectionID} destroyed")
            else:
                print(f"Failed destroying protection policy: {args.protectionID}")
        elif args.objectType == "replication":
            if ard.needsattr("replications"):
                ard.replications = astraSDK.replications.getReplicationpolicies().main()
            rc = astraSDK.replications.destroyReplicationpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(args.replicationID)
            if rc:
                print(f"Replication policy {args.replicationID} destroyed")
                # The underlying replication schedule(s) (protection policy) must also be deleted
                if ard.needsattr("protections"):
                    ard.protections = astraSDK.protections.getProtectionpolicies().main()
                for replication in ard.replications["items"]:
                    if replication["id"] == args.replicationID:
                        for protection in ard.protections["items"]:
                            if (
                                protection["appID"] == replication["sourceAppID"]
                                or protection["appID"] == replication["destinationAppID"]
                            ) and protection.get("replicate") == "true":
                                if astraSDK.protections.destroyProtectiontionpolicy(
                                    quiet=args.quiet, verbose=args.verbose
                                ).main(protection["appID"], protection["id"]):
                                    print(
                                        "Underlying replication schedule "
                                        + f"{protection['id']} destroyed"
                                    )
                                else:
                                    print(
                                        "Failed destroying underlying replication "
                                        + f"schedule: {protection['id']}"
                                    )
                                    sys.exit(1)
            else:
                print(f"Failed destroying replication policy: {args.replicationID}")
                sys.exit(1)
        elif args.objectType == "script":
            rc = astraSDK.scripts.destroyScript(quiet=args.quiet, verbose=args.verbose).main(
                args.scriptID
            )
            if rc:
                print(f"Script {args.scriptID} destroyed")
            else:
                print(f"Failed destroying script: {args.scriptID}")
        elif args.objectType == "snapshot":
            rc = astraSDK.snapshots.destroySnapshot(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.snapshotID
            )
            if rc:
                print(f"Snapshot {args.snapshotID} destroyed")
            else:
                print(f"Failed destroying snapshot: {args.snapshotID}")
        elif args.objectType == "user":
            roleBindings = astraSDK.rolebindings.getRolebindings().main()
            for rb in roleBindings["items"]:
                if rb["userID"] == args.userID:
                    rc = astraSDK.rolebindings.destroyRolebinding(
                        quiet=args.quiet, verbose=args.verbose
                    ).main(rb["id"])
                    if rc:
                        print(f"User {args.userID} / roleBinding {rb['id']} destroyed")
                        sys.exit(0)
                    else:
                        print(f"Failed destroying user {args.userID} with roleBinding {rb['id']}")
                        sys.exit(1)
            # If we reached this point, it's due to plaidMode == True and bad userID
            print(f"Error: userID {args.userID} not found")
            sys.exit(1)

    elif args.subcommand == "unmanage":
        if args.objectType == "app":
            rc = astraSDK.apps.unmanageApp(quiet=args.quiet, verbose=args.verbose).main(args.appID)
            if rc is False:
                print("astraSDK.apps.unmanageApp() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "bucket":
            rc = astraSDK.buckets.unmanageBucket(quiet=args.quiet, verbose=args.verbose).main(
                args.bucketID
            )
            if rc is False:
                print("astraSDK.buckets.unmanageBucket() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cluster":
            rc = astraSDK.clusters.unmanageCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.clusterID
            )
            if rc:
                # "Private" cloud clusters+credentials also should be deleted
                if ard.needsattr("clusters"):
                    ard.clusters = astraSDK.clusters.getClusters().main()
                for cluster in ard.clusters["items"]:
                    for label in cluster["metadata"]["labels"]:
                        if (
                            cluster["id"] == args.clusterID
                            and label["name"] == "astra.netapp.io/labels/read-only/cloudName"
                            and label["value"] == "private"
                        ):
                            if astraSDK.clusters.deleteCluster(
                                quiet=args.quiet, verbose=args.verbose
                            ).main(args.clusterID, cluster["cloudID"]):
                                if astraSDK.credentials.destroyCredential(
                                    quiet=args.quiet, verbose=args.verbose
                                ).main(cluster.get("credentialID")):
                                    print(f"Credential deleted")
                                else:
                                    print("astraSDK.credentials.destroyCredential() failed")
                                    sys.exit(1)
                            else:
                                print("astraSDK.clusters.deleteCluster() failed")
                                sys.exit(1)
                sys.exit(0)
            else:
                print("astraSDK.clusters.unmanageCluster() failed")
                sys.exit(1)
        elif args.objectType == "cloud":
            if ard.needsattr("cloud"):
                ard.clouds = astraSDK.clouds.getClouds().main()
            rc = astraSDK.clouds.unmanageCloud(quiet=args.quiet, verbose=args.verbose).main(
                args.cloudID
            )
            if rc:
                # Cloud credentials also should be deleted
                for cloud in ard.clouds["items"]:
                    if cloud["id"] == args.cloudID:
                        if cloud.get("credentialID"):
                            if astraSDK.credentials.destroyCredential(
                                quiet=args.quiet, verbose=args.verbose
                            ).main(cloud.get("credentialID")):
                                print(f"Credential deleted")
                            else:
                                print("astraSDK.credentials.destroyCredential() failed")
                                sys.exit(1)
                sys.exit(0)
            else:
                print("astraSDK.clusters.unmanageCloud() failed")
                sys.exit(1)

    elif args.subcommand == "restore":
        if (args.filterSelection and not args.filterSet) or (
            args.filterSet and not args.filterSelection
        ):
            print(
                f"{' '.join(cmdHeader)}: error: either both or none of "
                "--filterSelection and --filterSet should be specified"
            )
            sys.exit(1)
        rc = astraSDK.apps.restoreApp(quiet=args.quiet, verbose=args.verbose).main(
            args.appID,
            backupID=args.backupID,
            snapshotID=args.snapshotID,
            resourceFilter=tkSrc.helpers.createFilterSet(
                args.filterSelection, args.filterSet, astraSDK.apps.getAppAssets().main(args.appID)
            ),
        )
        if rc:
            if args.background:
                print("Restore job submitted successfully")
                print("Background restore flag selected, run 'list apps' to get status")
                sys.exit(0)
            print("Restore job in progress...", end="")
            sys.stdout.flush()
            while True:
                restoreApps = astraSDK.apps.getApps().main()
                state = None
                for restoreApp in restoreApps["items"]:
                    if restoreApp["id"] == args.appID:
                        state = restoreApp["state"]
                if state == "restoring":
                    print(".", end="")
                    sys.stdout.flush()
                elif state == "ready":
                    print("Success!")
                    break
                elif state == "failed":
                    print("Failed!")
                    sys.exit(2)
                time.sleep(args.pollTimer)
        else:
            print("Submitting restore job failed.")
            sys.exit(3)

    elif args.subcommand == "clone":
        if (args.filterSelection and not args.filterSet) or (
            args.filterSet and not args.filterSelection
        ):
            print(
                f"{' '.join(cmdHeader)}: error: either both or none of "
                "--filterSelection and --filterSet should be specified"
            )
            sys.exit(1)
        if args.filterSet and args.sourceAppID:
            print(
                "Error: resource filters (--filterSet) may only be specified with --backupID "
                "or --snapshotID arguments, not --sourceAppID"
            )
            sys.exit(1)
        if not args.cloneAppName:
            args.cloneAppName = input("App name for the clone: ")
        # TODO: add this back in
        """if not args.clusterID:
            print("Select destination cluster for the clone")
            print("Index\tClusterID\t\t\t\tclusterName\tclusterPlatform")
            args.clusterID = userSelect(
                destCluster, ["id", "name", "clusterType"]
            )"""
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
            print(
                "Error: the corresponding appID was not found in the system, please check "
                + "your inputs and try again."
            )
            sys.exit(1)

        tk.doClone(
            tkSrc.helpers.isRFC1123(args.cloneAppName),
            args.clusterID,
            oApp,
            tkSrc.helpers.createNamespaceMapping(oApp, args.cloneNamespace, args.multiNsMapping),
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

    elif args.subcommand == "update":
        if args.objectType == "bucket":
            # Validate that both credentialID and accessKey/accessSecret were not specified
            if args.credentialID is not None and (
                args.accessKey is not None or args.accessSecret is not None
            ):
                print(
                    f"Error: if a credentialID is specified, neither accessKey nor accessSecret"
                    + " should be specified."
                )
                sys.exit(1)
            # Validate args and create credential if credentialID was not specified
            if args.credentialID is None:
                if args.accessKey is None or args.accessSecret is None:
                    print(
                        "Error: if a credentialID is not specified, both accessKey and "
                        + "accessSecret arguments must be provided."
                    )
                    sys.exit(1)
                if ard.needsattr("buckets"):
                    ard.buckets = astraSDK.buckets.getBuckets().main()
                encodedKey = base64.b64encode(args.accessKey.encode("utf-8")).decode("utf-8")
                encodedSecret = base64.b64encode(args.accessSecret.encode("utf-8")).decode("utf-8")
                try:
                    crc = astraSDK.credentials.createCredential(
                        quiet=args.quiet, verbose=args.verbose
                    ).main(
                        next(b for b in ard.buckets["items"] if b["id"] == args.bucketID)["name"],
                        "s3",
                        {"accessKey": encodedKey, "accessSecret": encodedSecret},
                        cloudName="s3",
                    )
                except StopIteration:
                    print(f"Error: {args.bucketID} does not seem to be a valid bucketID")
                    sys.exit(1)
                if crc:
                    args.credentialID = crc["id"]
                else:
                    print("astraSDK.credentials.createCredential() failed")
                    sys.exit(1)
            # Call updateBucket class
            rc = astraSDK.buckets.updateBucket(quiet=args.quiet, verbose=args.verbose).main(
                args.bucketID, credentialID=args.credentialID
            )
            if rc is False:
                print("astraSDK.buckets.updateBucket() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cloud":
            if args.credentialPath:
                with open(args.credentialPath, encoding="utf8") as f:
                    try:
                        credDict = json.loads(f.read().rstrip())
                    except json.decoder.JSONDecodeError:
                        print(f"Error: {args.credentialPath} does not seem to be valid JSON")
                        sys.exit(1)
                encodedStr = base64.b64encode(json.dumps(credDict).encode("utf-8")).decode("utf-8")
                if ard.needsattr("clouds"):
                    ard.clouds = astraSDK.clouds.getClouds().main()
                try:
                    cloud = next(c for c in ard.clouds["items"] if c["id"] == args.cloudID)
                except StopIteration:
                    print(f"Error: {args.cloudID} does not seem to be a valid cloudID")
                    sys.exit(1)
                rc = astraSDK.credentials.createCredential(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    "astra-sa@" + cloud["name"],
                    "service-account",
                    {"base64": encodedStr},
                    cloud["cloudType"],
                )
                if rc:
                    args.credentialID = rc["id"]
                else:
                    print("astraSDK.credentials.createCredential() failed")
                    sys.exit(1)
            # Next update the cloud
            rc = astraSDK.clouds.updateCloud(quiet=args.quiet, verbose=args.verbose).main(
                args.cloudID,
                credentialID=args.credentialID,
                defaultBucketID=args.defaultBucketID,
            )
            if rc:
                sys.exit(0)
            else:
                print(rc.error)
                print("astraSDK.clouds.updateCloud() failed")
        elif args.objectType == "cluster":
            # Get the cluster information based on the clusterID input
            if ard.needsattr("clusters"):
                ard.clusters = astraSDK.clusters.getClusters().main()
            try:
                cluster = next(c for c in ard.clusters["items"] if c["id"] == args.clusterID)
            except StopIteration:
                print(f"Error: {args.clusterID} does not seem to be a valid clusterID")
                sys.exit(1)
            # Currently this is required to be True, but this will not always be the case
            if args.credentialPath:
                with open(args.credentialPath, encoding="utf8") as f:
                    kubeconfigDict = yaml.load(f.read().rstrip(), Loader=yaml.SafeLoader)
                    encodedStr = base64.b64encode(
                        json.dumps(kubeconfigDict).encode("utf-8")
                    ).decode("utf-8")
                rc = astraSDK.credentials.updateCredential(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    cluster.get("credentialID"),
                    kubeconfigDict["clusters"][0]["name"],
                    keyStore={"base64": encodedStr},
                )
                if rc:
                    sys.exit(0)
                else:
                    print("astraSDK.credentials.updateCredential() failed")
                    sys.exit(1)
        elif args.objectType == "replication":
            # Gather replication data
            if ard.needsattr("replications"):
                ard.replications = astraSDK.replications.getReplicationpolicies().main()
                if not ard.replications:  # Gracefully handle ACS env
                    print("Error: 'replication' commands are currently only supported in ACC.")
                    sys.exit(1)
            repl = None
            for replication in ard.replications["items"]:
                if args.replicationID == replication["id"]:
                    repl = replication
            if not repl:
                print(f"Error: replicationID {args.replicationID} not found")
                sys.exit(1)
            # Make call based on operation type
            if args.operation == "resync":
                if not args.dataSource:
                    print("Error: --dataSource must be provided for 'resync' operations")
                    sys.exit(1)
                if repl["state"] != "failedOver":
                    print(
                        "Error: to resync a replication, it must be in a `failedOver` state"
                        + f", not a(n) `{repl['state']}` state"
                    )
                    sys.exit(1)
                if args.dataSource in [repl["sourceAppID"], repl["sourceClusterID"]]:
                    rc = astraSDK.replications.updateReplicationpolicy(
                        quiet=args.quiet, verbose=args.verbose
                    ).main(
                        args.replicationID,
                        "established",
                        sourceAppID=repl["sourceAppID"],
                        sourceClusterID=repl["sourceClusterID"],
                        destinationAppID=repl["destinationAppID"],
                        destinationClusterID=repl["destinationClusterID"],
                    )
                elif args.dataSource in [repl["destinationAppID"], repl["destinationClusterID"]]:
                    rc = astraSDK.replications.updateReplicationpolicy(
                        quiet=args.quiet, verbose=args.verbose
                    ).main(
                        args.replicationID,
                        "established",
                        sourceAppID=repl["destinationAppID"],
                        sourceClusterID=repl["destinationClusterID"],
                        destinationAppID=repl["sourceAppID"],
                        destinationClusterID=repl["sourceClusterID"],
                    )
                else:
                    print(
                        f"Error: dataSource '{args.dataSource}' not one of:\n"
                        + f"\t{repl['sourceAppID']}\t(original sourceAppID)\n"
                        + f"\t{repl['sourceClusterID']}\t(original sourceClusterID)\n"
                        + f"\t{repl['destinationAppID']}\t(original destinationAppID)\n"
                        + f"\t{repl['destinationClusterID']}\t(original destinationClusterID)"
                    )
                    sys.exit(1)
            elif args.operation == "reverse":
                if repl["state"] != "established" and repl["state"] != "failedOver":
                    print(
                        "Error: to reverse a replication, it must be in an `established` or "
                        + f"`failedOver` state, not a(n) `{repl['state']}` state"
                    )
                    sys.exit(1)
                rc = astraSDK.replications.updateReplicationpolicy(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    args.replicationID,
                    "established",
                    sourceAppID=repl["destinationAppID"],
                    sourceClusterID=repl["destinationClusterID"],
                    destinationAppID=repl["sourceAppID"],
                    destinationClusterID=repl["sourceClusterID"],
                )
            else:  # failover
                if repl["state"] != "established":
                    print(
                        "Error: to failover a replication, it must be in an `established` state"
                        + f", not a(n) `{repl['state']}` state"
                    )
                    sys.exit(1)
                rc = astraSDK.replications.updateReplicationpolicy(
                    quiet=args.quiet, verbose=args.verbose
                ).main(args.replicationID, "failedOver")
            # Exit based on response
            if rc:
                print(f"Replication {args.operation} initiated")
                sys.exit(0)
            else:
                print("astraSDK.replications.updateReplicationpolicy() failed")
                sys.exit(1)
        elif args.objectType == "script":
            with open(args.filePath, encoding="utf8") as f:
                encodedStr = base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")
            rc = astraSDK.scripts.updateScript(quiet=args.quiet, verbose=args.verbose).main(
                args.scriptID, source=encodedStr
            )
            if rc is False:
                print("astraSDK.scripts.updateScript() failed")
            else:
                sys.exit(0)
