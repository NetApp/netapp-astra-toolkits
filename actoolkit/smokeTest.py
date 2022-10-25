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

import helpers
import sys
import os
import json
import time
import kubernetes
from termcolor import colored
from datetime import datetime, timedelta


def getItems(noun, errorCounter=0):
    """Runs a 'toolkit list {noun}' command, returns a python dict of response"""
    print(colored(f"    └──> getItems({noun})", "magenta"))
    try:
        return json.loads(
            helpers.run(f"./toolkit.py -o json list {noun}", captureOutput=True).decode("utf-8")
        )
    except:
        if errorCounter < 10:
            print(
                colored(
                    f"    └──> ERROR: './toolkit.py list {noun}' failed, "
                    + "sleeping 10 and trying again",
                    "red",
                )
            )
        else:
            print(
                colored(
                    f"    └──> ERROR: './toolkit.py list {noun}' failed 10 times, exiting", "red"
                )
            )
            sys.exit(1)
        time.sleep(10)
        return getItems(noun, errorCounter + 1)


def manageClusters(clusters, storageClasses):
    """Manages all non-manged clusters"""
    print(colored("──> manageClusters(clusters, storageClasses)", "cyan"))
    for cluster in clusters["items"]:
        clusterManaged = False
        if cluster["managedState"] != "managed":
            for sc in storageClasses["items"]:
                if (
                    cluster["id"] == sc["clusterID"]
                    and sc["provisioner"] == "csi.trident.netapp.io"
                    and not clusterManaged
                ):
                    print(colored(f"    └──> {cluster['name']} cluster being managed", "yellow"))
                    helpers.run(f"./toolkit.py -f manage cluster {cluster['id']} {sc['id']}")
                    clusterManaged = True
            # We want NetApp SCs to be highest priority, so doing a second loop for EBS-CSI
            for sc in storageClasses["items"]:
                if (
                    cluster["id"] == sc["clusterID"]
                    and sc["provisioner"] == "ebs.csi.aws.com"
                    and not clusterManaged
                ):
                    print(colored(f"    └──> {cluster['name']} cluster being managed", "yellow"))
                    helpers.run(f"./toolkit.py -f manage cluster {cluster['id']} {sc['id']}")
                    clusterManaged = True


def checkIfManaged(noun):
    """Ensures a given {noun} has all objects in a managed state"""
    print(colored(f"──> checkIfManaged({noun})", "cyan"))
    objects = getItems(noun)
    for obj in objects["items"]:
        if obj["managedState"] == "managed":
            print(colored(f"    └──> {obj['name']} successfully managed", "blue"))
        else:
            print(colored(f"    └──> ERROR: {noun} not managed", "red"))
            sys.exit(1)
    return objects


def waitForPodsRunning(namespace):
    """Ensures all pods in {namespace} are in a running state"""
    print(colored(f"──> waitForPodsRunning({namespace})", "cyan"))
    clusters = getItems("clusters")
    contexts, _ = kubernetes.config.list_kube_config_contexts()
    # Loop through clusters and contexts, find matches and open api_client
    for cluster in clusters["items"]:
        for context in contexts:
            if cluster["name"] in context["name"]:
                client = kubernetes.client.CoreV1Api(
                    api_client=kubernetes.config.new_client_from_config(context=context["name"])
                )
                try:
                    allPodsRunning = False
                    while not allPodsRunning:
                        allPodsRunning = True
                        podResp = client.list_pod_for_all_namespaces(
                            _preload_content=False, _request_timeout=5
                        )
                        pods = json.loads(podResp.data)
                        for pod in pods["items"]:
                            if pod["metadata"]["namespace"] == namespace:
                                if pod["status"]["phase"] != "Running":
                                    print(
                                        colored(
                                            f"    └──> {pod['metadata']['name']} in "
                                            + f"{pod['status']['phase']} phase, "
                                            + "sleeping for 20 seconds",
                                            "yellow",
                                        )
                                    )
                                    allPodsRunning = False
                                    time.sleep(20)
                except kubernetes.client.rest.ApiException as e:
                    print("Exception when calling list_pod_for_all_namespaces: %s\n" % e)
                print(
                    colored(f"    └──> {namespace} pods in {cluster['name']} all running", "blue")
                )


