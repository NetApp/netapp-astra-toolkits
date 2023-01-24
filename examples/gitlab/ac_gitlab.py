#!/usr/bin/env python3
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

import json
import kubernetes
import subprocess
import sys
import time
import yaml
from datetime import datetime, timedelta
from secrets import token_urlsafe
from tabulate import tabulate
from termcolor import colored
from base64 import b64encode, b64decode

import gcpClasses

# A bit of a hack to support both git repo and actoolkit python package use cases
try:
    # If this import succeeds, it's due to the actoolkit package being installed
    import astraSDK
except ModuleNotFoundError:
    # If actoolkit isn't installed, then we're working within the git repo
    # Add the repo root dir to sys.path and set it as __package__
    # For more info on __package__, see https://peps.python.org/pep-0366/
    sys.path.append(sys.path[0].split("/examples")[0])
    __package__ = "netapp-astra-toolkits"
    import astraSDK


def run(command, captureOutput=False, ignoreErrors=False):
    """Run an arbitrary shell command.
    If ignore_errors=False raise SystemExit exception if the commands returns != 0 (failure).
    If ignore_errors=True, return the shell return code if it is != 0.
    If the shell return code is 0 (success) either return True or the contents of stdout,
    depending on whether capture_output is set to True or False"""
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


def getGcpProject():
    """Get GCP project based on gcloud settings"""
    return run("gcloud config get-value project", captureOutput=True).decode().strip()


###########################################################################################
#                      GLOBAL VARIABLES - MODIFY FOR YOUR ENVIRONMENT                     #
###########################################################################################
APP_NAME = "gitlab"  # To be created namespace, helm name, astra app, gcp resources prepend
DB_PASSWORD = token_urlsafe(13)  # Optionally change random password to your desired value
GITALY_AUTH = token_urlsafe(13)  # Optionally change random password to your desired value
GITLAB_SHELL = token_urlsafe(13)  # Optionally change random password to your desired value
EMAIL = "mhaigh@netapp.com"  # Change to your email, used for certmanager
GCP_NETWORK_NAME = "gke-uscentral1-network"  # Existing network name, must be GKE's network
GCP_PROJECT = getGcpProject()  # Uses gcloud config value
GCP_REGION = "us-central1"  # Region to deploy the resources in, must be GKE's region
GCP_ZONE = "us-central1-b"  # Zone to deploy the resources in
GITLAB_DOMAIN = "astrademo.net"  # The existing domain name, DNS must be managed by GCP
GITLAB_DNS_ZONE = "astrademo-net"  # The existing DNS zone name, DNS must be managed by GCP
###########################################################################################
#                      GLOBAL VARIABLES - MODIFY FOR YOUR ENVIRONMENT                     #
###########################################################################################


def createYamlOnDisk(filename, inpt):
    """Takes in a dict or str, converts to yaml, writes filename.yaml to disk"""
    print(f"Creating {filename}")
    with open(filename, "w") as f:
        f.write(yaml.dump(inpt)) if type(inpt) is dict else f.write(inpt)


def getBucketNames(valuesDict):
    """Returns a generator of all names based on the 'bucket' and 'tmpBucket' keys in a dict"""
    for key, value in valuesDict.items():
        if isinstance(value, dict):
            yield from getBucketNames(value)
        elif key == "bucket" or key == "tmpBucket":
            yield value


def getAppDict(app_name):
    """Get the appDict based on app_name variable and current kubeconfig context"""
    _, context = kubernetes.config.list_kube_config_contexts()
    clusterDict = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
    for cluster in clusterDict["items"]:
        if cluster["name"] in context["context"]["cluster"]:
            apps = astraSDK.apps.getApps().main(cluster=cluster["id"])
            for app in apps["items"]:
                if app["name"] == app_name:
                    return app


def assignOrAppend(bKey, abKey, backups, allBackups):
    """For a backups dictionary, either assign the matching 'tmpstmp' backup to the existing
    allBackups["items"] dictionary, or append in the event there is not already a match"""
    for backup in backups:
        append = True
        for item in allBackups["items"]:
            if backup.get(bKey):
                if item.get("tmstmp") == backup[bKey].split("-")[-1]:
                    item[abKey] = backup
                    append = False
            else:  # if the backup key doesn't exist in the backup dict, we do not want to append
                append = False
        if append and backup.get(bKey):
            allBackups["items"].append({"tmstmp": backup[bKey].split("-")[-1], abKey: backup})


