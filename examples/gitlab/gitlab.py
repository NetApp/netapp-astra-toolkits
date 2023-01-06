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
from base64 import b64encode, b64decode

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
GCP_NETWORK_NAME = "gke-prod-network"  # Existing network name, must be GKE's network
GCP_PROJECT = getGcpProject()  # Uses gcloud config value
GCP_REGION = "us-east4"  # Region to deploy the resources in, must be GKE's region
GCP_ZONE = "us-east4-b"  # Zone to deploy the resources in
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


class ComputeEngineVM:
    """Manages a Compute Engine VM instance for Gitaly"""

    def __init__(self, app_name):
        self.name = app_name + "-gitaly-demo"
        self.app_name = app_name
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for i in json.loads(
            run("gcloud compute instances list --format=json", captureOutput=True).decode()
        ):
            if i["name"] == self.name:
                self.properties = i

    def createInstance(
        self,
        imageFamily,
        imageProject,
        machineType,
        network,
        zone,
        project,
        authToken,
        shellToken,
        cloudinit,
    ):
        self.network = network
        self.zone = zone
        self.project = project
        self.authToken = authToken
        self.shellToken = shellToken
        self.getSubnet()
        createYamlOnDisk(f"{self.app_name}-gitaly-cloudinit.yaml", cloudinit)
        run(
            f"gcloud compute instances create {self.name} --image-family={imageFamily} "
            f"--image-project={imageProject} --machine-type={machineType} --zone={self.zone} "
            f"--network-interface=subnet={self.subnet},no-address --create-disk=auto-delete="
            f"yes,device-name={self.app_name}-disk,mode=rw,name={self.app_name}-disk,size=100,"
            f"type=projects/{self.project}/zones/{self.zone}/diskTypes/pd-ssd "
            f"--metadata-from-file=user-data={self.app_name}-gitaly-cloudinit.yaml"
        )
        self.setProperties()

    def getSubnet(self):
        """Gets the subnet that the GKE cluster belongs in based on the current k8s context"""
        self.subnet = None
        _, context = kubernetes.config.list_kube_config_contexts()
        for i in json.loads(
            run("gcloud container clusters list --format=json", captureOutput=True).decode()
        ):
            if i["name"] in context["context"]["cluster"]:
                self.subnet = i["subnetwork"]
        if self.subnet is None:
            print(
                f"Unable to determine subnet, context {context['name']} not present in 'gcloud "
                "container clusters list'"
            )
            sys.exit(1)

    def createSecretFile(self):
        """Creates a Gitaly authToken secret and shell authToken secret dictionaries,
        and then writes yaml to disk"""
        createYamlOnDisk(
            f"{self.app_name}-gitaly-secret.yaml",
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": f"{self.app_name}-gitaly-token",
                    "namespace": self.app_name,
                    "labels": {"app": self.app_name},
                },
                "type": "Opaque",
                "data": {"token": b64encode(self.authToken.encode()).decode()},
            },
        )
        createYamlOnDisk(
            f"{self.app_name}-shell-secret.yaml",
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": f"{self.app_name}-shell-token",
                    "namespace": self.app_name,
                    "labels": {"app": self.app_name},
                },
                "type": "Opaque",
                "data": {"token": b64encode(self.shellToken.encode()).decode()},
            },
        )
        createYamlOnDisk(
            f"{self.app_name}-psql-secret.yaml",
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": f"{self.app_name}-postgresql-password",
                    "namespace": self.app_name,
                    "labels": {"app": self.app_name},
                },
                "type": "Opaque",
                "data": {"postgres-password": b64encode(self.password.encode()).decode()},
            },
        )

    def updateDNS(self, hostname, zoneName):
        """Creates a DNS A Record pointing to the VM"""
        run(
            f"gcloud dns record-sets create {hostname}. --zone={zoneName} --type=A "
            f"--rrdatas={self.properties['networkInterfaces'][0]['networkIP']}"
        )

    def deleteInstance(self):
        if self.properties:
            run(
                f"gcloud -q compute instances delete {self.name} "
                f"--zone={self.properties['zone'].split('/')[-1]}",
                ignoreErrors=True,
            )
            for f in [
                f"{self.app_name}-gitaly-cloudinit.yaml",
                f"{self.app_name}-gitaly-secret.yaml",
                f"{self.app_name}-shell-secret.yaml",
            ]:
                print(f"Removing {f}")
                run(f"rm {f}", ignoreErrors=True)