def waitForClusterRunning():
    """Ensures all newly managed clusters are in a 'running' state"""
    print(colored(f"──> waitForClusterRunning()", "cyan"))
    clusters = getItems("clusters")
    allClustersRunning = False
    while not allClustersRunning:
        allClustersRunning = True
        for cluster in clusters["items"]:
            if cluster["state"] != "running":
                print(
                    colored(
                        f"    └──> {cluster['name']} in {cluster['state']} state, "
                        + "sleeping for 20 seconds",
                        "yellow",
                    )
                )
                allClustersRunning = False
            else:
                print(colored(f"    └──> {cluster['name']} in running state", "blue"))
        if not allClustersRunning:
            time.sleep(20)
            clusters = getItems("clusters")


def clusterManagement():
    """Gets all clusters and storageClasses, manages those that aren't managed,
    then checks to ensure all clusters are managed, if so returns cluster dict"""
    print(colored("──> clusterManagement()", "cyan"))
    clusters = getItems("clusters")
    storageClasses = getItems("storageclasses")
    manageClusters(clusters, storageClasses)
    checkIfManaged("clusters")
    waitForPodsRunning("trident")
    waitForClusterRunning()


def deployApp(appName, deployCommand):
    """Deploys an app {appName} via {deployCommand} assuming not already deployed"""
    print(colored(f"──> deployApp({appName}, {deployCommand})", "cyan"))

    # Get all the apps
    deployApp = True
    apps = getItems("apps")
    namespaces = getItems("namespaces")

    # Check to see if the apps are already present
    for app in apps["items"]:
        if app["name"] == appName:
            deployApp = False
    if deployApp:
        for ns in namespaces["items"]:
            if ns["name"] == appName and (
                datetime.utcnow()
                - datetime.strptime(ns["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ")
            ) < timedelta(minutes=60):
                deployApp = False

    # Deploy apps if needed
    if deployApp:
        print(colored(f"    └──> {appName} being deployed", "yellow"))
        if "helm install" in deployCommand:
            helpers.run(f"kubectl create namespace {appName}", ignoreErrors=True)
        helpers.run(deployCommand)


def appManagement(deployedApps):
    """Gets all applications of type namespace, if they're not managed then manage them"""
    print(colored(f"──> appManagement({deployedApps})", "cyan"))

    # Loop until the app is in a managed state
    for deployedApp in deployedApps:
        appManaged = False
        while not appManaged:

            # Get the apps
            apps = getItems("apps")
            namespaces = getItems("namespaces")

            # Figure out if the app is defined
            for app in apps["items"]:
                if app["name"] == deployedApp and app["state"] == "ready":
                    appManaged = True
                    print(colored(f"    └──> {app['name']} successfully defined", "blue"))

            # If the app isn't defined, then manage the namespace
            if not appManaged:
                for app in namespaces["items"]:
                    if (
                        app["name"] == deployedApp
                        and app["namespaceState"] == "discovered"
                        and (
                            datetime.utcnow()
                            - datetime.strptime(
                                app["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ"
                            )
                        )
                        < timedelta(minutes=10)
                    ):
                        print(colored(f"    └──> {app['name']} app being managed", "yellow"))
                        helpers.run(
                            f"./toolkit.py -f manage app {app['name']} {app['name']} "
                            + f"{app['clusterID']} --labelSelectors "
                            + f"app.kubernetes.io/instance={app['name']}"
                        )

                # Sleep if things aren't managed yet
                print(colored("    └──> sleeping for 10 seconds for app management", "yellow"))
                time.sleep(10)


def createProtectionObject(noun, appID=None):
    """Takes a background {noun} (snapshot/backup) of {appID} or all apps if appID=None"""
    print(colored(f"──> createProtectionObject({noun})", "cyan"))
    apps = getItems("apps")
    for app in apps["items"]:
        if not appID or app["id"] == appID:
            time.sleep(2)
            print(colored(f"    └──> {app['name']} app initiating {noun}", "yellow"))
            helpers.run(
                f"./toolkit.py -f create {noun} -b {app['id']} "
                + f"{app['name']}-smoke-{time.strftime('%Y%m%d%H%M')}"
            )


def waitForCompletion(noun):
    """Lists {noun} and ensures everything is in a running state"""
    print(colored(f"──> waitForCompletion({noun})", "cyan"))
    nounFailures = []
    complete = False
    while not complete:
        complete = True
        print(colored(f"    └──> sleeping for 60 seconds for {noun} completion", "yellow"))
        time.sleep(60)
        items = getItems(noun)
        for item in items["items"]:
            if "smoke" in item["name"]:
                if (
                    item["state"] == "pending"
                    or item["state"] == "running"
                    or item["state"] == "discovering"
                ):
                    print(colored(f"    └──> {item['name']} in {item['state']} state", "yellow"))
                    complete = False
                elif item["state"] == "failed":
                    print(colored(f"    └──> ERROR: {item['name']} failed", "red"))
                    complete = False
                    print(colored(f"    └──> {item['name']} {noun[:-1]} being destroyed", "yellow"))
                    helpers.run(
                        f"./toolkit.py -f destroy {noun[:-1]} {item['appID']} {item['id']}",
                        ignoreErrors=True,
                    )
                    if item["id"] not in nounFailures:
                        createProtectionObject(noun[:-1], item["appID"])
                        nounFailures.append(item["id"])
                else:
                    print(colored(f"    └──> {item['name']} {item['state']}", "blue"))


def createUser(email, constraint):
    """Creates a 'member' user with namespace constraints"""
    print(colored(f"──> createUser()", "cyan"))
    namespaces = getItems("namespaces")
    for namespace in namespaces["items"]:
        if namespace["name"] == constraint:
            print(
                colored(f"    └──> {email} with '{constraint}' constraint being created", "yellow")
            )
            helpers.run(
                f"./toolkit.py -f create user {email} member -f Michael -l Haigh"
                + f" -n {namespace['id']}"
            )


def destroyUser(email):
    """Destroys a user based on email"""
    print(colored(f"──> destroyUser()", "cyan"))
    users = getItems("users")
    for user in users["items"]:
        if user["email"] == email:
            print(colored(f"    └──> {email} user being destroyed", "yellow"))
            helpers.run(f"./toolkit.py -f destroy user {user['id']}")


def createScripts(scriptPaths):
    """Creates scripts based on the passed script paths"""
    print(colored(f"──> createScripts()", "cyan"))
    for scriptPath in scriptPaths:
        scriptName = scriptPath.split("/")[2] + "-smoke"
        print(colored(f"    └──> {scriptName} being created", "yellow"))
        helpers.run(
            f"./toolkit.py -f create script {scriptName} {os.path.expanduser(scriptPath)}"
            + " -d smokeTest-automated-script"
        )


def createHooks():
    """Creates execution hooks for the passed apps"""
    print(colored(f"──> createHooks()", "cyan"))
    hookCreated = False
    apps = getItems("apps")
    scripts = getItems("scripts")
    for app in apps["items"]:
        appAssets = getItems(f"assets {app['id']}")
        for appAsset in appAssets["items"]:
            if appAsset["assetType"] == "Pod":
                for label in appAsset["labels"]:
                    for script in scripts["items"]:
                        if "smoke" in script["name"].lower():
                            for name in script["name"].split("-"):
                                if name.lower() in label["value"].lower() and not hookCreated:
                                    print(
                                        colored(
                                            f"    └──> {app['name']} execution hook being"
                                            + f" created based on {script['name']}",
                                            "yellow",
                                        )
                                    )
                                    helpers.run(
                                        f"./toolkit.py -f create hook {app['id']} {app['name']}-smoke"
                                        + f"-hook {script['id']} -o pre-snapshot -a pre"
                                    )
                                    hookCreated = True
        hookCreated = False


def cloneApp(appName):
    """Clones an app {appName} from cluster1 to cluster2"""
    print(colored(f"──> cloneApp({appName})", "cyan"))
    apps = getItems("apps")
    clusters = getItems("clusters")
    backups = getItems("backups")
    for app in apps["items"]:
        if appName == app["name"]:
            for cluster in clusters["items"]:
                if cluster["name"] == "uscentral1-cluster":
                    for backup in backups["items"]:
                        if app["id"] == backup["appID"] and "smoke" in backup["name"]:
                            print(colored(f"    └──> {appName} being cloned", "yellow"))
                            helpers.run(
                                f"./toolkit.py -f clone -b --cloneAppName "
                                + f"{appName}-clone-{time.strftime('%Y%m%d%H%M')} --cloneNamespace "
                                + f"{appName}-clonens-{time.strftime('%Y%m%d%H%M')} "
                                + f"--clusterID {cluster['id']} --backupID {backup['id']}"
                            )
                            return True


def restoreApp(appName):
    """Restores an app {appName} from a snapshot"""
    print(colored(f"──> restoreApp({appName})", "cyan"))
    apps = getItems("apps")
    snapshots = getItems("snapshots")
    for app in apps["items"]:
        if appName == app["name"]:
            for snapshot in snapshots["items"]:
                if app["id"] == snapshot["appID"] and "smoke" in snapshot["name"]:
                    print(colored(f"    └──> {appName} being restored", "yellow"))
                    helpers.run(
                        f"./toolkit.py -f restore -b {app['id']} --snapshotID {snapshot['id']}"
                    )
                    return True


def checkAppStatus():
    """Checks the state of all managed apps"""
    print(colored("──> checkAppStatus()", "cyan"))
    allAppsRunning = False
    while not allAppsRunning:
        allAppsRunning = True
        print(colored(f"    └──> sleeping for 60 seconds for app state updates", "yellow"))
        time.sleep(60)
        apps = getItems("apps")
        for app in apps["items"]:
            if app["state"] == "ready":
                print(colored(f"    └──> {app['name']} in {app['state']} state", "blue"))
            elif app["state"] == "failed":
                print(colored(f"    └──> {app['name']} in {app['state']} state", "red"))
            else:
                allAppsRunning = False
                print(colored(f"    └──> {app['name']} in {app['state']} state", "yellow"))


def removeObjects(noun):
    """Destroys/unmanages all {noun}s on the system"""
    print(colored(f"──> removeObjects({noun})", "cyan"))
    if noun == "cluster":
        itemStr = noun + "s -u"
    else:
        itemStr = noun + "s"
    items = getItems(itemStr)
    # "scripts" are a special case where we don't want to destroy all of them
    scriptBreak = False
    while len(items["items"]) > 0 and not scriptBreak:
        if noun == "script":
            scriptBreak = True
        for item in items["items"]:
            sleepTimer = 5
            if noun == "snapshot" or noun == "backup" or noun == "hook":
                print(colored(f"    └──> {item['name']} {noun} being destroyed", "yellow"))
                helpers.run(
                    f"./toolkit.py -f destroy {noun} {item['appID']} {item['id']}",
                    ignoreErrors=True,
                )
                if noun == "snapshot" or noun == "backup":
                    sleepTimer = 60
            elif noun == "app" or noun == "cluster":
                print(colored(f"    └──> {item['name']} {noun} being unmanaged", "yellow"))
                helpers.run(f"./toolkit.py -f unmanage {noun} {item['id']}", ignoreErrors=True)
                sleepTimer = 10
            elif noun == "script" and "smoke" in item["name"].lower():
                scriptBreak = False
                print(colored(f"    └──> {item['name']} {noun} being destroyed", "yellow"))
                helpers.run(f"./toolkit.py -f destroy {noun} {item['id']}", ignoreErrors=True)
        if not scriptBreak:
            print(
                colored(f"    └──> sleeping for {sleepTimer} seconds for {noun} removal", "yellow")
            )
            time.sleep(sleepTimer)
            items = getItems(itemStr)
    print(colored(f"    └──> {noun}s all removed", "blue"))


def destroyKubernetesApps(apps):
    """Destroys all Kubernetes apps on all clusters in the kubectl config AND Astra"""
    print(colored("──> destroyKubernetesApps()", "cyan"))
    clusters = getItems("clusters")
    contexts, _ = kubernetes.config.list_kube_config_contexts()
    # Loop through clusters and contexts, find matches and open api_client
    for cluster in clusters["items"]:
        for context in contexts:
            if cluster["name"] in context["name"]:
                client = kubernetes.client.CoreV1Api(
                    api_client=kubernetes.config.new_client_from_config(context=context["name"])
                )
                try:
                    namespaceResp = client.list_namespace(
                        _preload_content=False, _request_timeout=5
                    )
                    namespaces = json.loads(namespaceResp.data)
                    for namespace in namespaces["items"]:
                        for app in apps:
                            if app in namespace["metadata"]["name"]:
                                print(
                                    colored(
                                        f"    └──> {namespace['metadata']['name']} being "
                                        + "destroyed",
                                        "yellow",
                                    )
                                )
                                client.delete_namespace(namespace["metadata"]["name"])
                except kubernetes.client.rest.ApiException as e:
                    print("Exception when calling CoreV1Api: %s\n" % e)


if __name__ == "__main__":
    """This is an idempotent smoke test which requires the following configuration:
     - at least 2 kubernetes clusters eligible to be managed by Astra Control
     - those same clusters available in the kubeconfig context

    It carries out the following tasks:
     - manages all unmanaged clusters
     - waits for all trident pods to go into a running state
     - deploys an application "manually" with helm, then manages that app
     - deploys an application via the toolkit deploy command
     - creates a snapshot for all deployed apps
     - creates a backup for all deployed apps
     - clones an app from its original cluster to a new cluster via a backup
     - restores an app via a snapshot
     - monitors the app status of the cloned and restored app
     - destroys all snapshots
     - destroys all backups
     - unmanages all apps
     - deletes the non-default kubernetes namespaces
     - unmanages all clusters"""
    # self.headers["ForceDelete"] = "true"

    apps = ["cassandra", "wordpress"]
    install = [
        "helm install -n cassandra cassandra bitnami/cassandra",
        "./toolkit.py -f deploy -n wordpress wordpress bitnami/wordpress",
    ]
    scripts = [
        "~/Verda/Cassandra/cassandra-snap-hooks.sh",
        "~/Verda/Mariadb-MySQL/mariadb_mysql.sh",
    ]
    userEmail = "mhaigh@netapp.com"

    # clusterManagement()
    """deployApp(apps[0], install[0])
    deployApp(apps[1], install[1])
    appManagement(apps)
    createUser(userEmail, apps[0])
    createScripts(scripts)
    createHooks()
    createProtectionObject("snapshot")
    waitForCompletion("snapshots")
    createProtectionObject("backup")
    waitForCompletion("backups")
    cloneApp(apps[0])
    restoreApp(apps[1])
    checkAppStatus()
    destroyUser(userEmail)
    removeObjects("hook")
    removeObjects("script")"""
    removeObjects("snapshot")
    removeObjects("backup")
    removeObjects("app")
    destroyKubernetesApps(apps)
    # removeObjects("cluster")"""
