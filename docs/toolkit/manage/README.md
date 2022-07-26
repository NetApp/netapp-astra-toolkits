# Manage (aka Define)

The `manage` argument allows you to manage a discovered [application](#app), or a currently unmanaged [cluster](#cluster).

```text
$ ./toolkit.py manage -h                
usage: toolkit.py manage [-h] {app,cluster} ...

optional arguments:
  -h, --help     show this help message and exit

objectType:
  {app,cluster}
    app          manage app
    cluster      manage cluster
```

## App

To define (or manage) an app, you must first gather the [namespace name](../list/README.md#namespaces) and [cluster ID](../list/README.md#clusters).  After an application is managed, it is recommended to [create a protectionpolicy](../create/README.md#protectionpolicy) for the app.

Command usage:

```text
./toolkit.py manage app <appLogicalName> <namespaceName> <clusterID>
```

Sample output:

```text
$ ./toolkit.py manage app wordpress wordpress b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{"type": "application/astra-app", "version": "2.0", "id": "40f27720-5e6d-4ab7-8647-cc05f2019319", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress"}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-25T14:21:48Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-25T14:21:48Z", "modificationTimestamp": "2022-07-25T14:21:48Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

## Cluster

To manage a cluster, you must gather the [cluster ID](../list/README.md#clusters), and a corresponding [storageclass ID](../list/README.md#storageclasses).  Command usage:

```text
./toolkit.py manage cluster <clusterID> <storageclassID>
```

Sample output:

```text
$ ./toolkit.py manage cluster 80d6bef8-300c-44bd-9e36-04ef874bdc29 \
    ba6d5a64-a321-4fd7-9842-9adce829229a
{"type": "application/astra-managedCluster", "version": "1.1", "id": "80d6bef8-300c-44bd-9e36-04ef874bdc29", "name": "aks-eastus-cluster", "state": "pending", "stateUnready": [], "managedState": "managed", "managedStateUnready": [], "managedTimestamp": "2022-05-19T20:33:59Z", "inUse": "false", "clusterType": "aks", "clusterVersion": "1.22", "clusterVersionString": "v1.22.6", "clusterCreationTimestamp": "0001-01-01T00:00:00Z", "namespaces": [], "defaultStorageClass": "ba6d5a64-a321-4fd7-9842-9adce829229a", "cloudID": "7b8d4252-293c-4c70-b101-7fd6b7d08e15", "credentialID": "04c067b2-df55-4d9c-8a3a-c869a779c276", "location": "eastus", "isMultizonal": "false", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/hasNonTridentCSIDriverSupport", "value": "true"}, {"name": "astra.netapp.io/labels/read-only/hasTridentDriverSupport", "value": "true"}, {"name": "astra.netapp.io/labels/read-only/azure/subscriptionID", "value": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxa2935"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "Azure"}], "creationTimestamp": "2022-05-19T20:33:59Z", "modificationTimestamp": "2022-05-19T20:34:03Z", "createdBy": "system"`
```