class CloudPostgreSQL:
    """Manages a PostgreSQL 14 Cloud SQL instance"""

    def __init__(self, app_name):
        self.name = app_name + "-psql-demo"
        self.app_name = app_name
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for i in json.loads(
            run("gcloud sql instances list --format=json", captureOutput=True).decode()
        ):
            if i["name"] == self.name:
                self.properties = i

    def createInstance(self, network, zone, region, project, cpu, mem, password):
        self.network = network
        self.zone = zone
        self.region = region
        self.project = project
        self.mem = mem
        self.cpu = cpu
        self.password = password
        run(
            f"gcloud sql instances create {self.name} --database-version=POSTGRES_14 "
            f"--cpu={self.cpu} --memory={self.mem} --zone={self.zone} "
            f"--root-password={self.password} --no-assign-ip "
            f"--network=projects/{self.project}/global/networks/{self.network}"
        )
        self.setProperties()

    def createUser(self, user):
        run(f"gcloud sql users create {user} --instance={self.name} --password={self.password}")

    def createDB(self, db):
        run(f"gcloud sql databases create {db} --instance={self.name}")

    def createSecretFile(self):
        """Creates a PostgreSQL secret dictionary, then writes yaml to disk"""
        createYamlOnDisk(
            f"{self.app_name}-psql-secret.yaml",
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": f"{self.app_name}-postgresql-password",
                    "namespace": self.app_name,
                    "labels": {"app": self.app_name},
                },
                "type": "Opaque",
                "data": {"postgres-password": b64encode(self.password.encode()).decode()},
            },
        )

    def deleteInstance(self):
        if self.properties:
            run(f"gcloud -q sql instances delete {self.name}", ignoreErrors=True)
            print(f"Removing {self.app_name}-psql-secret.yaml")
            run(f"rm {self.app_name}-psql-secret.yaml", ignoreErrors=True)


class CloudRedis:
    """Manages a Memorystore Redis instance"""

    def __init__(self, app_name, region):
        self.name = app_name + "-redis-demo"
        self.app_name = app_name
        self.region = region
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for i in json.loads(
            run(
                f"gcloud redis instances list --region={self.region} --format=json",
                captureOutput=True,
            ).decode()
        ):
            if i["name"].split("/")[-1] == self.name:
                self.properties = i
        if self.properties:
            self.authString = json.loads(
                run(
                    f"gcloud redis instances get-auth-string {self.name} --region={self.region} "
                    "--format=json",
                    captureOutput=True,
                ).decode()
            )["authString"]

    def createInstance(self, network, zone, project, mem, tier="standard", persistence="rdb"):
        self.network = network
        self.zone = zone
        self.project = project
        self.mem = mem
        self.tier = tier
        self.persistence = persistence
        run(
            f"gcloud -q redis instances create {self.name} --region={self.region} "
            f"--zone={self.zone} --size={self.mem} --tier={self.tier} --persistence-mode="
            f"{self.persistence} --rdb-snapshot-period=1h --connect-mode=private-service-access "
            f"--network=projects/{self.project}/global/networks/{self.network} --enable-auth"
        )
        self.setProperties()

    def createSecretFile(self):
        """Creates a Redis secret dictionary, then writes yaml to disk"""
        createYamlOnDisk(
            f"{self.app_name}-redis-secret.yaml",
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": f"{self.app_name}-redis-secret",
                    "namespace": self.app_name,
                    "labels": {"app": self.app_name},
                },
                "type": "Opaque",
                "data": {"redis-password": b64encode(self.authString.encode()).decode()},
            },
        )

    def deleteInstance(self):
        if self.properties:
            run(
                f"gcloud -q redis instances delete {self.name} --region={self.region}",
                ignoreErrors=True,
            )
            print(f"Removing {self.app_name}-redis-secret.yaml")
            run(f"rm {self.app_name}-redis-secret.yaml", ignoreErrors=True)


