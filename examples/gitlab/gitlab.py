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
import sys
import time
import yaml
from secrets import token_urlsafe
from base64 import b64encode

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


###########################################################################################
#                      GLOBAL VARIABLES - MODIFY FOR YOUR ENVIRONMENT                     #
###########################################################################################
APP_NAME = "gitlab"  # To be created namespace name, helm name, and astra app name
DB_PASSWORD = token_urlsafe(13)  # Optionally change random password to your desired value
EMAIL = "mhaigh@netapp.com"  # Email used for certmanager
GCP_NETWORK_NAME = "gke-prod-network"  # Existing network name, must be GKE's network
GCP_PROJECT = getGcpProject()  # Uses gcloud config value
GCP_REGION = "us-east4"  # Region to deploy the resources in
GCP_ZONE = "us-east4-b"  # Zone to deploy the resources in
GCS_SA_NAME = "gitlab-gcs"  # To be created google cloud storage service account name
GITLAB_DOMAIN = "astrademo.net"  # The existing domain name, DNS must be managed by GCP
GITLAB_DNS_ZONE = "astrademo-net"  # The existing DNS zone name, DNS must be managed by GCP
REDIS_INSTANCE_NAME = "gitlab-redis-demo"  # To be created name of the Redis instance
SQL_INSTANCE_NAME = "gitlab-psql-demo"  # To be created name of the PostgreSQL instance
###########################################################################################
#                      GLOBAL VARIABLES - MODIFY FOR YOUR ENVIRONMENT                     #
###########################################################################################


def getSqlInstance():
    """Returns a dict of the postgres SQL instance"""
    sqlInstances = json.loads(
        tkHelpers.run("gcloud sql instances list --format=json", captureOutput=True).decode()
    )
    for instance in sqlInstances:
        if instance["name"] == SQL_INSTANCE_NAME:
            return instance
    return None


def getRedisInstance():
    """Returns the redis instance associated with GitLab"""
    redisInstances = json.loads(
        tkHelpers.run(
            f"gcloud redis instances list --region={GCP_REGION} --format=json", captureOutput=True
        ).decode()
    )
    for instance in redisInstances:
        if instance["name"].split("/")[-1] == REDIS_INSTANCE_NAME:
            return instance
    return None


def getRedisAuthString():
    """Returns the Redis auth string"""
    return json.loads(
        tkHelpers.run(
            f"gcloud redis instances get-auth-string {REDIS_INSTANCE_NAME} --region={GCP_REGION} "
            "--format=json",
            captureOutput=True,
        ).decode()
    )["authString"]


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


def getExternalAddress():
    """Returns the gitlab external DNS IP address"""
    return json.loads(
        tkHelpers.run(
            f"gcloud compute addresses describe gitlab-external-ip --region {GCP_REGION} "
            f"--project {GCP_PROJECT} --format=json",
            captureOutput=True,
        ).decode()
    )["address"]


def createExternalAddress():
    """Creates an external IP address to set as the GitLab DNS IP"""
    tkHelpers.run(
        f"gcloud compute addresses create {APP_NAME}-external-ip --region {GCP_REGION} "
        f"--project {GCP_PROJECT}"
    )


def createRecordSet():
    """Creates a DNS record set based on the GitLab domain and DNS zone names"""
    tkHelpers.run(
        f"gcloud dns --project={GCP_PROJECT} record-sets create *.{GITLAB_DOMAIN}. "
        f"--zone={GITLAB_DNS_ZONE} --type=A --ttl=60 --rrdatas={getExternalAddress()}"
    )


def createPeeringAddress():
    """Creates an address range for VPC peering between the GKE cluster and Cloud SQL"""
    tkHelpers.run(
        f"gcloud compute addresses create google-managed-services-{GCP_NETWORK_NAME}"
        " --global --purpose=VPC_PEERING --prefix-length=20 "
        f"--network=projects/{GCP_PROJECT}/global/networks/{GCP_NETWORK_NAME}"
    )


def createVpcPeering():
    """Creates a VPC peering between the GKE cluster and Cloud SQL"""
    tkHelpers.run(
        "gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com "
        f"--ranges=google-managed-services-{GCP_NETWORK_NAME} --network={GCP_NETWORK_NAME} "
        f"--project={GCP_PROJECT}"
    )