def printBackups(backups):
    """Given a dictionary of all the backups, print out their state in a table"""
    tabHeader = [
        colored("Timestamp", "blue"),
        colored("Gitaly OS Disk Backup", "blue"),
        colored("Gitaly Git Disk Backup", "blue"),
        colored("PostgreSQL Backup", "blue"),
        colored("Redis Backup", "blue"),
        colored("Astra App Backup", "blue"),
    ]
    tabData = []
    for backup in backups["items"]:
        tabData.append(
            [
                colored(backup["tmstmp"], "blue"),
                backup["osBackup"]["status"]
                if backup.get("osBackup")
                else colored("No backup found", "yellow"),
                backup["dataBackup"]["status"]
                if backup.get("dataBackup")
                else colored("No backup found", "yellow"),
                backup["dbBackup"]["status"]
                if backup.get("dbBackup")
                else colored("No backup found", "yellow"),
                backup["redisBackup"]["response"]["state"]
                if (backup.get("redisBackup") and backup["redisBackup"].get("response"))
                else colored("No backup found", "yellow"),
                backup["appBackup"]["state"]
                if backup.get("appBackup")
                else colored("No backup found", "yellow"),
            ]
        )
    print(tabulate(tabData, tabHeader, tablefmt="grid"))


def organizeBackups(osBackups, dataBackups, dbBackups, redisBackups, appBackups):
    """Given five lists of varying order, create a single dictionary of format:
    {"items": [
                    {
                        "tmstmp": "202301111306",
                        "osBackup": osBackupDict,
                        "dataBackup": dataBackupDict,
                        "dbBackup": dbBackupDict,
                        "redisBackup": redisBackupDict,
                        "appBackup": appBackupDict,
                    }
              ]
    }"""
    allBackups = {"items": []}
    assignOrAppend("name", "osBackup", osBackups, allBackups)
    assignOrAppend("name", "dataBackup", dataBackups, allBackups)
    assignOrAppend("description", "dbBackup", dbBackups, allBackups)
    assignOrAppend("name", "appBackup", appBackups, allBackups)
    assignOrAppend("backupName", "redisBackup", redisBackups, allBackups)
    return {"items": sorted(allBackups["items"], key=lambda i: i["tmstmp"])}


def destroyBackup(valuesDict, tmstmp):
    """Destroy the backups of the services based on the provided 'tmpstmp'"""
    gcpClasses.ComputeEngineDisk(  # os disk
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
    ).deleteBackup(tmstmp)
    gcpClasses.ComputeEngineDisk(  # data/git disk
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
    ).deleteBackup(tmstmp)
    gcpClasses.CloudPostgreSQL(APP_NAME).deleteBackup(tmstmp)
    gcpClasses.CloudRedis(APP_NAME, GCP_REGION).deleteBackup(
        valuesDict["global"]["appConfig"]["backups"]["bucket"],
        tmstmp,
    )
    if app := getAppDict(APP_NAME):
        for backup in astraSDK.backups.getBackups().main(appFilter=app["id"])["items"]:
            if tmstmp in backup["name"]:
                astraSDK.backups.destroyBackup(quiet=False).main(app["id"], backup["id"])
                print(f"Astra backup {backup['id']} of app {app['id']} destroyd")


def listBackups(valuesDict):
    """Lists the backups of the main objects (astra app, psql, redis, gitaly disks)"""
    printBackups(
        organizeBackups(
            gcpClasses.ComputeEngineDisk(  # os disk
                valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
            ).getBackups(),
            gcpClasses.ComputeEngineDisk(  # data/git disk
                valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
            ).getBackups(),
            gcpClasses.CloudPostgreSQL(APP_NAME).getBackups(),
            gcpClasses.CloudRedis(APP_NAME, GCP_REGION).getBackups(
                valuesDict["global"]["appConfig"]["backups"]["bucket"]
            ),
            astraSDK.backups.getBackups().main(appFilter=app["id"])["items"]
            if (app := getAppDict(APP_NAME))
            else [],
        )
    )


