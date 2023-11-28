# Update

The `update` argument allows you to update an Astra resource, at this time only including:

* [Bucket](#bucket)
* [Cloud](#cloud)
* [Cluster](#cluster)
* [Replication](#replication)
* [Script](#script)

```text
$ actoolkit update -h
usage: actoolkit update [-h] {bucket,cloud,cluster,replication,script} ...

options:
  -h, --help            show this help message and exit

objectType:
  {bucket,cloud,cluster,replication,script}
    bucket              update bucket
    cloud               update cloud
    cluster             update cluster
    replication         update replication
    script              update script
```

## Bucket

The `update bucket` command allows you to update the credential of a managed [bucket](../manage/README.md#bucket).  The high level command usage is:

```text
actoolkit update bucket <bucketID> <credentialGroupArgs>
```

The \<bucketID\> argument can be gathered from a [list buckets](../list/README.md#buckets) command.  The possible \<credentialGroupArgs\> are:

* `--credentialID`/`-c`: the **already existing** [credentialID](../list/README.md#credentials), or
* `--accessKey` and `--accessSecret`: to create a new credential which the bucket is then updated to use

Sample commands and output are as follows:

```text
$ actoolkit update bucket 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac \
    --credentialID ad0754c4-08dd-4b68-b478-b4d2456968d3
{"type": "application/astra-bucket", "version": "1.0", "id": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "name": "astra-gcp-backup-fbe43be9aaa0", "state": "available", "credentialID": "ad0754c4-08dd-4b68-b478-b4d2456968d3", "provider": "gcp", "bucketParameters": {"gcp": {"bucketName": "astra-gcp-backup-fbe43be9aaa0"}}, "metadata": {"labels": [{"name": "astra.netapp.io/labels/internal/nautilusCreated", "value": "true"}], "creationTimestamp": "2022-04-28T19:05:53Z", "modificationTimestamp": "2023-02-07T19:03:21Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

```text
$ actoolkit update bucket 266f3453-fef2-4f93-849b-a165a5625d25 \
    --accessKey accessKey1234567890 --accessSecret accessSecret1234567890
{"type": "application/astra-credential", "version": "1.1", "id": "03851a0d-c8cb-4550-83da-40cde27e530a", "name": "mhaigh-test-bucket", "keyType": "s3", "valid": "true", "metadata": {"creationTimestamp": "2023-02-07T19:08:55Z", "modificationTimestamp": "2023-02-07T19:08:55Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "s3"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "s3"}]}}
{"type": "application/astra-bucket", "version": "1.1", "id": "266f3453-fef2-4f93-849b-a165a5625d25", "name": "mhaigh-test-bucket", "state": "available", "credentialID": "03851a0d-c8cb-4550-83da-40cde27e530a", "provider": "gcp", "bucketParameters": {"gcp": {"bucketName": "mhaigh-test-bucket"}}, "metadata": {"creationTimestamp": "2023-02-06T20:19:58Z", "modificationTimestamp": "2023-02-07T19:08:55Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Cloud

The `update cloud` command allows you to update the credential and/or default bucket of a [cloud](../manage/README.md#cloud).  The high level command usage is:

```text
actoolkit update cloud <cloudID> <updateArg>
```

The \<cloudID\> argument can be gathered from a [list clouds](../list/README.md#clouds) command.  The other three possible arguments are:

### Credential Path

To update the credentials of a cloud to a currently non-existing credential, use the `--credentialPath` argument to point at a local filesystem JSON credential object:

```text
actoolkit update cloud <cloudID> --credentialPath path/to/credentials.json
```

This command first creates the credential object, and then updates the cloud to reference the new credential ID:

```text
$ actoolkit update cloud 0ec2e027-80bc-426a-b844-692de243b29e -c ~/gcp-astra-demo-3d7d.json
{"type": "application/astra-credential", "version": "1.1", "id": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "name": "astra-sa@GCP", "keyType": "generic", "valid": "true", "metadata": {"creationTimestamp": "2023-02-06T19:54:32Z", "modificationTimestamp": "2023-02-06T19:54:32Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "service-account"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "GCP"}]}}
{"type": "application/astra-cloud", "version": "1.0", "id": "0ec2e027-80bc-426a-b844-692de243b29e", "name": "GCP", "state": "running", "stateUnready": [], "cloudType": "GCP", "credentialID": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "defaultBucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "metadata": {"labels": [], "creationTimestamp": "2022-04-26T01:53:06Z", "modificationTimestamp": "2023-02-06T19:54:33Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Credential ID

To update the credentials of a cloud to a currently existing credential, use the `--credentialID` argument to reference an existing credentialID:

```text
actoolkit update cloud <cloudID> --credentialID <credentialID>
```

The \<credentialID\> value can be gathered from a [list credentials](../list/README.md#credentials) command.

```text
$ actoolkit update cloud 0ec2e027-80bc-426a-b844-692de243b29e \
    --credentialID 8e6c9667-f2f2-40c2-92d0-38467f7f45be
{"type": "application/astra-cloud", "version": "1.0", "id": "0ec2e027-80bc-426a-b844-692de243b29e", "name": "GCP", "state": "running", "stateUnready": [], "cloudType": "GCP", "credentialID": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "defaultBucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "metadata": {"labels": [], "creationTimestamp": "2022-04-26T01:53:06Z", "modificationTimestamp": "2023-02-08T13:48:23Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Default Bucket

To change a cloud's default bucket for backups, run the following command:

```text
actoolkit update cloud <cloudID> --defaultBucketID <bucketID>
```

The \<bucketID\> can be gathered from a [list buckets](../list/README.md#buckets) command (the bucket must already be under [management](../manage/README.md#bucket)).

```text
$ actoolkit update cloud 0ec2e027-80bc-426a-b844-692de243b29e --defaultBucketID 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac
{"type": "application/astra-cloud", "version": "1.0", "id": "0ec2e027-80bc-426a-b844-692de243b29e", "name": "GCP", "state": "running", "stateUnready": [], "cloudType": "GCP", "credentialID": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "defaultBucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "metadata": {"labels": [], "creationTimestamp": "2022-04-26T01:53:06Z", "modificationTimestamp": "2023-02-06T20:24:53Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Cluster

The `update cluster` command allows you to update a [cluster](../create/README.md#cluster).  The high level command usage is:

```text
actoolkit update cluster <clusterID> <updateArg>
```

The \<clusterID\> argument can be gathered from a [list clusters](../list/README.md#clusters) command.  The available \<updateArg\> values are currently `--credentialPath` and `--defaultBucketID`, as detailed below.

### Credential Path

The `-p`/`--credentialPath` argument allows for updating the kubeconfig credential of an existing cluster:

```text
actoolkit update cluster <clusterID> --credentialPath path/to/kubeconfig
```

```text
$ actoolkit update cluster 2d37cc47-f543-46a6-8895-2504b1a50ce2 --credentialPath ~/.kube/config
{"type": "application/astra-credential", "version": "1.1", "id": "f1bfe212-fb48-4f1f-9637-138efc04e788", "name": "aks-eastus-cluster", "keyType": "kubeconfig", "valid": "true", "metadata": {"creationTimestamp": "2023-03-07T20:17:21Z", "modificationTimestamp": "2023-03-07T20:26:48Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "kubeconfig"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "private"}, {"name": "astra.netapp.io/labels/read-only/clusterID", "value": "2d37cc47-f543-46a6-8895-2504b1a50ce2"}, {"name": "astra.netapp.io/labels/read-only/clusterName", "value": "aks-eastus-cluster"}]}}
```

### Default Bucket

To change or add a cluster's default bucket for backups and appVaults, run the following command:

```text
actoolkit update cluster <clusterID> --defaultBucketID <bucketID>
```

The \<bucketID\> argument can be gathered from a [list buckets](../list/README.md#buckets) command.

```text
$ actoolkit update cluster d0e0767b-1d77-478d-8640-13272efe1e23 --defaultBucketID 78263925-c3b3-48af-97c9-32bc5bde3273
{"type": "application/astra-managedCluster", "version": "1.6", "id": "d0e0767b-1d77-478d-8640-13272efe1e23", "name": "uscentral1", "state": "running", "stateUnready": [], "managedState": "managed", "protectionState": "full", "protectionStateDetails": [], "restoreTargetSupported": "true", "snapshotSupported": "true", "managedStateUnready": [], "managedTimestamp": "2023-11-28T14:30:42Z", "inUse": "true", "clusterType": "gke", "clusterVersion": "1.27", "clusterVersionString": "v1.27.3-gke.100", "connectorCapabilities": ["relayV1", "watcherV1", "neptuneV1"], "namespaces": [], "defaultStorageClass": "274562c4-9fff-4051-b16b-9db6db60651b", "cloudID": "d1c502e6-d410-46fc-8c15-f67c5b63dea2", "credentialID": "dcf1c466-d0fe-4bdf-b3ba-6e0e6e0ae066", "isMultizonal": "false", "tridentManagedStateAllowed": ["unmanaged"], "tridentVersion": "23.10.0-test.6d2477dfad063cd2277395663d5b06d198365c9e+6d2477dfad063cd2277395663d5b06d198365c9e", "acpVersion": "23.10.0-test.6d2477dfad063cd2277395663d5b06d198365c9e+3670363ff598b0105b8b2735323d3c0ae3ccabb8", "privateRouteID": "b68aa04d-a787-483f-9d9e-7c2930981534", "apiServiceID": "727422d9-abca-45d6-876e-3a6c62ef5664", "defaultBucketID": "", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/cloudName", "value": "private"}], "creationTimestamp": "2023-11-28T14:30:42Z", "modificationTimestamp": "2023-11-28T15:41:36Z", "createdBy": "45347ae2-6a07-41b0-a544-674ac4317b87"}}
```

## Replication

The `update replication` command allows you to **failover**, **reverse**, or **resync** an existing [replication policy](../create/README.md#replication).  It is currently **only** supported for ACC environments.  The high level command usage is:

```text
actoolkit update replication <replicationID> <operation>
```

The \<replicationID\> argument can be gathered from a [list replications](../list/README.md#replications) command.

The \<operation\> keyword can be one of **failover**, **reverse**, or **resync**, as detailed below.

### Failover

The **failover** operation stops the replication relationship and brings the app online on the destination cluster. This procedure does not stop the app on the source cluster if it was operational.

```text
$ actoolkit update replication 5dbb4893-373d-46be-a5ec-cbdbf65ac673 failover
{"type": "application/astra-appMirror", "version": "1.0", "id": "5dbb4893-373d-46be-a5ec-cbdbf65ac673", "namespaceMapping": [{"clusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaces": ["wordpress"]}, {"clusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaces": ["wordpress"]}], "state": "failingOver", "stateDesired": "failedOver", "stateDetails": [{"type": "https://astra.netapp.io/stateDetails/24", "title": "Snapshot replication completed", "detail": "A snapshot was replicated to the destination.", "additionalDetails": {"completionTime": "2022-09-20T18:07:03Z", "snapshotID": "037d315c-a40a-4e26-8624-1910f847137f", "startTime": "2022-09-20T18:05:43Z"}}], "transferState": "idle", "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-19T19:09:32Z", "modificationTimestamp": "2022-09-20T18:58:31Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444"}, "ReplicatedPVCs_": null}
Replication failover initiated
```

### Resync

The **resync** operation re-establishes the replication relationship. You can choose which data to retain through the `--dataSource`/`-s` argument and either the `clusterID` or `appID` of the side you wish to use as the replication source.

This operation re-establishes the SnapMirror relationships to start the volume replication in the direction of choice.  The process also stops the app on the new destination cluster before re-establishing replication.

```text
$ actoolkit update replication 5dbb4893-373d-46be-a5ec-cbdbf65ac673 resync -s f3332e48-d175-4d6d-852f-bdee0f65a6fe
{"type": "application/astra-appMirror", "version": "1.0", "id": "5dbb4893-373d-46be-a5ec-cbdbf65ac673", "sourceAppID": "dbda1d21-76b2-4cad-bd92-f047e41453c7", "sourceClusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "destinationAppID": "1be8daef-816e-4d17-a449-14b03639dcd1", "destinationClusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaceMapping": [{"clusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaces": ["wordpress"]}, {"clusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaces": ["wordpress"]}], "state": "establishing", "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [], "transferState": "idle", "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-19T19:09:32Z", "modificationTimestamp": "2022-09-20T19:59:09Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444"}, "ReplicatedPVCs_": null}
Replication resync initiated
```

### Reverse

The **reverse** operation moves the application to the destination cluster while continuing to replicate back to the original source cluster. Astra Control stops the application on the source cluster and replicates the data to the destination before failing over the app to the destination cluster.

In this situation, you are swapping the source and destination. The original source cluster becomes the new destination cluster, and the original destination cluster becomes the new source cluster.

```text
$ actoolkit update replication 5dbb4893-373d-46be-a5ec-cbdbf65ac673 reverse
{"type": "application/astra-appMirror", "version": "1.0", "id": "5dbb4893-373d-46be-a5ec-cbdbf65ac673", "sourceAppID": "1be8daef-816e-4d17-a449-14b03639dcd1", "sourceClusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "destinationAppID": "dbda1d21-76b2-4cad-bd92-f047e41453c7", "destinationClusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaceMapping": [{"clusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaces": ["wordpress"]}, {"clusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaces": ["wordpress"]}], "state": "establishing", "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [{"type": "https://astra.netapp.io/stateDetails/24", "title": "Snapshot replication completed", "detail": "A snapshot was replicated to the destination.", "additionalDetails": {"completionTime": "2022-09-20T20:07:05Z", "snapshotID": "1a5fc936-4f21-4e27-8081-d17155f50453", "startTime": "2022-09-20T20:05:44Z"}}], "transferState": "idle", "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-19T19:09:32Z", "modificationTimestamp": "2022-09-20T20:18:44Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444"}, "ReplicatedPVCs_": null}
Replication reverse initiated
```

## Script

The `update script` command allows you to update the source of an already existing [script](../create/README.md#script).  The high level command usage is:

```text
actoolkit update script <scriptID> <updatedScriptFilePath>
```

The \<scriptID\> argument can be gathered from a [list scripts](../list/README.md#scripts) command.

Sample command and output are as follows:

```text
$ actoolkit update script 282adc93-9df7-40e7-89d5-e120f525628d exampleScript.sh
{"metadata": {"labels": [], "creationTimestamp": "2023-02-08T21:31:30Z", "modificationTimestamp": "2023-02-08T21:32:08Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "type": "application/astra-hookSource", "version": "1.0", "id": "282adc93-9df7-40e7-89d5-e120f525628d", "name": "exampleScript", "private": "false", "preloaded": "false", "sourceType": "script", "source": "IyEvYmluL2Jhc2gKZWNobyAidGhpcyBpcyBqdXN0IGFuIGV4YW1wbGUgdXBkYXRlIg==", "sourceMD5Checksum": "30978f9517ef027e7c6861e4cc1797ae"}
```