def createCloudSQL():
    """Creates and configures a Google Cloud SQL Postgres Instance"""
    tkHelpers.run(
        f"gcloud sql instances create {APP_NAME}-psql-demo --database-version=POSTGRES_14 --cpu=2 "
        f"--memory=8GiB --zone={GCP_ZONE} --root-password={DB_PASSWORD} "
        f"--network=projects/{GCP_PROJECT}/global/networks/{GCP_NETWORK_NAME} --no-assign-ip"
    )
    tkHelpers.run(
        f"gcloud sql users create gitlab --instance={APP_NAME}-psql-demo --password={DB_PASSWORD}"
    )
    tkHelpers.run(
        f"gcloud sql databases create gitlabhq_production --instance={APP_NAME}-psql-demo"
    )


def createRedis():
    """Creates a Redis Instance"""
    tkHelpers.run(
        f"gcloud redis instances create {REDIS_INSTANCE_NAME} --region={GCP_REGION} "
        f"--zone={GCP_ZONE} --size=4 --tier=standard --persistence-mode=rdb "
        f"--rdb-snapshot-period=1h --connect-mode=private-service-access --enable-auth "
        f"--network=projects/{GCP_PROJECT}/global/networks/{GCP_NETWORK_NAME}"
    )


def createServiceAccount():
    """Creates a Cloud Storage Service Account for object storage"""
    tkHelpers.run(
        f"gcloud iam service-accounts create {GCS_SA_NAME} --display-name 'GitLabCloudStorage'"
    )
    tkHelpers.run(
        f"gcloud projects add-iam-policy-binding --role roles/storage.admin {GCP_PROJECT} "
        f"--member=serviceAccount:{GCS_SA_NAME}@{GCP_PROJECT}.iam.gserviceaccount.com"
    )
    tkHelpers.run(
        f"gcloud iam service-accounts keys create --iam-account {GCS_SA_NAME}@{GCP_PROJECT}"
        ".iam.gserviceaccount.com storage.config"
    )


def createBuckets():
    """Creates all of the object storage buckets"""
    bucketNames = [
        "registry-storage",
        "backup-storage",
        "tmp-storage",
        "artifacts-storage",
        "dependencyproxy-storage",
        "externaldiffs-storage",
        "lfs-storage",
        "packages-storage",
        "pseudonymizer-storage",
        "tfstate-storage",
        "uploads-storage",
        "",
    ]
    for bucket in bucketNames:
        tkHelpers.run(f"gcloud storage buckets create gs://{GCP_PROJECT}-{APP_NAME}-{bucket}")


def dictToYamlOnDisk(filename, d):
    """Takes in a dict 'd', converts to yaml, writes filename.yaml to disk"""
    with open(filename, "w") as f:
        f.write(yaml.dump(d))


def createPsqlSecretFile():
    """Creates a PostgreSQL secret dictionary, then writes yaml to disk"""
    dictToYamlOnDisk(
        f"{APP_NAME}-psql-secret.yaml",
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{APP_NAME}-postgresql-password",
                "namespace": APP_NAME,
                "labels": {"app": APP_NAME},
            },
            "type": "Opaque",
            "data": {"postgres-password": b64encode(DB_PASSWORD.encode()).decode()},
        },
    )


def createRedisSecretFile():
    """Creates a Redis secret dictionary, then writes yaml to disk"""
    dictToYamlOnDisk(
        f"{APP_NAME}-redis-secret.yaml",
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{APP_NAME}-redis-secret",
                "namespace": APP_NAME,
                "labels": {"app": APP_NAME},
            },
            "type": "Opaque",
            "data": {"redis-password": b64encode(getRedisAuthString().encode()).decode()},
        },
    )


def createRegistrySecret():
    """Creates a Object storage bucket secret for the Registry"""
    dictToYamlOnDisk(
        f"{APP_NAME}-registry-storage.yaml",
        {
            "gcs": {
                "bucket": f"{GCP_PROJECT}-registry-storage",
                "keyfile": "/etc/docker/registry/storage/gcs.json",
            }
        },
    )


def createRailsStorageSecret():
    """Creates a Rails Object Storage secret for all non-registry buckets"""
    with open("storage.config", encoding="utf8") as f:
        saStr = f.read().rstrip()
    dictToYamlOnDisk(
        f"{APP_NAME}-rails.yaml",
        {
            "provider": "Google",
            "google_project": "astracontroltoolkitdev",
            "google_json_key_string": saStr,
        },
    )


