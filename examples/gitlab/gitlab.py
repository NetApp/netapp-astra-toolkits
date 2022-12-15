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

# GLOBAL VARIABLES - MODIFY FOR YOUR ENVIRONMENT
GCP_REGION = "us-east4"  # Region to deploy the resources in
GCP_ZONE = "us-east4-b"  # Zone to deploy the resources in
GKE_NETWORK_NAME = "gke-prod-network"  # GKE cluster network name, needed for SQL peering
GITLAB_DOMAIN = "astrademo.net"  # The gitlab domain name
EMAIL = "mhaigh@netapp.com"  # Email used for certmanager
APP_NAME = "gitlab"  # The namespace name, helm deployment name, and astra app name

import json
import kubernetes
import sys
import time
import yaml

# A bit of a hack to support both git repo and actoolkit python package use cases
try:
    # If these imports succeed, it's due to the actoolkit package being installed
    import astraSDK
    import tkHelpers
except ModuleNotFoundError:
    # If actoolkit isn't installed, then we're working within the git repo
    # Add the repo root dir to sys.path and set it as __package__
    # For more info on __package__, see https://peps.python.org/pep-0366/
    sys.path.append(sys.path[0].split("/examples")[0])
    __package__ = "netapp-astra-toolkits"
    import astraSDK
    import tkHelpers


def getGcpProject():
    """Get GCP project based on gcloud settings"""
    return tkHelpers.run("gcloud config get-value project", captureOutput=True).decode().strip()


def getSqlInstance(ip):
    """Returns the postgres SQL instance associated with GitLab based on IP address"""
    sqlInstances = json.loads(
        tkHelpers.run("gcloud sql instances list --format=json", captureOutput=True).decode()
    )
    for instance in sqlInstances:
        if instance["ipAddresses"][0]["ipAddress"] == ip:
            return instance


def getRedisInstance(ip):
    """Returns the redis instance associated with GitLab based on IP address"""
    redisInstances = json.loads(
        tkHelpers.run(
            f"gcloud redis instances list --region={GCP_REGION} --format=json", captureOutput=True
        ).decode()
    )
    for instance in redisInstances:
        if instance["host"] == ip:
            return instance


def getBucketNames(valuesDict):
    """Returns a list of all bucket names based on the 'bucket' and 'tmpBucket' keys in a dict"""
    for key, value in valuesDict.items():
        if isinstance(value, dict):
            yield from getBucketNames(value)
        elif key == "bucket" or key == "tmpBucket":
            yield value


def getAppDict():
    """Get the appDict based on APP_NAME global variable and current kubeconfig context"""
    _, context = kubernetes.config.list_kube_config_contexts()
    clusterDict = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
    for cluster in clusterDict["items"]:
        if cluster["name"] in context["context"]["cluster"]:
            apps = astraSDK.apps.getApps().main(cluster=cluster["id"])
            for app in apps["items"]:
                if app["name"] == APP_NAME:
                    return app


def destroyKubernetesResources():
    """Destroy the Kubernetes resources via delete namespace"""
    tkHelpers.run(f"kubectl delete namespace {APP_NAME}", ignoreErrors=True)


def destroyGcpResources():
    """Destroy Cloud SQL, Redis, Buckets, and storage service account"""

    # Read in values and storage service account files to gather resource names for cleanup
    with open("gitlab-values.yaml", encoding="utf8") as f:
        valuesDict = yaml.load(f.read().rstrip(), Loader=yaml.SafeLoader)
    with open("storage.config", encoding="utf8") as f:
        saDict = json.loads(f.read().rstrip())

    # Get SQL, Redis, and Bucket info from data stored in valuesDict
    sqlInstance = getSqlInstance(valuesDict["global"]["psql"]["host"])
    redisInstance = getRedisInstance(valuesDict["global"]["redis"]["host"])
    buckets = list(getBucketNames(valuesDict))

    # Delete the cloud resources
    if sqlInstance:
        tkHelpers.run(f"gcloud -q sql instances delete {sqlInstance['name']}", ignoreErrors=True)
    if redisInstance:
        tkHelpers.run(
            f"gcloud -q redis instances delete {redisInstance['name'].split('/')[-1]} "
            f"--region={GCP_REGION}",
            ignoreErrors=True,
        )
    tkHelpers.run(
        f"gcloud -q iam service-accounts delete {saDict['client_email']}", ignoreErrors=True
    )
    for bucket in buckets:
        if tkHelpers.run(f"gcloud storage ls gs://{bucket}/", ignoreErrors=True) == 0:
            tkHelpers.run(
                f"gcloud storage rm --recursive gs://{bucket}/",
                ignoreErrors=True,
            )


def destroyAstraResources():
    """Delete all backups/snapshots of our APP_NAME app, then unmanage the app"""
    print("Cleaning up Astra Control resources...")
    app = getAppDict()
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


def destroy():
    """Destroy Astra (snapshots, backups, app) and GCP (sql, redis, buckets, SA) resources"""
    destroyAstraResources()
    destroyGcpResources()
    # TODO: Delete files
    destroyKubernetesResources()


if __name__ == "__main__":
    """Script should be run as 'python3 gitlab.py <arg>', with arg == deploy or destroy"""
    if len(sys.argv) < 2:
        print("Error: must specify 'deploy' or 'destroy' argument")
        sys.exit(1)
    elif sys.argv[1].lower() == "deploy":
        pass
    elif sys.argv[1].lower() == "destroy":
        destroy()
    else:
        print("Error: must specify 'deploy' or 'destroy' argument")
        sys.exit(1)
