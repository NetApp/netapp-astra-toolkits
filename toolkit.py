#!/usr/bin/env python
"""
   Copyright 2022 NetApp, Inc

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

try:
    from . import astraSDK
except ImportError:
    import astraSDK


import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import yaml
import kubernetes
import base64
from datetime import datetime, timedelta


def subKeys(subObject, key):
    """Short recursion function for when the userSelect dict object has another
    dict as one of its key's values"""
    subKey = key.split("/", maxsplit=1)
    if len(subKey) == 1:
        return subObject[subKey[0]]
    else:
        return subKeys(subObject[subKey[0]], subKey[1])


def userSelect(pickList, keys):
    """pickList is a dictionary with an 'items' array of dicts.  Print the values
    that match the 'keys' array, have the user pick one and then return the value
    of index 0 of the keys array"""
    # pickList = {"items": [{"id": "123", "name": "webapp",  "state": "running"},
    #                       {"id": "345", "name": "mongodb", "state": "stopped"}]}
    # keys = ["id", "name"]
    # Output:
    # 1:    123         webapp
    # 2:    345         mongodb
    # User enters 2, "id" (index 0) is returned, so "345"

    if not isinstance(pickList, dict) or not isinstance(keys, list):
        return False

    for counter, item in enumerate(pickList["items"], start=1):
        outputStr = str(counter) + ":\t"
        for key in keys:
            if item.get(key):
                outputStr += str(item[key]) + "\t"
            elif "/" in key:
                outputStr += subKeys(item, key) + "\t"
        print(outputStr)

    while True:
        ret = input(f"Select a line (1-{counter}): ")
        try:
            # try/except catches errors thrown from non-valid input
            objectValue = pickList["items"][int(ret) - 1][keys[0]]
            if int(ret) > 0 and int(ret) <= counter and objectValue:
                return objectValue
            else:
                continue
        except (IndexError, TypeError, ValueError):
            continue


def createHelmStr(flagName, values):
    """Create a string to be appended to a helm command which contains a list
    of --set {value} and/or --values {file} arguments"""
    returnStr = ""
    if values:
        for value in values:
            if type(value) == list:
                for v in value:
                    returnStr += f" --{flagName} {v}"
            else:
                returnStr += f" --{flagName} {value}"
    return returnStr


def createHookList(hookArguments):
    """Create a list of strings to be used for --hookArguments, as nargs="*" can provide
    a variety of different types of lists of lists depending on how the user ueses it.
    User Input                    argParse Value                      createHookList Return
    ----------                    --------------                      ---------------------
    -a arg1                       [['arg1']]                          ['arg1']
    -a arg1 arg2                  [['arg1', 'arg2']]                  ['arg1', 'arg2']
    -a arg1 -a arg2               [['arg1'], ['arg2']]                ['arg1', 'arg2']
    -a "arg1 s_arg" arg2          [['arg1 s_arg', 'arg2']]            ['arg1 s_arg', 'arg2']
    -a "arg1 s_arg" arg2 -a arg3  [['arg1 s_arg', 'arg2'], ['arg3']]  ['arg1 s_arg', 'arg2', 'arg3']
    """
    returnList = []
    if hookArguments:
        for arg in hookArguments:
            if type(arg) == list:
                for a in arg:
                    returnList.append(a)
            else:
                returnList.append(arg)
    return returnList


def updateHelm():
    """Check to see if the bitnami helm repo is installed
    If it is, get the name of the repo
    otherwise install it
    ignore_errors=True here because helm repo list returns 1 if there are no
    repos configured"""
    ret = run("helm repo list -o yaml", captureOutput=True, ignoreErrors=True)
    repos = {
        "https://charts.gitlab.io": None,
        "https://charts.bitnami.com/bitnami": None,
        "https://charts.cloudbees.com/public/cloudbees": None,
    }
    if ret != 1:
        retYaml = yaml.load(ret, Loader=yaml.SafeLoader)
        # Adding support for user-defined repos
        for item in retYaml:
            if item.get("url") not in repos:
                repos[item.get("url")] = None
        for repoUrlToMatch in repos:
            for item in retYaml:
                if item.get("url") == repoUrlToMatch:
                    repos[repoUrlToMatch] = item.get("name")
    for k, v in repos.items():
        if not v:
            repoName = k.split(".")[1]
            run(f"helm repo add {repoName} {k}")
            repos[k] = repoName

    run("helm repo update")
    chartsDict = {}
    chartsDict["items"] = []
    for val in repos.values():
        charts = run(f"helm -o json search repo {val}", captureOutput=True)
        for chart in json.loads(charts.decode("utf-8")):
            chartsDict["items"].append(chart)
    return chartsDict


def run(command, captureOutput=False, ignoreErrors=False):
    """Run an arbitrary shell command.  Our API is terrible.  If ignore_errors=False
    raise the SystemExit exception if the commands returns != 0 (e.g.: failure)
    If ignore_errors=True, return the shell return code if it is != 0
    If the shell return code is 0 (success) either return True or the contents of stdout, depending
    on whether capture_output is set to True or False"""
    command = command.split(" ")
    try:
        ret = subprocess.run(command, capture_output=captureOutput)
    except OSError as e:
        raise SystemExit(f"{command} OSError: {e}")
    # Shell returns 0 for success, a positive int for an error
    # inverted from python True/False
    if ret.returncode:
        if ignoreErrors:
            return ret.returncode
        else:
            raise SystemExit(f"{command} returned failure: {ret.returncode}")
    else:
        if captureOutput:
            return ret.stdout
        else:
            return True


def doProtectionTask(protectionType, appID, name, background):
    """Take a snapshot/backup of appID giving it name <name>
    Return the snapshotID/backupID of the backup taken or False if the protection task fails"""
    if protectionType == "backup":
        protectionID = astraSDK.takeBackup().main(appID, name)
    elif protectionType == "snapshot":
        protectionID = astraSDK.takeSnap().main(appID, name)
    if protectionID == False:
        sys.exit(1)

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
            objects = astraSDK.getBackups().main()
        elif protectionType == "snapshot":
            objects = astraSDK.getSnaps().main()
        if not objects:
            # This isn't technically true.  Trying to list the backups/snapshots after taking the
            # protection job failed.  The protection job itself may eventually succeed.
            print(f"Taking {protectionType} failed")
            return False
        for obj in objects["items"]:
            # There's no API for monitoring long running tasks.  Just because
            # the API call to create a backup/snapshot succeeded, that doesn't mean the
            # actual backup will succeed as well.  So we spin on checking the backups/snapshots
            # waiting for our backupsnapshot to either show completed or failed.
            if obj["id"] == protectionID:
                if obj["state"] == "completed":
                    print("complete!")
                    sys.stdout.flush()
                    return protectionID
                elif obj["state"] == "failed":
                    print(f"{protectionType} job failed")
                    return False
        time.sleep(5)
        print(".", end="")
        sys.stdout.flush()


def stsPatch(patch, stsName):
    """Patch and restart a statefulset"""
    patchYaml = yaml.dump(patch)
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(bytes(patchYaml, "utf-8"))
    tmp.seek(0)
    # Use os.system a few times because the home rolled run() simply isn't up to the task
    try:
        # TODO: I suspect these gymnastics wouldn't be needed if the py-k8s module
        # were used
        ret = os.system(f'kubectl patch statefulset.apps/{stsName} -p "$(cat {tmp.name})"')
    except OSError as e:
        print(f"Exception: {e}")
        sys.exit(11)
    if ret:
        print(f"os.system exited with RC: {ret}")
        sys.exit(12)
    tmp.close()
    try:
        os.system(
            f"kubectl scale sts {stsName} --replicas=0 && "
            f"sleep 10 && kubectl scale sts {stsName} --replicas=1"
        )
    except OSError as e:
        print(f"Exception: {e}")
        sys.exit(13)
    if ret:
        print(f"os.system exited with RC: {ret}")
        sys.exit(14)