def validateAndGetBackup(timestamp, backups):
    """Validates that a given timestamp has valid backups for all services"""
    for backup in backups["items"]:
        if backup["tmstmp"] == timestamp:
            if (
                backup.get("osBackup")
                and backup["osBackup"]["status"] == "READY"
                and backup.get("dataBackup")
                and backup["dataBackup"]["status"] == "READY"
                and backup.get("dbBackup")
                and backup["dbBackup"]["status"] == "SUCCESSFUL"
                and backup.get("redisBackup")
                and backup["redisBackup"].get("response")
                and backup["redisBackup"]["response"]["state"] == "READY"
                and backup.get("appBackup")
                and backup["appBackup"]["state"] == "completed"
            ):
                return backup
            else:
                print(f"Error: not all components of backup timestamp {timestamp} in valid state:")
                printBackups(backups)
                sys.exit(1)
    print(f"Error: No backup of timestamp {timestamp} found:")
    printBackups(backups)
    sys.exit(1)


def restore(valuesDict, timestamp):
    """In-place restore for GitLab to a backup from 'timestamp'"""

    # Instantiate the objects
    osDisk = gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
    )
    dataDisk = gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
    )
    db = gcpClasses.CloudPostgreSQL(APP_NAME)
    redis = gcpClasses.CloudRedis(APP_NAME, GCP_REGION)
    app = getAppDict(APP_NAME)
    gitaly = gcpClasses.ComputeEngineVM(APP_NAME)

    # Ensure timestamp has valid backups for all instantiated objects, and get backup info
    backup = validateAndGetBackup(
        timestamp,
        organizeBackups(
            osDisk.getBackups(),
            dataDisk.getBackups(),
            db.getBackups(),
            redis.getBackups(valuesDict["global"]["appConfig"]["backups"]["bucket"]),
            astraSDK.backups.getBackups().main(appFilter=app["id"])["items"],
        ),
    )

    # Restore the backups
    if astraSDK.apps.restoreApp(quiet=False).main(app["id"], backupID=backup["appBackup"]["id"]):
        print(f"Astra app {app['name']} restore successfully initiated")
    db.restoreFromBackup(backup["dbBackup"]["id"])
    redis.restoreFromBackup(backup["redisBackup"]["gcsLocation"])
    gitaly.shutdownAndDetach()
    osDisk.deleteDisk()
    dataDisk.deleteDisk()
    osDisk.createDiskFromBackup(backup["osBackup"]["name"], GCP_ZONE)
    dataDisk.createDiskFromBackup(backup["dataBackup"]["name"], GCP_ZONE)
    gitaly.attachAndBoot()

    # Wait for completion
    print(f"Waiting for {APP_NAME} application to finish restoration...", end="")
    sys.stdout.flush()
    while True:
        time.sleep(60)
        db.setProperties()
        if db.properties["state"] == "MAINTENANCE":
            print(".", end="")
            sys.stdout.flush()
        elif db.properties["state"] == "RUNNABLE":
            print("success!")
            break
        else:
            print(f"Error restoring {APP_NAME} application")
            sys.exit(1)
    print(f"\n{APP_NAME} application successfully restored")


def backup(valuesDict):
    """Backs up GCP and Astra Kubernetes resources"""
    tmstmp = datetime.utcnow().strftime("%Y%m%d%H%M")
    # Instantiate the objects
    osDisk = gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
    )
    dataDisk = gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
    )
    db = gcpClasses.CloudPostgreSQL(APP_NAME)
    redis = gcpClasses.CloudRedis(APP_NAME, GCP_REGION)
    app = getAppDict(APP_NAME)

    # Execute async/background backups
    astraSDK.backups.takeBackup(quiet=False).main(app["id"], f"{APP_NAME}-{tmstmp}")
    redis.createBackup(valuesDict["global"]["appConfig"]["backups"]["bucket"], tmstmp)
    db.createBackup(tmstmp)
    dataDisk.createBackup(tmstmp)
    osDisk.createBackup(tmstmp)