class ExternalDnsAddress:
    """Manages external DNS for *.domain.tld
    Domain must already exist and be managed by GCP"""

    def __init__(self, app_name, region):
        self.name = app_name + "-external-ip"
        self.region = region
        self.setProperties()

    def setProperties(self):
        bProperties = run(
            f"gcloud compute addresses describe {self.name} --region {self.region} --format=json",
            captureOutput=True,
            ignoreErrors=True,
        )
        if type(bProperties) is bytes:
            self.properties = json.loads(bProperties.decode())
        else:
            self.properties = None

    def createExternalAddress(self):
        """Creates an external IP address to set as the GitLab DNS IP"""
        run(f"gcloud compute addresses create {self.name} --region {self.region}")
        self.setProperties()

    def deleteAddress(self):
        """Deletes the external IP address"""
        run(
            f"gcloud -q compute addresses delete {self.name} --region={self.region}",
            ignoreErrors=True,
        )


class RecordSet:
    """Manages the DNS record set based on domain and DNS zone names"""

    def __init__(self, region, fqdn, dns_zone, app_name):
        self.region = region
        self.fqdn = fqdn
        self.dns_zone = dns_zone
        self.app_name = app_name
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for r in json.loads(
            run(
                f"gcloud dns record-sets list --zone={self.dns_zone} --format=json",
                captureOutput=True,
            ).decode()
        ):
            if r["name"] == f"{self.fqdn}.":
                self.properties = r

    def createRecordSet(self, address):
        run(
            f"gcloud dns record-sets create {self.fqdn}. --zone={self.dns_zone} --type=A "
            f"--rrdatas={address}"
        )
        """
        ExternalDnsAddress:
        run(
            f"gcloud dns record-sets create *.{self.domain}. --zone={self.dns_zone} --type=A --ttl"
            f"=60 --rrdatas={ExternalDnsAddress(self.app_name, self.region).properties['address']}"
        )
        Gitaly:
        run(
            f"gcloud dns record-sets create {hostname}. --zone={zoneName} --type=A "
            f"--rrdatas={self.properties['networkInterfaces'][0]['networkIP']}"
        )"""
        self.setProperties()

    def deleteRecordSet(self):
        run(
            f"gcloud dns record-sets delete {self.fqdn} --zone={self.dns_zone} --type=A",
            ignoreErrors=True,
        )


class VpcPeering:
    """Manages the VPC peering between Cloud SQL and GKE"""

    def __init__(self, network, project):
        self.network = network
        self.project = project
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for p in json.loads(
            run(
                f"gcloud services vpc-peerings list --network={self.network} --format=json",
                captureOutput=True,
            ).decode()
        ):
            if p["service"] == "services/servicenetworking.googleapis.com":
                self.properties = p

    def createPeering(self):
        run(
            f"gcloud compute addresses create google-managed-services-{self.network}"
            " --global --purpose=VPC_PEERING --prefix-length=20 "
            f"--network=projects/{self.project}/global/networks/{self.network}"
        )
        run(
            "gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com "
            f"--ranges=google-managed-services-{self.network} --network={self.network} "
            f"--project={self.project}"
        )
        self.setProperties()

    def deletePeering(self):
        run(
            f"gcloud -q compute addresses delete google-managed-services-{self.network} --global",
            ignoreErrors=True,
        )
        # The command below will fail due to the reasons explained here, so commenting it out but
        # leaving it for posterity:
        # https://cloud.google.com/vpc/docs/configure-private-services-access#removing-connection
        # For example, if you delete a Cloud SQL instance, you receive a success response, but the
        # service waits for four days before deleting the service producer resources. The waiting
        # period means that if you change your mind about deleting the service, you can request to
        # reinstate the resources. If you try to delete the connection during the waiting period,
        # the deletion fails with a message that the resources are still in use by the service
        # producer.
        """run(
            f"gcloud services vpc-peerings delete --network={self.network} "
            "--service=servicenetworking.googleapis.com",
            ignoreErrors=True,
        )"""