class toolkit:
    def __init__(self):
        self.conf = astraSDK.getConfig().main()

    def deploy(self, chart, appName, namespace, setValues, fileValues, verbose, quiet):
        """Deploy a helm chart <chart>, naming the app <appName> into <namespace>"""

        setStr = createHelmStr("set", setValues)
        valueStr = createHelmStr("values", fileValues)

        nsObj = astraSDK.getNamespaces(verbose=verbose)
        retval = run("kubectl get ns -o json", captureOutput=True)
        retvalJSON = json.loads(retval)
        for item in retvalJSON["items"]:
            if item["metadata"]["name"] == namespace:
                print(f"Namespace {namespace} already exists!")
                sys.exit(24)
        run(f"kubectl create namespace {namespace}")
        run(f"kubectl config set-context --current --namespace={namespace}")

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

        run(f"helm install {appName} {chart}{setStr}{valueStr}")
        print("Waiting for Astra to discover the namespace.", end="")
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
                    rc = astraSDK.manageApp(verbose=verbose).main(
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
                        rc = astraSDK.manageApp(quiet=quiet, verbose=verbose).main(
                            ns["name"], ns["name"], ns["clusterID"]
                        )
                        if rc:
                            appID = rc["id"]
                            print("Success!")
                            break
                        else:
                            sys.exit(1)

        # Create a protection policy on that namespace (using its appID)
        backupRetention = "1"
        snapshotRetention = "1"
        minute = "0"
        cpp = astraSDK.createProtectionpolicy(quiet=True)
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
                snapshotRetention,
                backupRetention,
                dayOfWeek,
                dayOfMonth,
                hour,
                minute,
                appID,
            )
            if cppRet is False:
                raise SystemExit(f"cpp.main({period}...) returned False")

    def clone(
        self,
        cloneAppName,
        clusterID,
        sourceClusterID,
        appIDstr,
        cloneNamespace,
        backupID,
        snapshotID,
        sourceAppID,
        background,
        verbose,
    ):
        """Create a clone."""
        # Check to see if cluster-level resources are needed to be manually created
        needsIngressclass = False
        appAssets = astraSDK.getAppAssets(verbose=verbose).main(appIDstr)
        for asset in appAssets["items"]:
            if (
                "nginx-ingress-controller" in asset["assetName"]
                or "ingress-nginx-controller" in asset["assetName"]
            ) and asset["assetType"] == "Pod":
                needsIngressclass = True
                assetName = asset["assetName"]
        # Clone 'ingressclass' cluster object
        if needsIngressclass and sourceClusterID != clusterID:
            if not cloneNamespace:
                cloneNamespace = cloneAppName
            clusters = astraSDK.getClusters().main(hideUnmanaged=True)
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
                    elif cluster["id"] == sourceClusterID:
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

        cloneRet = astraSDK.cloneApp(verbose=verbose).main(
            cloneAppName,
            clusterID,
            sourceClusterID,
            cloneNamespace=cloneNamespace,
            backupID=backupID,
            snapshotID=snapshotID,
            sourceAppID=sourceAppID,
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
                apps = astraSDK.getApps().main()
                for app in apps["items"]:
                    if app["id"] == appID:
                        if app["state"] == "ready":
                            state = app["state"]
                            print("Cloning operation complete.")
                            sys.stdout.flush()
                        else:
                            print(".", end="")
                            sys.stdout.flush()
                            time.sleep(3)
        else:
            print("Submitting clone failed.")


def main():
    # The various functions to populate the lists used for choices() in the options are
    # expensive. argparse provides no way to know what subcommand was selected prior to
    # parsing the options. By then it's too late to decide which functions to run to
    # populate the various choices the differing options for each subcommand needs. So
    # we just go around argparse's back and inspect sys.argv directly.
    appList = []
    backupList = []
    bucketList = []
    chartsList = []
    cloudList = []
    clusterList = []
    credentialList = []
    destclusterList = []
    hookList = []
    namespaceList = []
    protectionList = []
    replicationList = []
    scriptList = []
    snapshotList = []
    storageClassList = []

    if len(sys.argv) > 1:

        # verbs must manually be kept in sync with the top level subcommands in the argparse
        # section of this code.
        verbs = {
            "deploy": False,
            "clone": False,
            "restore": False,
            "list": False,
            "get": False,
            "create": False,
            "manage": False,
            "define": False,
            "destroy": False,
            "unmanage": False,
            "update": False,
        }

        firstverbfoundPosition = None
        verbPosition = None
        cookedlistofVerbs = [x for x in verbs]
        for verb in verbs:
            if verb not in sys.argv:
                # no need to iterate over the arg list for a verb that isn't in there
                continue
            if verbPosition:
                # once we've found the first verb we can stop looking
                break
            for counter, item in enumerate(sys.argv):
                if item == verb:
                    if firstverbfoundPosition is None:
                        # firstverbfoundPosition exists to prevent
                        # "toolkit.py create deploy create deploy" from deciding the second create
                        # is the first verb found
                        firstverbfoundPosition = counter
                    else:
                        if counter > firstverbfoundPosition:
                            continue
                        else:
                            firstverbfoundPosition = counter
                    # Why are we jumping through hoops here to remove the verb we found
                    # from the list of verbs?  Consider the input "toolkit.py deploy deploy"
                    # When we loop over the args we find the first "deploy"
                    # verb["deploy"] gets set to True, we loop over the slice of sys.argv
                    # previous to "deploy" and find no other verbs so verb["deploy"] remains True
                    # Then we find the second deploy.  We loop over the slice of sys.argv previous
                    # to *that* and sure enough, the first "deploy" is in verbs so
                    # verb["deploy"] gets set to False
                    try:
                        cookedlistofVerbs.remove(item)
                    except ValueError:
                        pass
                    verbs[verb] = True
                    verbPosition = counter
                    for item2 in sys.argv[:(counter)]:
                        # sys.argv[:(counter)] is a slice of sys.argv of all the items
                        # before the one we found
                        if item2 in cookedlistofVerbs:
                            # deploy wasn't the verb, it was a symbolic name of an object
                            verbs[verb] = False
                            verbPosition = None

        # Turn off verification to speed things up if true
        plaidMode = False
        for counter, item in enumerate(sys.argv):
            if verbPosition and counter < verbPosition and (item == "-f" or item == "--fast"):
                plaidMode = True

        if not plaidMode:
            # It isn't intuitive, however only one key in verbs can be True
            if verbs["deploy"]:
                chartsDict = updateHelm()
                for chart in chartsDict["items"]:
                    chartsList.append(chart["name"])

            elif verbs["clone"]:
                apps = astraSDK.getApps().main()
                for app in apps["items"]:
                    appList.append(app["id"])
                destCluster = astraSDK.getClusters().main(hideUnmanaged=True)
                for cluster in destCluster["items"]:
                    destclusterList.append(cluster["id"])
                backups = astraSDK.getBackups().main()
                for backup in backups["items"]:
                    backupList.append(backup["id"])
                snapshots = astraSDK.getSnaps().main()
                for snap in snapshots["items"]:
                    snapshotList.append(snap["id"])

            elif verbs["restore"]:
                for app in astraSDK.getApps().main()["items"]:
                    appList.append(app["id"])

                # This expression translates to "Is there an arg after the verb we found?"
                if len(sys.argv) - verbPosition >= 2:
                    # If that arg after the verb "restore" matches an appID then
                    # populate the lists of backups and snapshots for that appID
                    backups = astraSDK.getBackups().main()
                    for backup in backups["items"]:
                        if backup["appID"] == sys.argv[verbPosition + 1] or (
                            len(sys.argv) > verbPosition + 2
                            and backup["appID"] == sys.argv[verbPosition + 2]
                        ):
                            backupList.append(backup["id"])
                    snapshots = astraSDK.getSnaps().main()
                    for snapshot in snapshots["items"]:
                        if snapshot["appID"] == sys.argv[verbPosition + 1] or (
                            len(sys.argv) > verbPosition + 2
                            and snapshot["appID"] == sys.argv[verbPosition + 2]
                        ):
                            snapshotList.append(snapshot["id"])
            elif (
                verbs["create"]
                and len(sys.argv) - verbPosition >= 2
                and (
                    sys.argv[verbPosition + 1] == "backup"
                    or sys.argv[verbPosition + 1] == "hook"
                    or sys.argv[verbPosition + 1] == "protectionpolicy"
                    or sys.argv[verbPosition + 1] == "protection"
                    or sys.argv[verbPosition + 1] == "replication"
                    or sys.argv[verbPosition + 1] == "snapshot"
                )
            ):
                apps = astraSDK.getApps().main()
                for app in apps["items"]:
                    appList.append(app["id"])
                if sys.argv[verbPosition + 1] == "hook":
                    for script in astraSDK.getScripts().main()["items"]:
                        scriptList.append(script["id"])
                if sys.argv[verbPosition + 1] == "replication":
                    destCluster = astraSDK.getClusters().main(hideUnmanaged=True)
                    for cluster in destCluster["items"]:
                        destclusterList.append(cluster["id"])
                    storageClassDict = astraSDK.getStorageClasses(quiet=True).main()
                    if isinstance(storageClassDict, bool):
                        # astraSDK.getStorageClasses(quiet=True).main() returns either True
                        # or False if it doesn't work, or if there are no clouds or clusters
                        sys.exit(1)
                    for storageClass in storageClassDict["items"]:
                        storageClassList.append(storageClass["name"])
                    storageClassList = list(set(storageClassList))

            elif (
                verbs["create"]
                and len(sys.argv) - verbPosition >= 2
                and sys.argv[verbPosition + 1] == "cluster"
            ):
                for cloud in astraSDK.getClouds().main()["items"]:
                    if cloud["cloudType"] not in ["GCP", "Azure", "AWS"]:
                        cloudList.append(cloud["id"])

            elif (
                verbs["list"]
                and len(sys.argv) - verbPosition >= 2
                and sys.argv[verbPosition + 1] == "assets"
            ):
                for app in astraSDK.getApps().main()["items"]:
                    appList.append(app["id"])

            elif (verbs["manage"] or verbs["define"]) and len(sys.argv) - verbPosition >= 2:
                if sys.argv[verbPosition + 1] == "app":
                    namespaceDict = astraSDK.getNamespaces().main()
                    for namespace in namespaceDict["items"]:
                        namespaceList.append(namespace["name"])
                        clusterList.append(namespace["clusterID"])
                    clusterList = list(set(clusterList))
                elif sys.argv[verbPosition + 1] == "bucket":
                    credentialDict = astraSDK.getCredentials().main()
                    for credential in credentialDict["items"]:
                        # if credential["keyType"] == "s3" or (
                        if credential["metadata"].get("labels"):
                            credID = None
                            if credential["keyType"] == "s3":
                                credID = credential["id"]
                            else:
                                for label in credential["metadata"]["labels"]:
                                    if label["name"] == "astra.netapp.io/labels/read-only/credType":
                                        if label["value"] in ["AzureContainer", "service-account"]:
                                            credID = credential["id"]
                            if credID:
                                credentialList.append(credential["id"])
                elif sys.argv[verbPosition + 1] == "cluster":
                    clusterDict = astraSDK.getClusters(quiet=True).main()
                    for cluster in clusterDict["items"]:
                        if cluster["managedState"] == "unmanaged":
                            clusterList.append(cluster["id"])
                    storageClassDict = astraSDK.getStorageClasses(quiet=True).main()
                    if isinstance(storageClassDict, bool):
                        # astraSDK.getStorageClasses(quiet=True).main() returns either True
                        # or False if it doesn't work, or if there are no clouds or clusters
                        sys.exit(1)
                    for storageClass in storageClassDict["items"]:
                        if (
                            len(sys.argv) - verbPosition >= 3
                            and sys.argv[verbPosition + 2] in clusterList
                            and storageClass["clusterID"] != sys.argv[verbPosition + 2]
                        ):
                            continue
                        storageClassList.append(storageClass["id"])

            elif verbs["destroy"] and len(sys.argv) - verbPosition >= 2:
                if sys.argv[verbPosition + 1] == "backup" and len(sys.argv) - verbPosition >= 3:
                    for app in astraSDK.getApps().main()["items"]:
                        appList.append(app["id"])
                    backups = astraSDK.getBackups().main()
                    for backup in backups["items"]:
                        if backup["appID"] == sys.argv[verbPosition + 2]:
                            backupList.append(backup["id"])
                elif (
                    sys.argv[verbPosition + 1] == "credential" and len(sys.argv) - verbPosition >= 3
                ):
                    credentialDict = astraSDK.getCredentials().main()
                    for credential in credentialDict["items"]:
                        credentialList.append(credential["id"])
                elif sys.argv[verbPosition + 1] == "hook" and len(sys.argv) - verbPosition >= 3:
                    for app in astraSDK.getApps().main()["items"]:
                        appList.append(app["id"])
                    hooks = astraSDK.getHooks().main()
                    for hook in hooks["items"]:
                        if hook["appID"] == sys.argv[verbPosition + 2]:
                            hookList.append(hook["id"])
                elif (
                    sys.argv[verbPosition + 1] == "protection" and len(sys.argv) - verbPosition >= 3
                ):
                    for app in astraSDK.getApps().main()["items"]:
                        appList.append(app["id"])
                    protections = astraSDK.getProtectionpolicies().main()
                    for protection in protections["items"]:
                        if protection["appID"] == sys.argv[verbPosition + 2]:
                            protectionList.append(protection["id"])
                elif (
                    sys.argv[verbPosition + 1] == "replication"
                    and len(sys.argv) - verbPosition >= 3
                ):
                    replicationDict = astraSDK.getReplicationpolicies().main()
                    if not replicationDict:  # Gracefully handle ACS env
                        print("Error: 'replication' commands are currently only supported in ACC.")
                        sys.exit(1)
                    for replication in replicationDict["items"]:
                        replicationList.append(replication["id"])
                elif sys.argv[verbPosition + 1] == "snapshot" and len(sys.argv) - verbPosition >= 3:
                    for app in astraSDK.getApps().main()["items"]:
                        appList.append(app["id"])
                    snapshots = astraSDK.getSnaps().main()
                    for snapshot in snapshots["items"]:
                        if snapshot["appID"] == sys.argv[verbPosition + 2]:
                            snapshotList.append(snapshot["id"])
                elif sys.argv[verbPosition + 1] == "script" and len(sys.argv) - verbPosition >= 3:
                    for script in astraSDK.getScripts().main()["items"]:
                        scriptList.append(script["id"])

            elif verbs["unmanage"] and len(sys.argv) - verbPosition >= 2:
                if sys.argv[verbPosition + 1] == "app":
                    for app in astraSDK.getApps().main()["items"]:
                        appList.append(app["id"])
                elif sys.argv[verbPosition + 1] == "bucket":
                    bucketDict = astraSDK.getBuckets(quiet=True).main()
                    for bucket in bucketDict["items"]:
                        bucketList.append(bucket["id"])
                elif sys.argv[verbPosition + 1] == "cluster":
                    clusterDict = astraSDK.getClusters(quiet=True).main()
                    for cluster in clusterDict["items"]:
                        if cluster["managedState"] == "managed":
                            clusterList.append(cluster["id"])

            elif (verbs["update"]) and len(sys.argv) - verbPosition >= 2:
                if sys.argv[verbPosition + 1] == "replication":
                    replicationDict = astraSDK.getReplicationpolicies().main()
                    if not replicationDict:  # Gracefully handle ACS env
                        print("Error: 'replication' commands are currently only supported in ACC.")
                        sys.exit(1)
                    for replication in replicationDict["items"]:
                        replicationList.append(replication["id"])

    parser = argparse.ArgumentParser(allow_abbrev=True)
    parser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="print verbose/verbose output",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="table",
        choices=["json", "yaml", "table"],
        help="command output format",
    )
    parser.add_argument("-q", "--quiet", default=False, action="store_true", help="supress output")
    parser.add_argument(
        "-f",
        "--fast",
        default=False,
        action="store_true",
        help="prioritize speed over validation (using this will not validate arguments, which "
        + "may have unintended consequences)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True, help="subcommand help")
    #######
    # Top level subcommands
    # # Be sure to keep these in sync with verbs{}
    #######
    parserDeploy = subparsers.add_parser(
        "deploy",
        help="Deploy a helm chart",
    )
    parserClone = subparsers.add_parser(
        "clone",
        help="Clone an app",
    )
    parserRestore = subparsers.add_parser(
        "restore",
        help="Restore an app from a backup or snapshot",
    )
    parserList = subparsers.add_parser(
        "list",
        aliases=["get"],
        help="List all items in a class",
    )
    parserCreate = subparsers.add_parser(
        "create",
        help="Create an object",
    )
    parserManage = subparsers.add_parser(
        "manage",
        aliases=["define"],
        help="Manage an object",
    )
    parserDestroy = subparsers.add_parser(
        "destroy",
        help="Destroy an object",
    )
    parserUnmanage = subparsers.add_parser(
        "unmanage",
        help="Unmanage an object",
    )
    parserUpdate = subparsers.add_parser(
        "update",
        help="Update an object",
    )
    #######
    # End of top level subcommands
    #######

    #######
    # subcommands "list", "create", "manage", "destroy", "unmanage", and "update"
    # have subcommands as well
    #######
    subparserList = parserList.add_subparsers(title="objectType", dest="objectType", required=True)
    subparserCreate = parserCreate.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    subparserManage = parserManage.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    subparserDestroy = parserDestroy.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    subparserUnmanage = parserUnmanage.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    subparserUpdate = parserUpdate.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    #######
    # end of subcommand "list", "create", "manage", "destroy", "unmanage", and "update"
    # subcommands
    #######

    #######
    # list 'X'
    #######
    subparserListApps = subparserList.add_parser(
        "apps",
        help="list apps",
    )
    subparserListAssets = subparserList.add_parser(
        "assets",
        help="list app assets",
    )
    subparserListBackups = subparserList.add_parser(
        "backups",
        help="list backups",
    )
    subparserListBuckets = subparserList.add_parser(
        "buckets",
        help="list buckets",
    )
    subparserListClouds = subparserList.add_parser(
        "clouds",
        help="list clouds",
    )
    subparserListClusters = subparserList.add_parser(
        "clusters",
        help="list clusters",
    )
    subparserListCredentials = subparserList.add_parser(
        "credentials",
        help="list credentials",
    )
    subparserListHooks = subparserList.add_parser("hooks", help="list hooks (executionHooks)")
    subparserListNamespaces = subparserList.add_parser(
        "namespaces",
        help="list namespaces",
    )
    subparserListProtections = subparserList.add_parser(
        "protections",
        help="list protection policies",
    )
    subparserListReplications = subparserList.add_parser(
        "replications",
        help="list replication policies",
    )
    subparserListScripts = subparserList.add_parser(
        "scripts",
        help="list scripts (hookSources)",
    )
    subparserListSnapshots = subparserList.add_parser(
        "snapshots",
        help="list snapshots",
    )
    subparserListStorageClasses = subparserList.add_parser(
        "storageclasses",
        help="list storageclasses",
    )
    subparserListUsers = subparserList.add_parser(
        "users",
        help="list users",
    )
    #######
    # end of list 'X'
    #######

    #######
    # list apps args and flags
    #######
    subparserListApps.add_argument(
        "-n", "--namespace", default=None, help="Only show apps from this namespace"
    )
    subparserListApps.add_argument(
        "-f",
        "--nameFilter",
        default=None,
        help="Filter app names by this value to minimize output (partial match)",
    )
    subparserListApps.add_argument(
        "-c", "--cluster", default=None, help="Only show apps from this cluster"
    )
    #######
    # end of list apps args and flags
    #######

    #######
    # list assets args and flags
    #######
    subparserListAssets.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="The appID from which to display the assets",
    )
    #######
    # end of list assets args and flags
    #######

    #######
    # list backups args and flags
    #######
    subparserListBackups.add_argument(
        "-a", "--app", default=None, help="Only show backups from this app"
    )
    #######
    # end of list backups args and flags
    #######

    #######
    # list buckets args and flags
    #######
    subparserListBuckets.add_argument(
        "-f",
        "--nameFilter",
        default=None,
        help="Filter app names by this value to minimize output (partial match)",
    )
    subparserListBuckets.add_argument(
        "-p",
        "--provider",
        default=None,
        help="Only show buckets of a single provider",
    )
    #######
    # end of list buckets args and flags
    #######

    #######
    # list clouds args and flags
    #######
    subparserListClouds.add_argument(
        "-t",
        "--cloudType",
        default=None,
        choices=["GCP", "Azure", "AWS", "Private"],
        help="Only show clouds of a single type",
    )
    #######
    # end of list clouds args and flags
    #######

    #######
    # list clusters args and flags
    #######
    subparserListClusters.add_argument(
        "-m",
        "--hideManaged",
        default=False,
        action="store_true",
        help="Hide managed clusters",
    )
    subparserListClusters.add_argument(
        "-u",
        "--hideUnmanaged",
        default=False,
        action="store_true",
        help="Hide unmanaged clusters",
    )
    subparserListClusters.add_argument(
        "-f",
        "--nameFilter",
        default=None,
        help="Filter cluster names by this value to minimize output (partial match)",
    )
    #######
    # end of list clusters args and flags
    #######

    #######
    # list credentials args and flags
    #######
    subparserListCredentials.add_argument(
        "-k",
        "--kubeconfigOnly",
        default=False,
        action="store_true",
        help="Only show kubeconfig credentials",
    )
    #######
    # end of list credentials args and flags
    #######

    #######
    # list hooks args and flags
    #######
    subparserListHooks.add_argument(
        "-a", "--app", default=None, help="Only show execution hooks from this app"
    )
    #######
    # end of list hooks args and flags
    #######

    #######
    # list namespaces args and flags
    #######
    subparserListNamespaces.add_argument(
        "-c", "--clusterID", default=None, help="Only show namespaces from this clusterID"
    )
    subparserListNamespaces.add_argument(
        "-f",
        "--nameFilter",
        default=None,
        help="Filter namespaces by this value to minimize output (partial match)",
    )
    subparserListNamespaces.add_argument(
        "-r",
        "--showRemoved",
        default=False,
        action="store_true",
        help="Show namespaces in a 'removed' state",
    )
    subparserListNamespaces.add_argument(
        "-u",
        "--unassociated",
        default=False,
        action="store_true",
        help="Only show namespaces which do not have any associatedApps",
    )
    subparserListNamespaces.add_argument(
        "-m",
        "--minutes",
        default=False,
        type=int,
        help="Only show namespaces created within the last X minutes",
    )
    #######
    # end of list namespaces args and flags
    #######

    #######
    # list protection policies args and flags
    #######
    subparserListProtections.add_argument(
        "-a", "--app", default=None, help="Only show protection policies from this app"
    )
    #######
    # end of list protection policies args and flags
    #######

    #######
    # list replication policies args and flags
    #######
    subparserListReplications.add_argument(
        "-a", "--app", default=None, help="Only show replication policies from this app"
    )
    #######
    # end of list replication policies args and flags
    #######

    #######
    # list scripts args and flags
    #######
    subparserListScripts.add_argument(
        "-s",
        "--getScriptSource",
        default=None,
        help="Provide a script name to view the script source code",
    )
    #######
    # end of list scripts args and flags
    #######

    #######
    # list snapshots args and flags
    #######
    subparserListSnapshots.add_argument(
        "-a", "--app", default=None, help="Only show snapshots from this app"
    )
    #######
    # end of list snapshots args and flags
    #######

    #######
    # list storageclasses args and flags
    #######
    subparserListStorageClasses.add_argument(
        "-t",
        "--cloudType",
        default=None,
        choices=["GCP", "Azure", "AWS", "Private"],
        help="Only show storageclasses of a single cloud type",
    )
    #######
    # end of list storageclasses args and flags
    #######

    #######
    # list users args and flags
    #######
    subparserListUsers.add_argument(
        "-f",
        "--nameFilter",
        default=None,
        help="Filter users by this value to minimize output (partial match)",
    )
    #######
    # end of list users args and flags
    #######

    #######
    # create 'X'
    #######
    subparserCreateBackup = subparserCreate.add_parser(
        "backup",
        help="create backup",
    )
    subparserCreateCluster = subparserCreate.add_parser(
        "cluster", help="create cluster (upload a K8s cluster kubeconfig to then manage)"
    )
    subparserCreateHook = subparserCreate.add_parser(
        "hook",
        help="create hook (executionHook)",
    )
    subparserCreateProtection = subparserCreate.add_parser(
        "protection",
        aliases=["protectionpolicy"],
        help="create protection policy",
    )
    subparserCreateReplication = subparserCreate.add_parser(
        "replication",
        help="create replication policy",
    )
    subparserCreateScript = subparserCreate.add_parser(
        "script",
        help="create script (hookSource)",
    )
    subparserCreateSnapshot = subparserCreate.add_parser(
        "snapshot",
        help="create snapshot",
    )
    #######
    # end of create 'X'
    #######

    #######
    # create backups args and flags
    #######
    subparserCreateBackup.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID to backup",
    )
    subparserCreateBackup.add_argument(
        "name",
        help="Name of backup to be taken",
    )
    subparserCreateBackup.add_argument(
        "-b",
        "--background",
        default=False,
        action="store_true",
        help="Run backup operation in the background",
    )
    #######
    # end of create backups args and flags
    #######

    #######
    # create cluster args and flags
    #######
    subparserCreateCluster.add_argument(
        "filePath",
        help="the local filesystem path to the cluster kubeconfig",
    )
    subparserCreateCluster.add_argument(
        "-c",
        "--cloudID",
        choices=(None if plaidMode else cloudList),
        default=(cloudList[0] if len(cloudList) == 1 else None),
        required=(False if len(cloudList) == 1 else True),
        help="The cloudID to add the cluster to (only required if # of clouds > 1)",
    )
    #######
    # end of create cluster args and flags
    #######

    #######
    # create hooks args and flags
    #######
    subparserCreateHook.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID to create an execution hook for",
    )
    subparserCreateHook.add_argument(
        "name",
        help="Name of the execution hook to be created",
    )
    subparserCreateHook.add_argument(
        "scriptID",
        choices=(None if plaidMode else scriptList),
        help="scriptID to use for the execution hook",
    )
    subparserCreateHook.add_argument(
        "-o",
        "--operation",
        choices=["pre-snapshot", "post-snapshot", "pre-backup", "post-backup", "post-restore"],
        required=True,
        type=str.lower,
        help="The operation type for the execution hook",
    )
    subparserCreateHook.add_argument(
        "-a",
        "--hookArguments",
        required=False,
        default=None,
        action="append",
        nargs="*",
        help="The (optional) arguments for the execution hook script",
    )
    subparserCreateHook.add_argument(
        "-r",
        "--containerRegex",
        default=None,
        # type=ascii,
        help="The (optional) container image name regex to match "
        + "(do not specify to match on all images)",
    )
    #######
    # end of create hooks args and flags
    #######

    #######
    # create protectionpolicy args and flags
    #######
    subparserCreateProtection.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of the application to create protection schedule for",
    )
    granArg = subparserCreateProtection.add_argument(
        "-g",
        "--granularity",
        required=True,
        choices=["hourly", "daily", "weekly", "monthly"],
        help="Must choose one of the four options for the schedule",
    )
    subparserCreateProtection.add_argument(
        "-b",
        "--backupRetention",
        type=int,
        required=True,
        choices=range(60),
        help="Number of backups to retain",
    )
    subparserCreateProtection.add_argument(
        "-s",
        "--snapshotRetention",
        type=int,
        required=True,
        choices=range(60),
        help="Number of snapshots to retain",
    )
    subparserCreateProtection.add_argument(
        "-M", "--dayOfMonth", type=int, choices=range(1, 32), help="Day of the month"
    )
    subparserCreateProtection.add_argument(
        "-W",
        "--dayOfWeek",
        type=int,
        choices=range(7),
        help="0 = Sunday ... 6 = Saturday",
    )
    subparserCreateProtection.add_argument(
        "-H", "--hour", type=int, choices=range(24), help="Hour in military time"
    )
    subparserCreateProtection.add_argument(
        "-m", "--minute", default=0, type=int, choices=range(60), help="Minute"
    )
    #######
    # end of create protectionpolicy args and flags
    #######

    #######
    # create replication policy args and flags
    #######
    subparserCreateReplication.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of the application to create the replication policy for",
    )
    subparserCreateReplication.add_argument(
        "-c",
        "--destClusterID",
        choices=(None if plaidMode else destclusterList),
        help="the destination cluster ID to replicate to",
        required=True,
    )
    subparserCreateReplication.add_argument(
        "-n",
        "--destNamespace",
        help="the namespace to create resources on the destination cluster",
        required=True,
    )
    subparserCreateReplication.add_argument(
        "-s",
        "--destStorageClass",
        choices=(None if plaidMode else storageClassList),
        default=None,
        help="the destination storage class to use for volume creation",
    )
    subparserCreateReplication.add_argument(
        "-f",
        "--replicationFrequency",
        choices=[
            "5m",
            "10m",
            "15m",
            "20m",
            "30m",
            "1h",
            "2h",
            "3h",
            "4h",
            "6h",
            "8h",
            "12h",
            "24h",
        ],
        help="the frequency that a snapshot is taken and replicated",
        required=True,
    )
    subparserCreateReplication.add_argument(
        "-o",
        "--offset",
        default="00:00",
        help="the amount of time to offset the replication snapshot as to not interfere with "
        + "other operations, in 'hh:mm' or 'mm' format",
    )
    #######
    # end of create replication policy args and flags
    #######

    #######
    # create script args and flags
    #######
    subparserCreateScript.add_argument(
        "name",
        help="Name of the script",
    )
    subparserCreateScript.add_argument(
        "filePath",
        help="the local filesystem path to the script",
    )
    subparserCreateScript.add_argument(
        "-d",
        "--description",
        default=None,
        help="The optional description of the script",
    )
    #######
    # end of create script args and flags
    #######

    #######
    # create snapshot args and flags
    #######
    subparserCreateSnapshot.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID to snapshot",
    )
    subparserCreateSnapshot.add_argument(
        "name",
        help="Name of snapshot to be taken",
    )
    subparserCreateSnapshot.add_argument(
        "-b",
        "--background",
        default=False,
        action="store_true",
        help="Run snapshot operation in the background",
    )
    #######
    # end of create snapshot args and flags
    #######

    #######
    # manage 'X'
    #######
    subparserManageApp = subparserManage.add_parser(
        "app",
        help="manage app",
    )
    subparserManageBucket = subparserManage.add_parser(
        "bucket",
        help="manage bucket",
    )
    subparserManageCluster = subparserManage.add_parser(
        "cluster",
        help="manage cluster",
    )
    #######
    # end of manage 'X'
    #######

    #######
    # manage app args and flags
    #######
    subparserManageApp.add_argument("appName", help="The logical name of the newly defined app")
    subparserManageApp.add_argument(
        "namespace",
        choices=(None if plaidMode else namespaceList),
        help="The namespace to move from undefined (aka unmanaged) to defined (aka managed)",
    )
    subparserManageApp.add_argument(
        "-l",
        "--labelSelectors",
        required=False,
        default=None,
        help="Optional label selectors to filter resources to be included or excluded from "
        + "the application definition",
    )
    subparserManageApp.add_argument(
        "clusterID",
        choices=(None if plaidMode else clusterList),
        help="The clusterID hosting the newly defined app",
    )
    #######
    # end of manage app args and flags
    #######

    #######
    # manage bucket args and flags
    #######
    subparserManageBucket.add_argument(
        "provider",
        choices=["aws", "azure", "gcp", "generic-s3", "ontap-s3", "storagegrid-s3"],
        help="The infrastructure provider of the storage bucket",
    )
    subparserManageBucket.add_argument(
        "bucketName",
        help="The existing bucket name",
    )
    credGroup = subparserManageBucket.add_argument_group(
        "credentialGroup",
        "Either an (existing credentialID) OR (accessKey AND accessSecret)",
    )
    credGroup.add_argument(
        "-c",
        "--credentialID",
        choices=(None if plaidMode else credentialList),
        help="The ID of the credentials used to access the bucket",
        default=None,
    )
    credGroup.add_argument(
        "--accessKey",
        help="The access key of the bucket",
        default=None,
    )
    credGroup.add_argument(
        "--accessSecret",
        help="The access secret of the bucket",
        default=None,
    )
    subparserManageBucket.add_argument(
        "-u",
        "--serverURL",
        help="The URL to the base path of the bucket "
        + "(only needed for 'aws', 'generic-s3', 'ontap-s3' 'storagegrid-s3')",
        default=None,
    )
    subparserManageBucket.add_argument(
        "-a",
        "--storageAccount",
        help="The  Azure storage account name (only needed for 'Azure')",
        default=None,
    )
    #######
    # end of manage bucket args and flags
    #######

    #######
    # manage cluster args and flags
    #######
    subparserManageCluster.add_argument(
        "clusterID",
        choices=(None if plaidMode else clusterList),
        help="clusterID of the cluster to manage",
    )
    subparserManageCluster.add_argument(
        "storageClassID",
        choices=(None if plaidMode else storageClassList),
        help="Default storage class ID",
    )
    #######
    # end of manage cluster args and flags
    #######

    #######
    # destroy 'X'
    #######
    subparserDestroyBackup = subparserDestroy.add_parser(
        "backup",
        help="destroy backup",
    )
    subparserDestroyCredential = subparserDestroy.add_parser(
        "credential",
        help="destroy credential",
    )
    subparserDestroyHook = subparserDestroy.add_parser(
        "hook",
        help="destroy hook (executionHook)",
    )
    subparserDestroyProtection = subparserDestroy.add_parser(
        "protection",
        help="destroy protection policy",
    )
    subparserDestroyReplication = subparserDestroy.add_parser(
        "replication",
        help="destroy replication policy",
    )
    subparserDestroyScript = subparserDestroy.add_parser(
        "script",
        help="destroy script (hookSource)",
    )
    subparserDestroySnapshot = subparserDestroy.add_parser(
        "snapshot",
        help="destroy snapshot",
    )
    #######
    # end of destroy 'X'
    #######

    #######

    #######
    # destroy backup args and flags
    #######
    subparserDestroyBackup.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of app to destroy backups from",
    )
    subparserDestroyBackup.add_argument(
        "backupID",
        choices=(None if plaidMode else backupList),
        help="backupID to destroy",
    )
    #######
    # end of destroy backup args and flags
    #######

    #######
    # destroy credential args and flags
    #######
    subparserDestroyCredential.add_argument(
        "credentialID",
        choices=(None if plaidMode else credentialList),
        help="credentialID to destroy",
    )
    #######
    # end of destroy credential args and flags
    #######

    #######
    # destroy hook args and flags
    #######
    subparserDestroyHook.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of app to destroy hooks from",
    )
    subparserDestroyHook.add_argument(
        "hookID",
        choices=(None if plaidMode else hookList),
        help="hookID to destroy",
    )
    #######
    # end of destroy hook args and flags
    #######

    #######
    # destroy protection args and flags
    #######
    subparserDestroyProtection.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of app to destroy protection policy from",
    )
    subparserDestroyProtection.add_argument(
        "protectionID",
        choices=(None if plaidMode else protectionList),
        help="protectionID to destroy",
    )
    #######
    # end of destroy protection args and flags
    #######

    #######
    # destroy replication args and flags
    #######
    subparserDestroyReplication.add_argument(
        "replicationID",
        choices=(None if plaidMode else replicationList),
        help="replicationID to destroy",
    )
    #######
    # end of destroy replication args and flags
    #######

    #######
    # destroy script args and flags
    #######
    subparserDestroyScript.add_argument(
        "scriptID",
        choices=(None if plaidMode else scriptList),
        help="scriptID of script to destroy",
    )
    #######
    # end of destroy script args and flags
    #######

    #######
    # destroy snapshot args and flags
    #######
    subparserDestroySnapshot.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of app to destroy snapshot from",
    )
    subparserDestroySnapshot.add_argument(
        "snapshotID",
        choices=(None if plaidMode else snapshotList),
        help="snapshotID to destroy",
    )
    #######
    # end of destroy snapshot args and flags
    #######

    #######
    # unmanage 'X'
    #######
    subparserUnmanageApp = subparserUnmanage.add_parser(
        "app",
        help="unmanage app",
    )
    subparserUnmanageBucket = subparserUnmanage.add_parser(
        "bucket",
        help="unmanage bucket",
    )
    subparserUnmanageCluster = subparserUnmanage.add_parser(
        "cluster",
        help="unmanage cluster",
    )
    #######
    # end of unmanage 'X'
    #######

    #######
    # unmanage app args and flags
    #######
    subparserUnmanageApp.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID of app to move from managed to unmanaged",
    )
    #######
    # end of unmanage app args and flags
    #######

    #######
    # unmanage bucket args and flags
    #######
    subparserUnmanageBucket.add_argument(
        "bucketID",
        choices=(None if plaidMode else bucketList),
        help="bucketID of bucket to unmanage",
    )
    #######
    # end of unmanage app args and flags
    #######

    #######
    # unmanage cluster args and flags
    #######
    subparserUnmanageCluster.add_argument(
        "clusterID",
        choices=(None if plaidMode else clusterList),
        help="clusterID of the cluster to unmanage",
    )
    #######
    # end of unmanage cluster args and flags
    #######

    #######
    # deploy args and flags
    #######
    parserDeploy.add_argument(
        "app",
        help="name of app",
    )
    parserDeploy.add_argument(
        "chart",
        choices=(None if plaidMode else chartsList),
        help="chart to deploy",
    )
    parserDeploy.add_argument(
        "-n", "--namespace", required=True, help="Namespace to deploy into (must not already exist)"
    )
    parserDeploy.add_argument(
        "-f",
        "--values",
        required=False,
        action="append",
        nargs="*",
        help="Specify Helm values in a YAML file",
    )
    parserDeploy.add_argument(
        "--set",
        required=False,
        action="append",
        nargs="*",
        help="Individual helm chart parameters",
    )
    #######
    # end of deploy args and flags
    #######

    #######
    # clone args and flags
    #######
    parserClone.add_argument(
        "-b",
        "--background",
        default=False,
        action="store_true",
        help="Run clone operation in the background",
    )
    parserClone.add_argument(
        "--cloneAppName",
        required=False,
        default=None,
        help="Clone app name",
    )
    parserClone.add_argument(
        "--cloneNamespace",
        required=False,
        default=None,
        help="Clone namespace name (optional, if not specified cloneAppName is used)",
    )
    parserClone.add_argument(
        "--clusterID",
        choices=(None if plaidMode else destclusterList),
        required=False,
        default=None,
        help="Cluster to clone into (can be same as source)",
    )
    group = parserClone.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--backupID",
        choices=(None if plaidMode else backupList),
        required=False,
        default=None,
        help="Source backup to clone",
    )
    group.add_argument(
        "--snapshotID",
        choices=(None if plaidMode else snapshotList),
        required=False,
        default=None,
        help="Source snapshot to restore from",
    )
    group.add_argument(
        "--sourceAppID",
        choices=(None if plaidMode else appList),
        required=False,
        default=None,
        help="Source app to clone",
    )
    #######
    # end of clone args and flags
    #######

    #######
    # restore args and flags
    #######
    parserRestore.add_argument(
        "-b",
        "--background",
        default=False,
        action="store_true",
        help="Run restore operation in the background",
    )
    parserRestore.add_argument(
        "appID",
        choices=(None if plaidMode else appList),
        help="appID to restore",
    )
    group = parserRestore.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--backupID",
        choices=(None if plaidMode else backupList),
        required=False,
        default=None,
        help="Source backup to restore from",
    )
    group.add_argument(
        "--snapshotID",
        choices=(None if plaidMode else snapshotList),
        required=False,
        default=None,
        help="Source snapshot to restore from",
    )
    #######
    # end of restore args and flags
    #######

    #######
    # update 'X'
    #######
    subparserUpdateReplication = subparserUpdate.add_parser(
        "replication",
        help="update replication",
    )
    #######
    # end of update 'X'
    #######

    #######
    # update replication args and flags
    #######
    subparserUpdateReplication.add_argument(
        "replicationID",
        choices=(None if plaidMode else replicationList),
        help="replicationID to update",
    )
    subparserUpdateReplication.add_argument(
        "operation",
        choices=["failover", "reverse", "resync"],
        help="whether to failover, reverse, or resync the replication policy",
    )
    subparserUpdateReplication.add_argument(
        "--dataSource",
        "-s",
        default=None,
        help="resync operation: the new source replication data (either appID or clusterID)",
    )
    #######
    # end of update replication args and flags
    #######

    args = parser.parse_args()
    # print(f"args: {args}")
    if hasattr(args, "granularity"):
        if args.granularity == "hourly":
            if args.hour:
                raise argparse.ArgumentError(granArg, " hourly must not specify -H / --hour")
            if not hasattr(args, "minute"):
                raise argparse.ArgumentError(granArg, " hourly requires -m / --minute")
            args.hour = "*"
            args.dayOfWeek = "*"
            args.dayOfMonth = "*"
        elif args.granularity == "daily":
            if type(args.hour) != int and not args.hour:
                raise argparse.ArgumentError(granArg, " daily requires -H / --hour")
            args.dayOfWeek = "*"
            args.dayOfMonth = "*"
        elif args.granularity == "weekly":
            if type(args.hour) != int and not args.hour:
                raise argparse.ArgumentError(granArg, " weekly requires -H / --hour")
            if type(args.dayOfWeek) != int and not args.dayOfWeek:
                raise argparse.ArgumentError(granArg, " weekly requires -W / --dayOfWeek")
            args.dayOfMonth = "*"
        elif args.granularity == "monthly":
            if type(args.hour) != int and not args.hour:
                raise argparse.ArgumentError(granArg, " monthly requires -H / --hour")
            if args.dayOfWeek:
                raise argparse.ArgumentError(granArg, " monthly must not specify -W / --dayOfWeek")
            if not args.dayOfMonth:
                raise argparse.ArgumentError(granArg, " monthly requires -M / --dayOfMonth")
            args.dayOfWeek = "*"

    tk = toolkit()
    if args.subcommand == "deploy":
        tk.deploy(
            args.chart,
            args.app,
            args.namespace,
            args.set,
            args.values,
            args.verbose,
            args.quiet,
        )

    elif args.subcommand == "list" or args.subcommand == "get":
        if args.objectType == "apps":
            rc = astraSDK.getApps(quiet=args.quiet, verbose=args.verbose, output=args.output).main(
                namespace=args.namespace,
                nameFilter=args.nameFilter,
                cluster=args.cluster,
            )
            if rc is False:
                print("astraSDK.getApps() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "assets":
            rc = astraSDK.getAppAssets(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(args.appID)
            if rc is False:
                print("astraSDK.getAppAssets() failed")
            else:
                sys.exit(0)
        elif args.objectType == "backups":
            rc = astraSDK.getBackups(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.getBackups() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "buckets":
            rc = astraSDK.getBuckets(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(nameFilter=args.nameFilter, provider=args.provider)
            if rc is False:
                print("astraSDK.getBuckets() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "clouds":
            rc = astraSDK.getClouds(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(cloudType=args.cloudType)
            if rc is False:
                print("astraSDK.getClouds() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "clusters":
            rc = astraSDK.getClusters(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                hideManaged=args.hideManaged,
                hideUnmanaged=args.hideUnmanaged,
                nameFilter=args.nameFilter,
            )
            if rc is False:
                print("astraSDK.getClusters() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "credentials":
            rc = astraSDK.getCredentials(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(kubeconfigOnly=args.kubeconfigOnly)
            if rc is False:
                print("astraSDK.getCredentials() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "hooks":
            rc = astraSDK.getHooks(quiet=args.quiet, verbose=args.verbose, output=args.output).main(
                appFilter=args.app
            )
            if rc is False:
                print("astraSDK.getHooks() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "protections":
            rc = astraSDK.getProtectionpolicies(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.getProtectionpolicies() failed")
            else:
                sys.exit(0)
        elif args.objectType == "replications":
            rc = astraSDK.getReplicationpolicies(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                print("astraSDK.getReplicationpolicies() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "namespaces":
            rc = astraSDK.getNamespaces(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                clusterID=args.clusterID,
                nameFilter=args.nameFilter,
                showRemoved=args.showRemoved,
                unassociated=args.unassociated,
                minuteFilter=args.minutes,
            )
            if rc is False:
                print("astraSDK.getNamespaces() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "scripts":
            if args.getScriptSource:
                args.quiet = True
                args.output = "json"
            rc = astraSDK.getScripts(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(scriptSourceName=args.getScriptSource)
            if rc is False:
                print("astraSDK.getScripts() failed")
                sys.exit(1)
            else:
                if args.getScriptSource:
                    if len(rc["items"]) == 0:
                        print(f"Script of name '{args.getScriptSource}' not found.")
                    for script in rc["items"]:
                        print(base64.b64decode(script["source"]).decode("utf-8"))
                sys.exit(0)
        elif args.objectType == "snapshots":
            rc = astraSDK.getSnaps(quiet=args.quiet, verbose=args.verbose, output=args.output).main(
                appFilter=args.app
            )
            if rc is False:
                print("astraSDK.getSnaps() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "storageclasses":
            rc = astraSDK.getStorageClasses(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(cloudType=args.cloudType)
            if rc is False:
                print("astraSDK.getStorageClasses() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "users":
            rc = astraSDK.getUsers(quiet=args.quiet, verbose=args.verbose, output=args.output).main(
                nameFilter=args.nameFilter
            )
            if rc is False:
                print("astraSDK.getUsers() failed")
                sys.exit(1)
            else:
                sys.exit(0)

    elif args.subcommand == "create":
        if args.objectType == "backup":
            rc = doProtectionTask(
                args.objectType, args.appID, args.name, args.background
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
            rc = astraSDK.createCredential(quiet=args.quiet, verbose=args.verbose).main(
                kubeconfigDict["clusters"][0]["name"], "kubeconfig", {"base64": encodedStr}
            )
            if rc:
                rc = astraSDK.addCluster(quiet=args.quiet, verbose=args.verbose).main(
                    args.cloudID,
                    rc["id"],
                )
                if rc is False:
                    print("astraSDK.createCloud() failed")
                else:
                    sys.exit(0)
            else:
                print("astraSDK.createCredential() failed")
                sys.exit(1)
        elif args.objectType == "hook":
            rc = astraSDK.createHook(quiet=args.quiet, verbose=args.verbose).main(
                args.appID,
                args.name,
                args.scriptID,
                args.operation.split("-")[0],
                args.operation.split("-")[1],
                createHookList(args.hookArguments),
                args.containerRegex,
            )
            if rc is False:
                print("astraSDK.createHook() failed")
            else:
                sys.exit(0)
        elif args.objectType == "protection" or args.objectType == "protectionpolicy":
            rc = astraSDK.createProtectionpolicy(quiet=args.quiet, verbose=args.verbose).main(
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
                print("astraSDK.createProtectionpolicy() failed")
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
            if plaidMode:
                apps = astraSDK.getApps().main()
            for app in apps["items"]:
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
            rc = astraSDK.createReplicationpolicy(quiet=args.quiet, verbose=args.verbose).main(
                args.appID,
                args.destClusterID,
                nsMapping,
                destinationStorageClass=args.destStorageClass,
            )
            if rc:
                prc = astraSDK.createProtectionpolicy(quiet=args.quiet, verbose=args.verbose).main(
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
                    print("astraSDK.createProtectionpolicy() failed")
                    sys.exit(1)
            else:
                print("astraSDK.createReplicationpolicy() failed")
                sys.exit(1)
        elif args.objectType == "script":
            with open(args.filePath, encoding="utf8") as f:
                encodedStr = base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")
            rc = astraSDK.createScript(quiet=args.quiet, verbose=args.verbose).main(
                name=args.name, source=encodedStr, description=args.description
            )
            if rc is False:
                print("astraSDK.createScript() failed")
            else:
                sys.exit(0)
        elif args.objectType == "snapshot":
            rc = doProtectionTask(
                args.objectType, args.appID, args.name, args.background
            )
            if rc is False:
                print("doProtectionTask() failed")
                sys.exit(1)
            else:
                sys.exit(0)

    elif args.subcommand == "manage" or args.subcommand == "define":
        if args.objectType == "app":
            rc = astraSDK.manageApp(quiet=args.quiet, verbose=args.verbose).main(
                args.appName, args.namespace, args.clusterID, args.labelSelectors
            )
            if rc is False:
                print("astraSDK.manageApp() failed")
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
                crc = astraSDK.createCredential(quiet=args.quiet, verbose=args.verbose).main(
                    args.bucketName,
                    "s3",
                    {"accessKey": encodedKey, "accessSecret": encodedSecret},
                    cloudName="s3",
                )
                if crc:
                    args.credentialID = crc["id"]
                else:
                    print("astraSDK.createCredential() failed")
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
            rc = astraSDK.manageBucket(quiet=args.quiet, verbose=args.verbose).main(
                args.bucketName, args.credentialID, args.provider, bucketParameters
            )
            if rc is False:
                print("astraSDK.manageBucket() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cluster":
            rc = astraSDK.manageCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.clusterID, args.storageClassID
            )
            if rc is False:
                print("astraSDK.manageCluster() failed")
                sys.exit(1)
            else:
                sys.exit(0)

    elif args.subcommand == "destroy":
        if args.objectType == "backup":
            rc = astraSDK.destroyBackup(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.backupID
            )
            if rc:
                print(f"Backup {args.backupID} destroyed")
            else:
                print(f"Failed destroying backup: {args.backupID}")
        elif args.objectType == "credential":
            rc = astraSDK.destroyCredential(quiet=args.quiet, verbose=args.verbose).main(
                args.credentialID
            )
            if rc:
                print(f"Credential {args.credentialID} destroyed")
            else:
                print(f"Failed destroying credential: {args.credentialID}")
        elif args.objectType == "hook":
            rc = astraSDK.destroyHook(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.hookID
            )
            if rc:
                print(f"Hook {args.hookID} destroyed")
            else:
                print(f"Failed destroying hook: {args.hookID}")
        elif args.objectType == "protection":
            rc = astraSDK.destroyProtectiontionpolicy(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.protectionID
            )
            if rc:
                print(f"Protection policy {args.protectionID} destroyed")
            else:
                print(f"Failed destroying protection policy: {args.protectionID}")
        elif args.objectType == "replication":
            if plaidMode:
                replicationDict = astraSDK.getReplicationpolicies().main()
            rc = astraSDK.destroyReplicationpolicy(quiet=args.quiet, verbose=args.verbose).main(
                args.replicationID
            )
            if rc:
                print(f"Replication policy {args.replicationID} destroyed")
                # The underlying replication schedule(s) (protection policy) must also be deleted
                protectionDict = astraSDK.getProtectionpolicies().main()
                for replication in replicationDict["items"]:
                    if replication["id"] == args.replicationID:
                        for protection in protectionDict["items"]:
                            if (
                                protection["appID"] == replication["sourceAppID"]
                                or protection["appID"] == replication["destinationAppID"]
                            ) and protection.get("replicate") == "true":
                                if astraSDK.destroyProtectiontionpolicy(
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
            rc = astraSDK.destroyScript(quiet=args.quiet, verbose=args.verbose).main(args.scriptID)
            if rc:
                print(f"Script {args.scriptID} destroyed")
            else:
                print(f"Failed destroying script: {args.scriptID}")
        elif args.objectType == "snapshot":
            rc = astraSDK.destroySnapshot(quiet=args.quiet, verbose=args.verbose).main(
                args.appID, args.snapshotID
            )
            if rc:
                print(f"Snapshot {args.snapshotID} destroyed")
            else:
                print(f"Failed destroying snapshot: {args.snapshotID}")

    elif args.subcommand == "unmanage":
        if args.objectType == "app":
            rc = astraSDK.unmanageApp(quiet=args.quiet, verbose=args.verbose).main(args.appID)
            if rc is False:
                print("astraSDK.unmanageApp() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "bucket":
            rc = astraSDK.unmanageBucket(quiet=args.quiet, verbose=args.verbose).main(args.bucketID)
            if rc is False:
                print("astraSDK.unmanageBucket() failed")
                sys.exit(1)
            else:
                sys.exit(0)
        elif args.objectType == "cluster":
            rc = astraSDK.unmanageCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.clusterID
            )
            if rc:
                # ACC clusters+credentials also should be deleted
                if plaidMode:
                    clusterDict = astraSDK.getClusters(quiet=True).main()
                acsList = ["gke", "aks", "eks"]
                for cluster in clusterDict["items"]:
                    if cluster["id"] == args.clusterID and cluster["clusterType"] not in acsList:
                        if astraSDK.deleteCluster(quiet=args.quiet, verbose=args.verbose).main(
                            args.clusterID, cluster["cloudID"]
                        ):
                            if astraSDK.destroyCredential(
                                quiet=args.quiet, verbose=args.verbose
                            ).main(cluster.get("credentialID")):
                                print(f"Credential deleted")
                            else:
                                print("astraSDK.destroyCredential() failed")
                                sys.exit(1)
                        else:
                            print("astraSDK.deleteCluster() failed")
                            sys.exit(1)
                sys.exit(0)
            else:
                print("astraSDK.unmanageCluster() failed")
                sys.exit(1)

    elif args.subcommand == "restore":
        rc = astraSDK.restoreApp(quiet=args.quiet, verbose=args.verbose).main(
            args.appID, backupID=args.backupID, snapshotID=args.snapshotID
        )
        if rc:
            if args.background:
                print("Restore job submitted successfully")
                print("Background restore flag selected, run 'list apps' to get status")
                sys.exit(0)
            print("Restore job in progress...", end="")
            sys.stdout.flush()
            while True:
                restoreApps = astraSDK.getApps().main()
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
                time.sleep(5)
        else:
            print("Submitting restore job failed.")
            sys.exit(3)

    elif args.subcommand == "clone":
        if not args.cloneAppName:
            args.cloneAppName = input("App name for the clone: ")
        if not args.clusterID:
            print("Select destination cluster for the clone")
            print("Index\tClusterID\t\t\t\tclusterName\tclusterPlatform")
            args.clusterID = userSelect(destCluster, ["id", "name", "clusterType"])
        # Determine sourceClusterID and the appID (appID could be provided by args.sourceAppID,
        # however if it's not that value will be 'None', and if so it needs to stay 'None' when
        # a backup or snapshot ID is provided for the app to be cloned from the correctly).
        sourceClusterID = ""
        appIDstr = ""
        # Handle -f/--fast/plaidMode cases
        if plaidMode:
            apps = astraSDK.getApps().main()
        if args.sourceAppID:
            for app in apps["items"]:
                if app["id"] == args.sourceAppID:
                    sourceClusterID = app["clusterID"]
                    appIDstr = app["id"]
        elif args.backupID:
            if plaidMode:
                backups = astraSDK.getBackups().main()
            for app in apps["items"]:
                for backup in backups["items"]:
                    if app["id"] == backup["appID"] and backup["id"] == args.backupID:
                        sourceClusterID = app["clusterID"]
                        appIDstr = app["id"]
        elif args.snapshotID:
            if plaidMode:
                snapshots = astraSDK.getSnaps().main()
            for app in apps["items"]:
                for snapshot in snapshots["items"]:
                    if app["id"] == snapshot["appID"] and snapshot["id"] == args.snapshotID:
                        sourceClusterID = app["clusterID"]
                        appIDstr = app["id"]
        # Ensure appIDstr is not equal to "", if so bad values were passed in with plaidMode
        if appIDstr == "":
            print(
                "Error: the corresponding appID was not found in the system, please check "
                + "your inputs and try again."
            )
            sys.exit(1)

        tk.clone(
            args.cloneAppName,
            args.clusterID,
            sourceClusterID,
            appIDstr,
            args.cloneNamespace,
            backupID=args.backupID,
            snapshotID=args.snapshotID,
            sourceAppID=args.sourceAppID,
            background=args.background,
            verbose=args.verbose,
        )

    elif args.subcommand == "update":
        if args.objectType == "replication":
            # Gather replication data
            if plaidMode:
                replicationDict = astraSDK.getReplicationpolicies().main()
                if not replicationDict: # Gracefully handle ACS env
                    print("Error: 'replication' commands are currently only supported in ACC.")
                    sys.exit(1)
            repl = None
            for replication in replicationDict["items"]:
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
                    rc = astraSDK.updateReplicationpolicy(
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
                    rc = astraSDK.updateReplicationpolicy(
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
                rc = astraSDK.updateReplicationpolicy(quiet=args.quiet, verbose=args.verbose).main(
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
                rc = astraSDK.updateReplicationpolicy(quiet=args.quiet, verbose=args.verbose).main(
                    args.replicationID, "failedOver"
                )
            # Exit based on response
            if rc:
                print(f"Replication {args.operation} initiated")
                sys.exit(0)
            else:
                print("astraSDK.updateReplicationpolicy() failed")
                sys.exit(1)


if __name__ == "__main__":
    main()