def destroyAstraResources():
    """Delete all backups/snapshots of our APP_NAME app, then unmanage the app"""
    print("Cleaning up Astra Control resources...")
    app = getAppDict(APP_NAME)
    if app:
        appBackups = astraSDK.backups.getBackups().main(appFilter=app["id"])
        appSnapshots = astraSDK.snapshots.getSnaps().main(appFilter=app["id"])
        while len(appBackups["items"]) > 0 or len(appSnapshots["items"]) > 0:
            for backup in appBackups["items"]:
                astraSDK.backups.destroyBackup(quiet=False).main(app["id"], backup["id"])
                time.sleep(1)
            for snapshot in appSnapshots["items"]:
                astraSDK.snapshots.destroySnapshot(quiet=False).main(app["id"], snapshot["id"])
                time.sleep(1)
            print("Sleeping for 60 seconds for backup/snapshot cleanup...")
            time.sleep(60)
            appBackups = astraSDK.backups.getBackups().main(appFilter=app["id"])
            appSnapshots = astraSDK.snapshots.getSnaps().main(appFilter=app["id"])
        astraSDK.apps.unmanageApp(quiet=False).main(app["id"])
    else:
        print("App already unmanaged, nothing to do.")


def destroyGcpResources(valuesDict):
    """Destroy backups, Cloud SQL, Redis, Buckets, and storage service account"""
    for backup in organizeBackups(
        gcpClasses.ComputeEngineDisk(  # os disk
            valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
        ).getBackups(),
        gcpClasses.ComputeEngineDisk(  # data/git disk
            valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
        ).getBackups(),
        gcpClasses.CloudPostgreSQL(APP_NAME).getBackups(),
        gcpClasses.CloudRedis(APP_NAME, GCP_REGION).getBackups(
            valuesDict["global"]["appConfig"]["backups"]["bucket"]
        ),
        [],
    )["items"]:
        destroyBackup(valuesDict, backup["tmstmp"])
    gcpClasses.RecordSet(
        GCP_REGION,
        valuesDict["global"]["gitaly"]["external"][0]["hostname"],
        GITLAB_DNS_ZONE,
        APP_NAME,
    ).deleteRecordSet()
    gcpClasses.ComputeEngineVM(APP_NAME).deleteInstance()
    gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
    ).deleteDisk()
    gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
    ).deleteDisk()
    gcpClasses.CloudPostgreSQL(APP_NAME).deleteInstance()
    gcpClasses.CloudRedis(APP_NAME, GCP_REGION).deleteInstance()
    gcpClasses.ServiceAccount(APP_NAME, GCP_PROJECT).deleteServiceAccount()
    gcpClasses.ObjectBuckets(
        APP_NAME, GCP_PROJECT, list(getBucketNames(valuesDict))
    ).deleteBuckets()
    gcpClasses.VpcPeering(GCP_NETWORK_NAME, GCP_PROJECT).deletePeering()
    gcpClasses.RecordSet(
        GCP_REGION, f"*.{GITLAB_DOMAIN}", GITLAB_DNS_ZONE, APP_NAME
    ).deleteRecordSet()
    gcpClasses.ExternalDnsAddress(APP_NAME, GCP_REGION).deleteAddress()


def destroyKubernetesResources():
    """Destroy the Kubernetes resources and values file"""
    run(f"kubectl delete namespace {APP_NAME}", ignoreErrors=True)
    print(f"Removing {APP_NAME}-values.yaml")
    run(f"rm {APP_NAME}-values.yaml", ignoreErrors=True)


def destroy(valuesDict):
    """Destroy Astra (snapshots, backups, app), GCP (gitaly VM, sql, redis, buckets, SA),
    and Kubernetes resources"""
    destroyAstraResources()
    destroyGcpResources(valuesDict)
    destroyKubernetesResources()
    print(f"\nSuccess! All resources destroyed.")


def getWebPassword():
    """Returns the 'root' user password for logging into gitlab via the browser"""
    return b64decode(
        json.loads(
            run(
                f"kubectl get secret {APP_NAME}-gitlab-initial-root-password -o json",
                captureOutput=True,
            )
        )["data"]["password"]
    ).decode()


