# Update

The `update` argument allows you to update an Astra resource, at this time only including:

* [Replications](#replication)

```text
$ ./toolkit.py update -h
usage: toolkit.py update [-h] {replication} ...

optional arguments:
  -h, --help     show this help message and exit

objectType:
  {replication}
    replication  update replication
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
