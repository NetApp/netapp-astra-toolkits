# Update

The `update` argument allows you to update an Astra resource, at this time only including:

* [Buckets](#bucket)
* [Clouds](#cloud)
* [Replications](#replication)

```text
$ ./toolkit.py update -h
usage: toolkit.py update [-h] {bucket,cloud,replication} ...

options:
  -h, --help            show this help message and exit

objectType:
  {bucket,cloud,replication}
    bucket              update bucket
    cloud               update cloud
    replication         update replication
```

## Bucket

The `update bucket` command allows you to update the credential of a managed [bucket](../manage/README.md#bucket).  The high level command usage is:

```text
./toolkit.py update <bucketID> <credentialGroupArgs>
```

The \<bucketID\> argument can be gathered from a [list buckets](../list/README.md#buckets) command.  The possible \<credentialGroupArgs\> are:

* `--credentialID`/`-c`: the **already existing** [credentialID](../list/README.md#credentials), or
* `--accessKey` and `--accessSecret`: to create a new credential which the bucket is then updated to use

Sample commands and output are as follows:

```text
$ ./toolkit.py update bucket 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac \
    --credentialID ad0754c4-08dd-4b68-b478-b4d2456968d3
{"type": "application/astra-bucket", "version": "1.0", "id": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "name": "astra-gcp-backup-fbe43be9aaa0", "state": "available", "credentialID": "ad0754c4-08dd-4b68-b478-b4d2456968d3", "provider": "gcp", "bucketParameters": {"gcp": {"bucketName": "astra-gcp-backup-fbe43be9aaa0"}}, "metadata": {"labels": [{"name": "astra.netapp.io/labels/internal/nautilusCreated", "value": "true"}], "creationTimestamp": "2022-04-28T19:05:53Z", "modificationTimestamp": "2023-02-07T19:03:21Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

```text
$ ./toolkit.py update bucket 266f3453-fef2-4f93-849b-a165a5625d25 \
    --accessKey accessKey1234567890 --accessSecret accessSecret1234567890
{"type": "application/astra-credential", "version": "1.1", "id": "03851a0d-c8cb-4550-83da-40cde27e530a", "name": "mhaigh-test-bucket", "keyType": "s3", "valid": "true", "metadata": {"creationTimestamp": "2023-02-07T19:08:55Z", "modificationTimestamp": "2023-02-07T19:08:55Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "s3"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "s3"}]}}
{"type": "application/astra-bucket", "version": "1.1", "id": "266f3453-fef2-4f93-849b-a165a5625d25", "name": "mhaigh-test-bucket", "state": "available", "credentialID": "03851a0d-c8cb-4550-83da-40cde27e530a", "provider": "gcp", "bucketParameters": {"gcp": {"bucketName": "mhaigh-test-bucket"}}, "metadata": {"creationTimestamp": "2023-02-06T20:19:58Z", "modificationTimestamp": "2023-02-07T19:08:55Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Cloud

The `update cloud` command allows you to update the credential and/or default bucket of a [cloud](../manage/README.md#cloud).  The high level command usage is:

```text
./toolkit.py update cloud <cloudID> <updateArg>
```

The \<cloudID\> argument can be gathered from a [list clouds](../list/README.md#clouds) command.  The other three possible commands are:

### Credential Path

To update the credentials of a cloud to a currently non-existing credential, use the `--credentialPath` argument to point at a local filesystem JSON credential object:

```text
./toolkit.py update cloud <cloudID> --credentialPath path/to/credentials.json
```

This command first creates the credential object, and then updates the cloud to reference the new credential ID:

```text
$ ./toolkit.py update cloud 0ec2e027-80bc-426a-b844-692de243b29e -c ~/gcp-astra-demo-3d7d.json
{"type": "application/astra-credential", "version": "1.1", "id": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "name": "astra-sa@GCP", "keyType": "generic", "valid": "true", "metadata": {"creationTimestamp": "2023-02-06T19:54:32Z", "modificationTimestamp": "2023-02-06T19:54:32Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "service-account"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "GCP"}]}}
{"type": "application/astra-cloud", "version": "1.0", "id": "0ec2e027-80bc-426a-b844-692de243b29e", "name": "GCP", "state": "running", "stateUnready": [], "cloudType": "GCP", "credentialID": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "defaultBucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "metadata": {"labels": [], "creationTimestamp": "2022-04-26T01:53:06Z", "modificationTimestamp": "2023-02-06T19:54:33Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Credential ID

To update the credentials of a cloud to a currently existing credential, use the `--credentialID` argument to reference an existing credentialID:

```text
./toolkit.py update cloud <cloudID> --credentialID <credentialID>
```

The \<credentialID\> value can be gathered from a [list credentials](../list/README.md#credentials) command.

```text
$ ./toolkit.py update cloud 0ec2e027-80bc-426a-b844-692de243b29e \
    --credentialID 8e6c9667-f2f2-40c2-92d0-38467f7f45be
{"type": "application/astra-cloud", "version": "1.0", "id": "0ec2e027-80bc-426a-b844-692de243b29e", "name": "GCP", "state": "running", "stateUnready": [], "cloudType": "GCP", "credentialID": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "defaultBucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "metadata": {"labels": [], "creationTimestamp": "2022-04-26T01:53:06Z", "modificationTimestamp": "2023-02-08T13:48:23Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Default Bucket

To change a cloud's default bucket for backups, run the following command:

```text
./toolkit.py update cloud <cloudID> --defaultBucketID <bucketID>
```

The \<bucketID\> can be gathered from a [list buckets](../list/README.md#buckets) command (the bucket must already be under [management](../manage/README.md#bucket)).

```text
$ ./toolkit.py update cloud 0ec2e027-80bc-426a-b844-692de243b29e --defaultBucketID 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac
{"type": "application/astra-cloud", "version": "1.0", "id": "0ec2e027-80bc-426a-b844-692de243b29e", "name": "GCP", "state": "running", "stateUnready": [], "cloudType": "GCP", "credentialID": "8e6c9667-f2f2-40c2-92d0-38467f7f45be", "defaultBucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "metadata": {"labels": [], "creationTimestamp": "2022-04-26T01:53:06Z", "modificationTimestamp": "2023-02-06T20:24:53Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Replication

The `update replication` command allows you to **failover**, **reverse**, or **resync** an existing [replication policy](../create/README.md#replication).  It is currently **only** supported for ACC environments.  The high level command usage is:

```text
./toolkit.py update replication <replicationID> <operation>
```

The \<replicationID\> argument can be gathered from a [list replications](../list/README.md#replications) command.

The \<operation\> keyword can be one of **failover**, **reverse**, or **resync**, as detailed below.

### Failover

The **failover** operation stops the replication relationship and brings the app online on the destination cluster. This procedure does not stop the app on the source cluster if it was operational.

```text
$ ./toolkit.py update replication 5dbb4893-373d-46be-a5ec-cbdbf65ac673 failover
{"type": "application/astra-appMirror", "version": "1.0", "id": "5dbb4893-373d-46be-a5ec-cbdbf65ac673", "namespaceMapping": [{"clusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaces": ["wordpress"]}, {"clusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaces": ["wordpress"]}], "state": "failingOver", "stateDesired": "failedOver", "stateDetails": [{"type": "https://astra.netapp.io/stateDetails/24", "title": "Snapshot replication completed", "detail": "A snapshot was replicated to the destination.", "additionalDetails": {"completionTime": "2022-09-20T18:07:03Z", "snapshotID": "037d315c-a40a-4e26-8624-1910f847137f", "startTime": "2022-09-20T18:05:43Z"}}], "transferState": "idle", "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-19T19:09:32Z", "modificationTimestamp": "2022-09-20T18:58:31Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444"}, "ReplicatedPVCs_": null}
Replication failover initiated
```

### Resync

The **resync** operation re-establishes the replication relationship. You can choose which data to retain through the `--dataSource`/`-s` argument and either the `clusterID` or `appID` of the side you wish to use as the replication source.

This operation re-establishes the SnapMirror relationships to start the volume replication in the direction of choice.  The process also stops the app on the new destination cluster before re-establishing replication.

```text
$ ./toolkit.py update replication 5dbb4893-373d-46be-a5ec-cbdbf65ac673 resync -s f3332e48-d175-4d6d-852f-bdee0f65a6fe
{"type": "application/astra-appMirror", "version": "1.0", "id": "5dbb4893-373d-46be-a5ec-cbdbf65ac673", "sourceAppID": "dbda1d21-76b2-4cad-bd92-f047e41453c7", "sourceClusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "destinationAppID": "1be8daef-816e-4d17-a449-14b03639dcd1", "destinationClusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaceMapping": [{"clusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaces": ["wordpress"]}, {"clusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaces": ["wordpress"]}], "state": "establishing", "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [], "transferState": "idle", "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-19T19:09:32Z", "modificationTimestamp": "2022-09-20T19:59:09Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444"}, "ReplicatedPVCs_": null}
Replication resync initiated
```

### Reverse

The **reverse** operation moves the application to the destination cluster while continuing to replicate back to the original source cluster. Astra Control stops the application on the source cluster and replicates the data to the destination before failing over the app to the destination cluster.

In this situation, you are swapping the source and destination. The original source cluster becomes the new destination cluster, and the original destination cluster becomes the new source cluster.

```text
$ ./toolkit.py update replication 5dbb4893-373d-46be-a5ec-cbdbf65ac673 reverse
{"type": "application/astra-appMirror", "version": "1.0", "id": "5dbb4893-373d-46be-a5ec-cbdbf65ac673", "sourceAppID": "1be8daef-816e-4d17-a449-14b03639dcd1", "sourceClusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "destinationAppID": "dbda1d21-76b2-4cad-bd92-f047e41453c7", "destinationClusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaceMapping": [{"clusterID": "0c00ddc3-4a80-45f9-8dd7-c8885153ad02", "namespaces": ["wordpress"]}, {"clusterID": "f3332e48-d175-4d6d-852f-bdee0f65a6fe", "namespaces": ["wordpress"]}], "state": "establishing", "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [{"type": "https://astra.netapp.io/stateDetails/24", "title": "Snapshot replication completed", "detail": "A snapshot was replicated to the destination.", "additionalDetails": {"completionTime": "2022-09-20T20:07:05Z", "snapshotID": "1a5fc936-4f21-4e27-8081-d17155f50453", "startTime": "2022-09-20T20:05:44Z"}}], "transferState": "idle", "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-19T19:09:32Z", "modificationTimestamp": "2022-09-20T20:18:44Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444"}, "ReplicatedPVCs_": null}
Replication reverse initiated
```