def gcpDeploy(valuesDict, cloudinit):
    """Deploy the GCP hosted resources (Postgres, Redis, Buckets, SA)"""

    # Create OS and data disks for Gitaly if not already present
    osDisk = gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[0], APP_NAME
    )
    if not osDisk.properties:
        osDisk.createDisk(
            "pd-standard",
            "10GB",
            GCP_ZONE,
            imageFamily="ubuntu-2204-lts",
            imageProject="ubuntu-os-cloud",
        )
    dataDisk = gcpClasses.ComputeEngineDisk(
        valuesDict["global"]["gitaly"]["external"][0]["hostname"].split(".")[1], APP_NAME
    )
    if not dataDisk.properties:
        dataDisk.createDisk(
            "pd-ssd",
            "100GB",
            GCP_ZONE,
        )

    # Create a VM instance for Gitaly if not already present
    gitaly = gcpClasses.ComputeEngineVM(APP_NAME)
    if not gitaly.properties:
        gitaly.createInstance(
            "n2-standard-4",
            osDisk.name,
            [dataDisk.name],
            GCP_NETWORK_NAME,
            GCP_ZONE,
            GCP_PROJECT,
            GITALY_AUTH,
            GITLAB_SHELL,
            cloudinit,
        )
        gitaly.createSecretFile()

    # Create a DNS record set so other services can access the Gitaly VM
    grs = gcpClasses.RecordSet(
        GCP_REGION,
        valuesDict["global"]["gitaly"]["external"][0]["hostname"],
        GITLAB_DNS_ZONE,
        APP_NAME,
    )
    if not grs.properties:
        grs.createRecordSet(gitaly.properties["networkInterfaces"][0]["networkIP"])

    # Create an external IP for Gitlab access if not already present
    extIP = gcpClasses.ExternalDnsAddress(APP_NAME, GCP_REGION)
    if not extIP.properties:
        extIP.createExternalAddress()
    valuesDict["global"]["hosts"]["externalIP"] = extIP.properties["address"]

    # Create a wildcard DNS record set to point at the external IP if not already present
    wrs = gcpClasses.RecordSet(GCP_REGION, f"*.{GITLAB_DOMAIN}", GITLAB_DNS_ZONE, APP_NAME)
    if not wrs.properties:
        wrs.createRecordSet(extIP.properties["address"])

    # Create a VPC peering between the GKE network and Cloud SQL if not already present
    vp = gcpClasses.VpcPeering(GCP_NETWORK_NAME, GCP_PROJECT)
    if not vp.properties:
        vp.createPeering()

    # Create a PostgreSQL instance if not already present
    db = gcpClasses.CloudPostgreSQL(APP_NAME)
    if not db.properties:
        db.createInstance(
            GCP_NETWORK_NAME, GCP_ZONE, GCP_REGION, GCP_PROJECT, "2", "8GiB", DB_PASSWORD
        )
        db.createUser("gitlab")
        db.createDB("gitlabhq_production")
        db.createSecretFile()
    valuesDict["global"]["psql"]["host"] = db.properties["ipAddresses"][0]["ipAddress"]

    # Create a service account for cloud storage if not already present
    sa = gcpClasses.ServiceAccount(APP_NAME, GCP_PROJECT)
    if not sa.properties:
        sa.createServiceAccount()
        sa.createRegistrySecret()
        sa.createRailsStorageSecret()

    # Create cloud storage buckets for all buckets listed in the values Dict
    gcpClasses.ObjectBuckets(
        APP_NAME, GCP_PROJECT, list(getBucketNames(valuesDict))
    ).createBuckets()

    # Create a Redis instance if not already present
    redis = gcpClasses.CloudRedis(APP_NAME, GCP_REGION)
    if not redis.properties:
        redis.createInstance(GCP_NETWORK_NAME, GCP_ZONE, GCP_PROJECT, "4")
        redis.createSecretFile()
        redis.addBucketIamPolicy(valuesDict["global"]["appConfig"]["backups"]["bucket"])
    valuesDict["global"]["redis"]["host"] = redis.properties["host"]


