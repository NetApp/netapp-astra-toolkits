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

import copy
import json
import kubernetes
import sys
from base64 import b64encode
from datetime import datetime, timedelta

from ac_gitlab import run, createYamlOnDisk


class ComputeEngineDisk:
    """Manages a Compute Engine Disk"""

    def __init__(self, partial_name, app_name):
        self.name = f"{app_name}-gitaly-{partial_name}-disk"
        self.app_name = app_name
        self.setProperties()

    def setProperties(self):
        self.properties = None
        for i in json.loads(
            run("gcloud compute disks list --format=json", captureOutput=True).decode()
        ):
            if i["name"] == self.name:
                self.properties = i

    def createDisk(self, dType, size, zone, imageFamily=None, imageProject=None):
        self.type = dType
        self.size = size
        self.zone = zone
        createStr = (
            f"gcloud compute disks create {self.name} --type={self.type} --size={self.size} "
            f"--zone={self.zone}"
        )
        if imageFamily:
            createStr += f" --image-family={imageFamily}"
        if imageProject:
            createStr += f" --image-project={imageProject}"
        run(createStr)
        self.setProperties()

    def createDiskFromBackup(self, sourceBackup, zone):
        self.zone = zone
        run(
            f"gcloud compute disks create {self.name} --source-snapshot={sourceBackup} "
            f"--zone={self.zone}"
        )
        self.setProperties()

    def getBackups(self):
        allSnaps = json.loads(
            run(
                f"gcloud compute snapshots list --format=json",
                captureOutput=True,
            ).decode()
        )
        backups = copy.deepcopy(allSnaps)
        for counter, snap in enumerate(allSnaps):
            if snap["sourceDisk"] != self.properties["selfLink"]:
                backups.remove(allSnaps[counter])
        return backups

    def createBackup(self, tmstmp):
        """Initiates a *multi-regional* disk snapshot (equivalent to a backup)"""
        run(
            f"gcloud compute snapshots create --async {self.name}-{tmstmp} --source-disk="
            f"{self.name} --source-disk-zone={self.properties['zone'].split('/')[-1]} "
            f"--storage-location={self.getMultiRegion(self.properties['zone'].split('/')[-1])}"
        )
        print(f" '{self.name}' backup successfully initiated")

    def deleteBackup(self, tmstmp):
        """Deletes a backup based on the tmstmp name"""
        run(f"gcloud -q compute snapshots delete {self.name}-{tmstmp}", ignoreErrors=True)

    def getMultiRegion(self, zone):
        """Returns either 'asia', 'eu', or 'us' depending upon the zone provided"""
        for mr in ["asia", "eu", "us"]:
            if mr in zone.split("-")[0]:
                return mr
        return "us"

    def deleteDisk(self):
        if self.properties:
            run(
                f"gcloud -q compute disks delete {self.name} "
                f"--zone={self.properties['zone'].split('/')[-1]}",
                ignoreErrors=True,
            )


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
        machineType,
        osDisk,
        dataDisks,
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
            f"gcloud compute instances create {self.name} --machine-type={machineType} "
            f"--disk=boot=yes,name={osDisk} {' '.join([f'--disk=name={d}' for d in dataDisks])} "
            f"--zone={self.zone} --network-interface=subnet={self.subnet},no-address "
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

    def updateDNS(self, hostname, zoneName):
        """Creates a DNS A Record pointing to the VM"""
        run(
            f"gcloud dns record-sets create {hostname}. --zone={zoneName} --type=A "
            f"--rrdatas={self.properties['networkInterfaces'][0]['networkIP']}"
        )

    def attachDisk(self, disk, boot=False):
        """Attaches a disk to an existing VM instance"""
        adStr = (
            f"gcloud compute instances attach-disk {self.name} --disk={disk} "
            + f"--zone={self.properties['zone'].split('/')[-1]}"
        )
        if boot:
            adStr += " --boot"
        run(adStr)

    def startupInstance(self):
        """Starts up a VM instance"""
        run(
            f"gcloud compute instances start {self.name} "
            f"--zone={self.properties['zone'].split('/')[-1]} --async"
        )

    def attachAndBoot(self):
        """Attaches disks and starts up the VM instance"""
        for disk in self.properties["disks"]:
            self.attachDisk(disk["source"].split("/")[-1], boot=disk["boot"])
        self.startupInstance()

    def shutdownInstance(self):
        """Shutdown / stop a VM instance"""
        run(
            f"gcloud compute instances stop {self.name} "
            f"--zone={self.properties['zone'].split('/')[-1]}"
        )

    def detachDisk(self, disk):
        """Detaches a disk from an instance (should first be shut down)"""
        run(
            f"gcloud compute instances detach-disk {self.name} --disk={disk}"
            f" --zone={self.properties['zone'].split('/')[-1]}"
        )

    def shutdownAndDetach(self):
        """Shuts down and detaches disks from a VM instance"""
        self.shutdownInstance()
        for disk in self.properties["disks"]:
            self.detachDisk(disk["source"].split("/")[-1])

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

    def getBackups(self):
        if (
            type(
                backups := run(
                    f"gcloud sql backups list --instance={self.name} --format=json",
                    captureOutput=True,
                    ignoreErrors=True,
                )
            )
            is not int
        ):
            return json.loads(backups.decode())
        else:
            return []

    def createBackup(self, tmstmp):
        """Initiates a cloud SQL backup operation"""
        run(
            f"gcloud sql backups create --async --instance={self.name} "
            f"--description={self.name}-{tmstmp}"
        )
        print(f"Cloud SQL '{self.name}' backup successfully initiated")

    def deleteBackup(self, tmstmp):
        """Deletes a cloud SQL backup"""
        for backup in self.getBackups():
            if tmstmp in backup["description"]:
                run(
                    f"gcloud -q sql backups delete {backup['id']} --instance={self.name}",
                    ignoreErrors=True,
                )

    def restoreFromBackup(self, backupID):
        """Restores a Cloud SQL instance from a backupID"""
        run(f"gcloud sql backups restore {backupID} --quiet --async --restore-instance={self.name}")
        print(f"Cloud SQL {self.name} restore successfully initiated")

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

    def addBucketIamPolicy(self, bucket):
        """Adds the roles/storage.admin role to {bucket} to enable backups/exports"""
        run(
            f"gcloud storage buckets add-iam-policy-binding gs://{bucket} "
            f"--member={self.properties['persistenceIamIdentity']} --role=roles/storage.admin"
        )

    def getBackups(self, bucket):
        allOps = json.loads(
            run(
                f"gcloud redis operations list --region={self.region} --format=json",
                captureOutput=True,
            ).decode()
        )
        ops = copy.deepcopy(allOps)
        for counter, op in enumerate(allOps):
            if (
                op["metadata"]["target"].split("/")[-1] != self.name
                or op["metadata"]["verb"] != "export"
            ):
                ops.remove(allOps[counter])
        # 'redis operations' unfortunately do not have any information about GCS location,
        # so instead we'll manually infer based on timestamps
        if (
            type(
                rdbs := run(
                    f"gcloud storage ls --buckets gs://{bucket}/{self.name}",
                    captureOutput=True,
                    ignoreErrors=True,
                )
            )
            is not int
        ):
            rdbs = rdbs.decode().rstrip().split("\n")
            for op in ops:
                for rdb in rdbs:
                    if abs(
                        datetime.strptime(
                            op["metadata"]["createTime"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
                        )
                        - datetime.strptime(
                            rdb.split("/")[-1].split("-")[-1].split(".")[0], "%Y%m%d%H%M"
                        )
                    ) < timedelta(minutes=2):
                        op["gcsLocation"] = rdb
                        op["backupName"] = rdb.split("/")[-1].split(".")[0]
        return ops

    def createBackup(self, bucket, tmstmp):
        """Initiates an export operation of the redis instance to object storage"""
        self.exportOp = json.loads(
            run(
                f"gcloud redis instances export gs://{bucket}/{self.name}/{self.name}-{tmstmp}.rdb"
                + f" {self.name} --region={self.region} --async --format=json",
                captureOutput=True,
            ).decode()
        )
        print(f"Redis '{self.name}' export successfully initiated")

    def deleteBackup(self, bucket, tmstmp):
        """Deletes a Redis export (backup) from object storage bucket"""
        run(
            f"gcloud storage rm gs://{bucket}/{self.name}/{self.name}-{tmstmp}.rdb",
            ignoreErrors=True,
        )

    def restoreFromBackup(self, gcsLocation):
        """Restores (imports) a Redis instance"""
        run(
            f"gcloud redis instances import {gcsLocation} {self.name} --region={self.region} "
            "--async",
        )
        print(f"Redis {self.name} import successfully initiated")

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