class ServiceAccount:
    """Manages the storage service account used for object storage management"""

    def __init__(self, app_name, project):
        self.app_name = app_name
        self.name = f"{app_name}-gcs"
        self.project = project
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for sa in json.loads(
            run(
                "gcloud iam service-accounts list --format=json",
                captureOutput=True,
            ).decode()
        ):
            if sa["displayName"] == self.name:
                self.properties = sa

    def createServiceAccount(self):
        """Creates a Cloud Storage Service Account for object storage"""
        run(f"gcloud iam service-accounts create {self.name} --display-name {self.name}")
        run(
            f"gcloud projects add-iam-policy-binding --role roles/storage.admin {self.project} "
            f"--member=serviceAccount:{self.name}@{self.project}.iam.gserviceaccount.com"
        )
        run(
            f"gcloud iam service-accounts keys create --iam-account {self.name}@{self.project}"
            f".iam.gserviceaccount.com {self.app_name}-storage.config"
        )
        self.setProperties()

    def createRegistrySecret(self):
        """Creates a Object storage bucket secret for the registry bucket"""
        createYamlOnDisk(
            f"{self.app_name}-registry-storage.yaml",
            {
                "gcs": {
                    "bucket": f"{self.project}-{self.app_name}-registry-storage",
                    "keyfile": "/etc/docker/registry/storage/gcs.json",
                }
            },
        )

    def createRailsStorageSecret(self):
        """Creates a Rails Object Storage secret for all non-registry buckets"""
        with open(f"{self.app_name}-storage.config", encoding="utf8") as f:
            saStr = f.read().rstrip()
        createYamlOnDisk(
            f"{self.app_name}-rails.yaml",
            {
                "provider": "Google",
                "google_project": "astracontroltoolkitdev",
                "google_json_key_string": saStr,
            },
        )

    def deleteServiceAccount(self):
        if self.properties:
            run(
                f"gcloud -q iam service-accounts delete {self.properties['email']}",
                ignoreErrors=True,
            )
        for f in [
            f"{self.app_name}-storage.config",
            f"{self.app_name}-registry-storage.yaml",
            f"{self.app_name}-rails.yaml",
        ]:
            print(f"Removing {f}")
            run(f"rm {f}", ignoreErrors=True)


class ObjectBuckets:
    """Manages the object storage buckets needed for GitLab"""

    def __init__(self, app_name, project, buckets):
        self.app_name = app_name
        self.project = project
        self.buckets = buckets

    def createBuckets(self):
        for bucket in self.buckets:
            run(f"gcloud storage buckets create gs://{bucket}", ignoreErrors=True)

    def deleteBuckets(self):
        for bucket in self.buckets:
            if run(f"gcloud storage ls gs://{bucket}/", ignoreErrors=True) is True:
                run(f"gcloud storage rm --recursive gs://{bucket}/", ignoreErrors=True)


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
    """Destroy Cloud SQL, Redis, Buckets, and storage service account"""
    RecordSet(
        GCP_REGION,
        valuesDict["global"]["gitaly"]["external"][0]["hostname"],
        GITLAB_DNS_ZONE,
        APP_NAME,
    ).deleteRecordSet()
    ComputeEngineVM(APP_NAME).deleteInstance()
    CloudPostgreSQL(APP_NAME).deleteInstance()
    CloudRedis(APP_NAME, GCP_REGION).deleteInstance()
    ServiceAccount(APP_NAME, GCP_PROJECT).deleteServiceAccount()
    ObjectBuckets(APP_NAME, GCP_PROJECT, list(getBucketNames(valuesDict))).deleteBuckets()
    VpcPeering(GCP_NETWORK_NAME, GCP_PROJECT).deletePeering()
    RecordSet(GCP_REGION, f"*.{GITLAB_DOMAIN}", GITLAB_DNS_ZONE, APP_NAME).deleteRecordSet()
    ExternalDnsAddress(APP_NAME, GCP_REGION).deleteAddress()


