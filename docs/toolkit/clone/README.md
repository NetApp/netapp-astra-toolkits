# Clone

The `clone` argument allows you to clone a [managed application](../manage/README.md#app) to a destination [cluster](..list/README.md#clusters) of your choice.  You may clone from an existing [backup](../list/README.md#backups) or [snapshot](../list/README.md#snapshots), or directly from the running application.

After cloning an application, it is recommended to [create a protection policy](../create/README.md#protectionpolicy) for the new application.

The overall command usage is:

```text
actoolkit clone [<optionalBackgroundArg>] --cloneAppName <cloneAppName> \
    --clusterID <destClusterID> [--cloneStorageClass <cloneStorageClass>] \
    [--cloneNamespace <cloneNamespace> | --multiNsMapping <sourcens1=destns1, sourcens2=destns2>] \
    (--backupID <backupID> | --snapshotID <snapshotID> | --sourceAppID <sourceAppID>) \
    [--pollTimer <seconds>] [--filterSelection <include|exclude>] \
    [--filterSelection <key1=value1 key2=value2>] [--filterSelection <key3=value3>]
```

* `--cloneAppName`: the name of the new application
* `--clusterID`: the destination clusterID (it can be any cluster manged by Astra Control)
* **Only one or zero** of the following arguments can be specified (if neither are specified, the single namespace is the same value as `cloneAppName`):
  * `--cloneNamespace`: for single-namespace apps, the name of the new namespace
  * `--multiNsMapping`: for multi-namespace apps, specify matching number of sourcens1=destns1 mappings (the number and name of namespace mappings must match the source app)
* `--cloneStorageClass`: optionally provide a new storage class (must be available on the specified `clusterID`) for the new application
* **Only one** of the following arguments must also be specified:
  * `--backupID`: the backupID to create the clone from
  * `--snapshotID`: the snapshotID to create the clone from
  * `--sourceAppID`: a [managed application ID](../manage/README.md#app) (the clone will be created from the running application)
* `--pollTimer`: optionally specify how frequently (in seconds) to poll the operation status (default: 5 seconds)
* **Neither or both** of the following resource filter group arguments must be specified to optionally clone a subset of resources:
  * `--filterSelection`: whether the filters should `include` or `exclude` resources from the cloned application
  * `--filterSet`: a set of `key=value` pair rules to filter the number of resources to be cloned. This argument can be specified any number of times, within a filter set a resource must match *all* filters (logical AND), but a resource only needs to match any single filter set to be included (logical OR). The `key` field must be one of 6 possible options:
    * `namespace`: any number of namespaces (useful for multi-namespace apps)
    * `name`: the name of a resource
    * `label`: a Kubernetes [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
    * `group`: the group of a GVK schema, must match an existing [app asset](../list/README.md#assets)
    * `version`: the version of a GVK schema, must match an existing [app asset](../list/README.md#assets)
    * `kind`: the kind of a GVK schema, must match an existing [app asset](../list/README.md#assets)

When the optional `--background`/`-b` argument is **not** specified, the command polls for the status of the clone operation every 5 seconds (which can be overridden by the `--pollTimer`/`-t` argument), and reports back once complete.

```text
$ actoolkit clone --cloneAppName myclonedapp --clusterID af0aecb9-9b18-473f-b417-54fb38e1e28d \
    --snapshotID 8e4fafc8-9175-4f47-94b9-181ea435f60c
Submitting clone succeeded.
Waiting for clone to become available..............................................................\
..........Cloning operation complete.
```

When the optional `--background`/`-b` argument **is** specified, the command simply initiates the clone task, and leaves it to the user to validate the clone operation completion.

```text
$ actoolkit clone -b --cloneAppName bgcloneapp --clusterID b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d \
    --sourceAppID f24ac04c-e476-4089-9475-686848457587
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
$ actoolkit list apps
+------------+--------------------------------------+--------------------+-----------+--------------+
| appName    | appID                                | clusterName        | namespace | state        |
+============+======================================+====================+===========+==============+
| cassandra  | e494a651-fc80-492e-bca8-5d901047c53f | aks-eastus-cluster | cassandra | ready        |
+------------+--------------------------------------+--------------------+-----------+--------------+
| wordpress  | f24ac04c-e476-4089-9475-686848457587 | uscentral1-cluster | wordpress | ready        |
+------------+--------------------------------------+--------------------+-----------+--------------+
| bgcloneapp | 8cd0718f-098b-4978-b692-0126f678dc25 | uscentral1-cluster |           | provisioning |
+------------+--------------------------------------+--------------------+-----------+--------------+
```

The `clone` argument also features an interactive wizard which promts the user for any arguments not specified in the original command (outside of one of `--backupID`, `--snapshotID`, or `--sourceAppID` being required):

```text
$ actoolkit clone -b --backupID e4436f2f-a973-4c5e-b235-f325c54926db
App name for the clone: prompt-clone
Select destination cluster for the clone
Index   ClusterID                               clusterName         clusterPlatform
1:      af0aecb9-9b18-473f-b417-54fb38e1e28d    aks-eastus-cluster  aks
2:      b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d    uscentral1-cluster  gke
Select a line (1-2): 1
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
$ actoolkit list apps
+--------------+--------------------------------------+--------------------+-----------+--------------+
| appName      | appID                                | clusterName        | namespace | state        |
+==============+======================================+====================+===========+==============+
| cassandra    | e494a651-fc80-492e-bca8-5d901047c53f | aks-eastus-cluster | cassandra | ready        |
+--------------+--------------------------------------+--------------------+-----------+--------------+
| wordpress    | f24ac04c-e476-4089-9475-686848457587 | uscentral1-cluster | wordpress | ready        |
+--------------+--------------------------------------+--------------------+-----------+--------------+
| prompt-clone | 1f000f0a-ca24-4b27-ad48-c64ddc67836b | aks-eastus-cluster |           | provisioning |
+--------------+--------------------------------------+--------------------+-----------+--------------+
```

## Namespace Mappings

### Single-Namespace Apps

Per the examples above, omitting `--cloneNamespace` results in the clone being created in a namespace that matches the `--cloneAppName` value.  If a different namespace is desired, specify that value with `--cloneNamespace`:

```text
$ actoolkit clone -b --cloneAppName wordpress-clone --cloneNamespace wordpress-dr \
    --clusterID 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --sourceAppID 090019ce-6e54-4635-85d6-4727ee1fe125
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
$ actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| wordpress       | 090019ce-6e54-4635-85d6-4727ee1fe125 | prod-cluster  | wordpress            | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| wordpress-clone | b76ee991-dc9c-4d0c-aca2-3f12013bbbc8 | dr-cluster    | wordpress-dr         | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```

### Multi-Namespace Apps

For multi-namespace apps, the `--multiNsMapping` argument **must** be provided.  The number of namespace mappings must match the number of namespaces on the source app, they must be of the `sourcenamespace=destnamespace` format, and `sourcenamespace` must be present within the source app definition.

Either separating the arguments with a space, or specifying multiple flags are both supported:

```text
$ actoolkit clone -b --cloneAppName example-clone \
    --clusterID 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --sourceAppID b94f474d-da0e-4f7e-b52b-9271fae78e0c \
    --multiNsMapping sourcens1=destns1 sourcens2=destns2
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
$ actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| example-app     | b94f474d-da0e-4f7e-b52b-9271fae78e0c | prod-cluster  | sourcens1, sourcens2 | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| example-clone   | 3d998134-7a4b-42f0-9065-98650e7a2799 | dr-cluster    | destns1, destns2     | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```

```text
$ actoolkit clone -b --cloneAppName example-clone \
    --clusterID 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --sourceAppID b94f474d-da0e-4f7e-b52b-9271fae78e0c \
    --multiNsMapping sourcens1=destns1 --multiNsMapping sourcens2=destns2
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
$ actoolkit list apps
actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| example-app     | b94f474d-da0e-4f7e-b52b-9271fae78e0c | prod-cluster  | sourcens1, sourcens2 | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| example-clone   | 9b081642-a695-4cec-b17c-2193b0aea55d | dr-cluster    | destns1, destns2     | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```

## Resource Filters

To clone a subset of resources through filters, **both** the `--filterSelection` and `--filterSet` arguments must be provided. The `--filterSelection` argument must be either `include` or `exclude`. The `--filterSet` argument can be provided multiple times for any number of filter sets.

*Note*: resource filters can only be used to clone from a snapshot or backup, not a live clone of the running app.

Within a single filter set, if specifying multiple `key=value` pairs (which are treated as logical AND), these pairs can be comma or space separated. To specify distinct sets of filters, the `--filterSet` argument should be specified again. The `key` must be one of 6 options:

* `namespace`: any number of namespaces (useful for multi-namespace apps)
* `name`: the name of a resource
* `label`: a Kubernetes [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
* `group`: the group of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `version`: the version of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `kind`: the kind of a GVK schema, must match an existing [app asset](../list/README.md#assets)

To clone only the persistent volumes of an application:

```text
$ actoolkit clone -b --cloneAppName wordpress-clone \
    --snapshotID 294cc14e-2d39-4286-9fb9-f325963e3c53 --clusterID c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection include --filterSet version=v1,kind=PersistentVolumeClaim
{"type": "application/astra-app", "version": "2.2", "id": "3d60a9e5-d235-42ba-a7e6-147e4b3ec6c9", "name": "wordpress-clone", "namespaceScopedResources": [{"namespace": "wordpress-clone", "labelSelectors": []}], "state": "provisioning", "lastResourceCollectionTimestamp": "2023-04-25T19:49:24Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "namespaceMapping": [{"source": "wordpress", "destination": "wordpress-clone"}], "clusterName": "gke-uscentral1-cluster", "clusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "clusterType": "gke", "sourceClusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "backupID": "146618ae-15f0-4474-8c0c-dc97b41b0fa1", "snapshotID": "294cc14e-2d39-4286-9fb9-f325963e3c53", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/appType", "value": "clone"}], "creationTimestamp": "2023-04-25T19:49:24Z", "modificationTimestamp": "2023-04-25T19:49:24Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "restoreFilter": {"resourceSelectionCriteria": "include", "GVKN": [{"kind": "PersistentVolumeClaim", "version": "v1"}]}, "links": [{"rel": "canonical", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v2/managedClusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/apps/3d60a9e5-d235-42ba-a7e6-147e4b3ec6c9"}, {"rel": "collection", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v1/clouds/0ec2e027-80bc-426a-b844-692de243b29e/clusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/namespaces/00000000-0000-0000-0000-000000000000/apps"}]}
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
```

To clone the entire application other than the secrets (perhaps an external secret manager is used):

```text
$ actoolkit clone --cloneAppName cassandra-clone \
    --snapshotID d4b3be8c-9b28-4cc3-ad0b-e58a67e132eb --clusterID c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection exclude --filterSet version=v1 kind=Secret
{"type": "application/astra-app", "version": "2.2", "id": "a6bb7e82-1275-4b79-a18f-1525ae2d3555", "name": "cassandra-clone", "namespaceScopedResources": [{"namespace": "cassandra-clone", "labelSelectors": []}], "state": "provisioning", "lastResourceCollectionTimestamp": "2023-04-25T21:11:23Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "namespaceMapping": [{"source": "cassandra", "destination": "cassandra-clone"}], "clusterName": "gke-uscentral1-cluster", "clusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "clusterType": "gke", "sourceClusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "backupID": "80a61a95-a446-42be-9aac-4b073f60b5a3", "snapshotID": "d4b3be8c-9b28-4cc3-ad0b-e58a67e132eb", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/appType", "value": "clone"}], "creationTimestamp": "2023-04-25T21:11:23Z", "modificationTimestamp": "2023-04-25T21:11:23Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "restoreFilter": {"resourceSelectionCriteria": "exclude", "GVKN": [{"kind": "Secret", "version": "v1"}]}, "links": [{"rel": "canonical", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v2/managedClusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/apps/a6bb7e82-1275-4b79-a18f-1525ae2d3555"}, {"rel": "collection", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v1/clouds/0ec2e027-80bc-426a-b844-692de243b29e/clusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/namespaces/00000000-0000-0000-0000-000000000000/apps"}]}
Submitting clone succeeded.
Waiting for clone to become available.....Cloning operation complete.
```

To clone any `pod` which also has the label `app.kubernetes.io/name=wordpress` (logical AND due to using a single `--filterSet` argument):

```text
$ actoolkit clone --cloneAppName wordpress-l-and \
    --backupID 42a8431e-2e41-47a0-9912-e34843a47720 --clusterID c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection include --filterSet version=v1,kind=Pod,label=app.kubernetes.io/name=wordpress
{"type": "application/astra-app", "version": "2.2", "id": "2060ae94-c006-461b-9a2c-a9e16534fed5", "name": "wordpress-l-and", "namespaceScopedResources": [{"namespace": "wordpress-l-and", "labelSelectors": []}], "state": "provisioning", "lastResourceCollectionTimestamp": "2023-04-26T13:25:14Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "namespaceMapping": [{"source": "wordpress", "destination": "wordpress-l-and"}], "clusterName": "gke-uscentral1-cluster", "clusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "clusterType": "gke", "sourceClusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "backupID": "42a8431e-2e41-47a0-9912-e34843a47720", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/appType", "value": "clone"}], "creationTimestamp": "2023-04-26T13:25:13Z", "modificationTimestamp": "2023-04-26T13:25:14Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "restoreFilter": {"resourceSelectionCriteria": "include", "GVKN": [{"kind": "Pod", "version": "v1", "labelSelectors": ["app.kubernetes.io/name=wordpress"]}]}, "links": [{"rel": "canonical", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v2/managedClusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/apps/2060ae94-c006-461b-9a2c-a9e16534fed5"}, {"rel": "collection", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v1/clouds/0ec2e027-80bc-426a-b844-692de243b29e/clusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/namespaces/00000000-0000-0000-0000-000000000000/apps"}]}
Submitting clone succeeded.
Waiting for clone to become available...........Cloning operation complete.
```

To clone all `pods`, and any resource which has the label `app.kubernetes.io/name=wordpress` (logical OR due to using two `--filterSet` arguments):

```text
$ actoolkit clone --cloneAppName wordpress-l-or \
    --backupID 42a8431e-2e41-47a0-9912-e34843a47720 --clusterID c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection include --filterSet version=v1 kind=Pod --filterSet label=app.kubernetes.io/name=wordpress
{"type": "application/astra-app", "version": "2.2", "id": "ba6ce35c-58f3-4873-b24d-ff656b507bd9", "name": "wordpress-l-or", "namespaceScopedResources": [{"namespace": "wordpress-l-or", "labelSelectors": []}], "state": "provisioning", "lastResourceCollectionTimestamp": "2023-04-26T13:39:50Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "namespaceMapping": [{"source": "wordpress", "destination": "wordpress-l-or"}], "clusterName": "gke-uscentral1-cluster", "clusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "clusterType": "gke", "sourceClusterID": "c5a86c5b-9dc8-4709-8897-61c20fdb8d8c", "backupID": "42a8431e-2e41-47a0-9912-e34843a47720", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/appType", "value": "clone"}], "creationTimestamp": "2023-04-26T13:39:49Z", "modificationTimestamp": "2023-04-26T13:39:50Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "restoreFilter": {"resourceSelectionCriteria": "include", "GVKN": [{"kind": "Pod", "version": "v1"}, {"labelSelectors": ["app.kubernetes.io/name=wordpress"]}]}, "links": [{"rel": "canonical", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v2/managedClusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/apps/ba6ce35c-58f3-4873-b24d-ff656b507bd9"}, {"rel": "collection", "href": "/accounts/fc018f3d-e807-4fa7-98d5-fbe43be9aaa0/topology/v1/clouds/0ec2e027-80bc-426a-b844-692de243b29e/clusters/c5a86c5b-9dc8-4709-8897-61c20fdb8d8c/namespaces/00000000-0000-0000-0000-000000000000/apps"}]}
Submitting clone succeeded.
Waiting for clone to become available............Cloning operation complete.
```