def applyYamlSecrets():
    """Applies the previously created external yaml secret files"""
    for f in [
        f"{APP_NAME}-psql-secret.yaml",
        f"{APP_NAME}-redis-secret.yaml",
        f"{APP_NAME}-gitaly-secret.yaml",
        f"{APP_NAME}-shell-secret.yaml",
    ]:
        run(f"kubectl -n {APP_NAME} apply -f {f}")
    run(
        f"kubectl -n {APP_NAME} create secret generic registry-storage --from-file="
        f"config={APP_NAME}-registry-storage.yaml --from-file=gcs.json={APP_NAME}-storage.config"
    )
    run(
        f"kubectl -n {APP_NAME} create secret generic storage-config "
        f"--from-file=config={APP_NAME}-storage.config"
    )
    run(
        f"kubectl -n {APP_NAME} create secret generic object-storage "
        f"--from-file=connection={APP_NAME}-rails.yaml"
    )


def kubernetesDeploy(valuesDict):
    """Creates values file, creates the kubernetes namespace, adds/updates the helm repo,
    applies the external secrets, runs helm install command, and manages the Astra app"""

    createYamlOnDisk(f"{APP_NAME}-values.yaml", valuesDict)

    for ns in json.loads(run("kubectl get ns -o json", captureOutput=True))["items"]:
        if ns["metadata"]["name"] == APP_NAME:
            print(f"Namespace {APP_NAME} already exists!")
            sys.exit(1)
    run("helm repo add gitlab https://charts.gitlab.io")
    run("helm repo update")
    run(f"kubectl create namespace {APP_NAME}")
    run(f"kubectl config set-context --current --namespace={APP_NAME}")
    applyYamlSecrets()
    run(f"helm install {APP_NAME} gitlab/gitlab -f {APP_NAME}-values.yaml")

    ansObj = astraSDK.namespaces.getNamespaces()
    appID = ""
    while not appID:
        print("Waiting for Astra to discover the namespace")
        time.sleep(3)
        for ns in ansObj.main()["items"]:
            if (
                ns["name"] == APP_NAME
                and ns["namespaceState"] == "discovered"
                and (
                    datetime.utcnow()
                    - datetime.strptime(ns["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ")
                )
                < timedelta(minutes=10)
            ):
                print(f"Managing app: {ns['name']}")
                rc = astraSDK.apps.manageApp().main(ns["name"], ns["name"], ns["clusterID"])
                if rc:
                    print("App managed!")
                    appID = rc["id"]
                    break
                else:
                    print("Error managing app")
                    sys.exit(1)


def deploy(valuesDict, cloudinit):
    """Deploy GCP (sql, redis, buckets, SA) resources, and GitLab via Helm"""
    gcpDeploy(valuesDict, cloudinit)
    kubernetesDeploy(valuesDict)
    print(f"\nSuccess! Open your browser to https://gitlab.{GITLAB_DOMAIN} and log in with:")
    print(f"root / {getWebPassword()}")


if __name__ == "__main__":
    """Script should be run as 'python3 gitlab.py <arg>', with arg == deploy or destroy"""

    valuesDict = {
        "global": {
            "appConfig": {
                "artifacts": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-artifacts-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "backups": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-backup-storage",
                    "tmpBucket": f"{GCP_PROJECT}-{APP_NAME}-tmp-storage",
                },
                "dependencyProxy": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-dependencyproxy-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "externalDiffs": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-externaldiffs-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "lfs": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-lfs-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "packages": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-packages-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "pseudonymizer": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-pseudonymizer-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "terraformState": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-tfstate-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
                "uploads": {
                    "bucket": f"{GCP_PROJECT}-{APP_NAME}-uploads-storage",
                    "connection": {"secret": "object-storage", "key": "connection"},
                },
            },
            "gitaly": {
                "enabled": False,
                "external": [
                    {
                        "name": "default",
                        "hostname": f"node1.git.{GITLAB_DOMAIN}",
                    }
                ],
                "authToken": {"secret": f"{APP_NAME}-gitaly-token", "key": "token"},
            },
            "hosts": {"domain": GITLAB_DOMAIN},
            "minio": {"enabled": False},
            "psql": {
                "password": {
                    "secret": f"{APP_NAME}-postgresql-password",
                    "key": "postgres-password",
                },
            },
            "redis": {
                "password": {"secret": f"{APP_NAME}-redis-secret", "key": "redis-password"},
            },
            "registry": {"bucket": f"{GCP_PROJECT}-{APP_NAME}-registry-storage"},
            "shell": {
                "authToken": {"secret": f"{APP_NAME}-shell-token", "key": "token"},
            },
        },
        "certmanager-issuer": {"email": f"{EMAIL}"},
        "gitlab": {
            "toolbox": {
                "backups": {
                    "objectStorage": {
                        "backend": "gcs",
                        "config": {
                            "gcpProject": f"{GCP_PROJECT}",
                            "secret": "storage-config",
                            "key": "config",
                        },
                    }
                }
            }
        },
        "postgresql": {"install": False},
        "redis": {"install": False},
        "registry": {
            "storage": {"secret": "registry-storage", "key": "config", "extraKey": "gcs.json"}
        },
    }

    if len(sys.argv) < 2:
        print("Error: must specify 'backup', 'deploy', or 'destroy' argument")
        sys.exit(1)

    elif sys.argv[1].lower() == "deploy":
        # This isn't ideal for readability, but cloudinit relies on some yaml-specific features
        # that aren't available in JSON, so using a multiline strings rather than a dictionary
        gitlabrb = f"""gitaly['auth_token'] = '{GITALY_AUTH}'
gitlab_shell['secret_token'] = '{GITLAB_SHELL}'

postgresql['enable'] = false
redis['enable'] = false
puma['enable'] = false
sidekiq['enable'] = false
gitlab_workhorse['enable'] = false
prometheus['enable'] = false
alertmanager['enable'] = false
grafana['enable'] = false
gitlab_exporter['enable'] = false
gitlab_kas['enable'] = false
nginx['enable'] = false

gitlab_rails['auto_migrate'] = false
gitlab_rails['internal_api_url'] = 'https://gitlab.{GITLAB_DOMAIN}'

gitaly['enable'] = true

gitaly['listen_addr'] = '0.0.0.0:8075'
gitaly['prometheus_listen_addr'] = '0.0.0.0:9236'
node_exporter['listen_address'] = '0.0.0.0:9100'

git_data_dirs({{
  'default' => {{
    'path' => '/mnt/gitlab/git-data'
  }},
}})
"""
        cloudinit = f"""#cloud-config

bootcmd:
  - curl -fsSL "https://packages.gitlab.com/gitlab/gitlab-ee/gpgkey" \
    | gpg --dearmor > /etc/apt/trusted.gpg.d/gitlab_gitlab-ee.gpg

fs_setup:
 - filesystem: "ext4"
   device: "/dev/sdb"

mounts:
 - [ sdb, /mnt/gitlab, "auto", "discard,defaults,noatime,nofail", "0", "2"]

write_files:
 - encoding: b64
   content: {b64encode(gitlabrb.encode()).decode()}
   owner: root:root
   path: /etc/gitlab/gitlab.rb
   permissions: '0600'

package_update: true
package_upgrade: true

apt:
  preserve_sources_list: true
  sources:
    gitlab_gitlab-ee.list:
      source: "deb https://packages.gitlab.com/gitlab/gitlab-ee/ubuntu/ jammy main"

packages:
  - gitlab-ee

runcmd:
  - [gitlab-ctl, reconfigure]"""
        deploy(valuesDict, cloudinit)

    elif sys.argv[1].lower() == "destroy":
        destroy(valuesDict)

    elif sys.argv[1].lower() == "backup":
        if len(sys.argv) < 3:
            print(
                "Error: must specify 'backup create', 'backup destroy', or 'backup list' argument"
            )
            sys.exit(1)
        if sys.argv[2].lower() == "create":
            backup(valuesDict)
        elif sys.argv[2].lower() == "destroy":
            if len(sys.argv) < 4:
                print("Error: must specify 'backup destroy <timestamp>' argument")
                sys.exit(1)
            destroyBackup(valuesDict, sys.argv[3])
        elif sys.argv[2].lower() == "list":
            listBackups(valuesDict)
        else:
            print("Error: must specify 'backup create', or 'backup list' argument")
            sys.exit(1)

    elif sys.argv[1].lower() == "restore":
        if len(sys.argv) < 3:
            print("Error: must specify 'restore <timestamp>' argument")
            sys.exit(1)
        restore(valuesDict, sys.argv[2])

    else:
        print("Error: must specify 'backup', 'deploy', 'destroy', or 'restore' argument")
        sys.exit(1)