def destroyKubernetesResources():
    """Destroy the Kubernetes resources and values file"""
    run(f"kubectl delete namespace {APP_NAME}", ignoreErrors=True)
    print(f"Removing {APP_NAME}-values.yaml")
    run(f"rm {APP_NAME}-values.yaml", ignoreErrors=True)


def destroy(valuesDict):
    """Destroy Astra (snapshots, backups, app), GCP (sql, redis, buckets, SA),
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

    # Create a VM instance for Gitaly if not already present
    gitaly = ComputeEngineVM(APP_NAME)
    if not gitaly.properties:
        gitaly.createInstance(
            "ubuntu-2204-lts",
            "ubuntu-os-cloud",
            "n2-standard-4",
            GCP_NETWORK_NAME,
            GCP_ZONE,
            GCP_PROJECT,
            GITALY_AUTH,
            GITLAB_SHELL,
            cloudinit,
        )
        gitaly.createSecretFile()

    # Create a DNS record set so other services can access the Gitaly VM
    grs = RecordSet(
        GCP_REGION,
        valuesDict["global"]["gitaly"]["external"][0]["hostname"],
        GITLAB_DNS_ZONE,
        APP_NAME,
    )
    if not grs.properties:
        grs.createRecordSet(gitaly.properties["networkInterfaces"][0]["networkIP"])

    # Create an external IP for Gitlab access if not already present
    extIP = ExternalDnsAddress(APP_NAME, GCP_REGION)
    if not extIP.properties:
        extIP.createExternalAddress()
    valuesDict["global"]["hosts"]["externalIP"] = extIP.properties["address"]

    # Create a wildcard DNS record set to point at the external IP
    wrs = RecordSet(GCP_REGION, f"*.{GITLAB_DOMAIN}", GITLAB_DNS_ZONE, APP_NAME)
    if not wrs.properties:
        wrs.createRecordSet(extIP.properties["address"])

    # Create a VPC peering between the GKE network and Cloud SQL
    vp = VpcPeering(GCP_NETWORK_NAME, GCP_PROJECT)
    if not vp.properties:
        vp.createPeering()

    # Create a PostgreSQL instance
    db = CloudPostgreSQL(APP_NAME)
    if not db.properties:
        db.createInstance(
            GCP_NETWORK_NAME, GCP_ZONE, GCP_REGION, GCP_PROJECT, "2", "8GiB", DB_PASSWORD
        )
        db.createUser("gitlab")
        db.createDB("gitlabhq_production")
        db.createSecretFile()
    valuesDict["global"]["psql"]["host"] = db.properties["ipAddresses"][0]["ipAddress"]

    # Create a Redis instance
    redis = CloudRedis(APP_NAME, GCP_REGION)
    if not redis.properties:
        redis.createInstance(GCP_NETWORK_NAME, GCP_ZONE, GCP_PROJECT, "4")
        redis.createSecretFile()
    valuesDict["global"]["redis"]["host"] = redis.properties["host"]

    # Create a service account for cloud storage
    sa = ServiceAccount(APP_NAME, GCP_PROJECT)
    if not sa.properties:
        sa.createServiceAccount()
        sa.createRegistrySecret()
        sa.createRailsStorageSecret()

    # Create cloud storage buckets for all buckets listed in the values Dict
    ObjectBuckets(APP_NAME, GCP_PROJECT, list(getBucketNames(valuesDict))).createBuckets()


def applyYamlSecrets():
    """Applies the previously create yaml secret files"""
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
    """Creates values file, runs helm install command, manages the Astra app"""

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
            "hosts": {
                "domain": GITLAB_DOMAIN,
            },
            "ingress": {"configureCertmanager": False},
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
        "certmanager": {"install": False},
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
        "gitlab-runner": {"install": False},
        "postgresql": {"install": False},
        "redis": {"install": False},
        "registry": {
            "storage": {"secret": "registry-storage", "key": "config", "extraKey": "gcs.json"}
        },
    }

    if len(sys.argv) < 2:
        print("Error: must specify 'deploy' or 'destroy' argument")
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

    else:
        print("Error: must specify 'deploy' or 'destroy' argument")
        sys.exit(1)