def createValuesYaml():
    """Creates a values file for input into helm install command"""
    dictToYamlOnDisk(
        f"{APP_NAME}-values.yaml",
        {
            "global": {
                "appConfig": {
                    "artifacts": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-artifacts-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "backups": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-backup-storage",
                        "tmpBucket": "{GCP_PROJECT}-{APP_NAME}-tmp-storage",
                    },
                    "dependencyProxy": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-dependencyproxy-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "externalDiffs": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-externaldiffs-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "lfs": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-lfs-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "packages": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-packages-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "pseudonymizer": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-pseudonymizer-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "terraformState": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-tfstate-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                    "uploads": {
                        "bucket": "{GCP_PROJECT}-{APP_NAME}-uploads-storage",
                        "connection": {"secret": "object-storage", "key": "connection"},
                    },
                },
                "hosts": {"domain": GITLAB_DOMAIN, "externalIP": getExternalAddress()},
                "ingress": {"configureCertmanager": False},
                "minio": {"enabled": False},
                "psql": {
                    "host": getSqlInstance()["ipAddresses"][0]["ipAddress"],
                    "password": {
                        "secret": "gitlab-postgresql-password",
                        "key": "postgres-password",
                    },
                },
                "redis": {
                    "host": getRedisInstance()["host"],
                    "password": {"secret": "gitlab-redis-secret", "key": "redis-password"},
                },
                "registry": {"bucket": "{GCP_PROJECT}-{APP_NAME}-registry-storage"},
            },
            "certmanager": {"install": False},
            "certmanager-issuer": {"email": "{MY_EMAIL}"},
            "gitlab": {
                "toolbox": {
                    "backups": {
                        "objectStorage": {
                            "backend": "gcs",
                            "config": {
                                "gcpProject": "{GCP_PROJECT}",
                                "secret": "storage-config",
                                "key": "config",
                            },
                        }
                    }
                }
            },
            "gitlab-runner": {"install": False},
            "postgresql": {"install": False},
            "redis": {"install": False},
            "registry": {
                "storage": {"secret": "registry-storage", "key": "config", "extraKey": "gcs.json"}
            },
        },
    )


def createYamlFiles():
    """Creates various secrets and value yaml files for kubectl apply"""
    createPsqlSecretFile()
    createRedisSecretFile()
    createRegistrySecret()
    createRailsStorageSecret()
    createValuesYaml()


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

    # Delete the cloud resources
    if getSqlInstance():
        tkHelpers.run(f"gcloud -q sql instances delete {SQL_INSTANCE_NAME}", ignoreErrors=True)
    if getRedisInstance():
        tkHelpers.run(
            f"gcloud -q redis instances delete {REDIS_INSTANCE_NAME} --region={GCP_REGION}",
            ignoreErrors=True,
        )
    tkHelpers.run(
        f"gcloud -q iam service-accounts delete {saDict['client_email']}", ignoreErrors=True
    )
    for bucket in list(getBucketNames(valuesDict)):
        if tkHelpers.run(f"gcloud storage ls gs://{bucket}/", ignoreErrors=True) == 0:
            tkHelpers.run(
                f"gcloud storage rm --recursive gs://{bucket}/",
                ignoreErrors=True,
            )
    # tkHelpers.run(
    # f"gcloud services vpc-peerings delete --network={GCP_NETWORK_NAME} "
    # "--service=servicenetworking.googleapis.com",
    # ignoreErrors=True,
    # )
    tkHelpers.run(
        f"gcloud -q compute addresses delete google-managed-services-{GCP_NETWORK_NAME} --global",
        ignoreErrors=True,
    )
    tkHelpers.run(
        f"gcloud dns record-sets delete *.{GITLAB_DOMAIN}. --zone={GITLAB_DNS_ZONE}" " --type=A",
        ignoreErrors=True,
    )
    tkHelpers.run(
        f"gcloud -q compute addresses delete {APP_NAME}-external-ip --region={GCP_REGION}",
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


def deploy():
    """Deploy GCP (sql, redis, buckets, SA) resources, and GitLab via Helm"""
    createExternalAddress()
    createRecordSet()
    createPeeringAddress()
    createVpcPeering()
    createCloudSQL()
    createRedis()
    createServiceAccount()
    createBuckets()
    createYamlFiles()


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
        deploy()
    elif sys.argv[1].lower() == "destroy":
        destroy()
    else:
        print("Error: must specify 'deploy' or 'destroy' argument")
        sys.exit(1)
