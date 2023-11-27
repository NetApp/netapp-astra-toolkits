# Restore

The `restore` argument allows you to restore a [managed application](../manage/README.md#app) to a destination [cluster](..list/README.md#clusters) of your choice.  You may restore from an existing [backup](../list/README.md#backups) or [snapshot](../list/README.md#snapshots).

To copy a running application, please see the [clone](../clone/README.md) command. To perform an in-place-restore (which is a destructive action), please see the [ipr](../ipr/README.md) command.

After restoring an application, it is recommended to [create a protection policy](../create/README.md#protectionpolicy) for the new application.

The overall command usage is:

```text
actoolkit restore <restoreSource> <appName> <cluster> \
    [--newStorageClass <newStorageClass>] \
    [--newNamespace <newNamespace> | --multiNsMapping <sourcens1=destns1, sourcens2=destns2>] \
    [--filterSelection <include|exclude> --filterSelection <key1=val1 key2=val2>] --filterSelection <key3=val3>] \
    [--background | --pollTimer <integer>]
```

* `restoreSource`: the backup or snapshot to use as the source for the new app
* `appName`: the name of the new application
* `cluster`: the destination cluster (it can be any cluster manged by Astra Control)
* `--newStorageClass`: optionally provide a new storage class (must be available on the specified `cluster`) for the new application
* **Only one or zero** of the following arguments can be specified (if neither are specified, the single namespace is the same value as `appName`):
  * `--newNamespace`: for single-namespace apps, the name of the new namespace
  * `--multiNsMapping`: for multi-namespace apps, specify matching number of sourcens1=destns1 mappings (the number and name of namespace mappings must match the source app)
* **Neither or both** of the following resource filter group arguments must be specified to optionally restore a subset of resources:
  * `--filterSelection`: whether the filters should `include` or `exclude` resources from the restored application
  * `--filterSet`: a set of `key=value` pair rules to filter the number of resources to be restored. This argument can be specified any number of times, within a filter set a resource must match *all* filters (logical AND), but a resource only needs to match any single filter set to be included (logical OR). The `key` field must be one of 6 possible options:
    * `namespace`: any number of namespaces (useful for multi-namespace apps)
    * `name`: the name of a resource
    * `label`: a Kubernetes [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
    * `group`: the group of a GVK schema, must match an existing [app asset](../list/README.md#assets)
    * `version`: the version of a GVK schema, must match an existing [app asset](../list/README.md#assets)
    * `kind`: the kind of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* Either of the following two arguments can be specified to modify the default mechanism which polls for the status of the restore operation every 5 seconds and reports back once complete:
  * `--background`/`-b`: initiate the restore task, and then leaves it to the user to validate completion
  * `--pollTimer`/`-t`: optionally specify how frequently (in seconds) to poll the operation status (default: 5 seconds)

Sample usage:

```text
$ actoolkit restore 9ef2fdc5-1f15-423c-ba57-b14af0f0b0e4 wordpress-fg 1a6242c8-b46c-431a-a5f8-584c4e4d7011
{"type": "application/astra-app", "version": "2.2", "id": "18d9e8c4-67ee-42e2-8647-c290bd0f3f25", ...
Submitting restore succeeded.
Waiting for restore to become available....................restoring operation complete.
```

```text
$ actoolkit restore -b 3eca3353-366b-4e86-be77-90f52d4e3ff1 wordpress-bg 1a6242c8-b46c-431a-a5f8-584c4e4d7011
{"type": "application/astra-app", "version": "2.2", "id": "9107cc78-525e-4b2b-9122-3504ce4d2115", ...
Submitting restore succeeded.
Background restore flag selected, run 'list apps' to get status.
$ actoolkit list apps
+--------------+--------------------------------------+--------------------+-----------+--------------+
| appName      | appID                                | clusterName        | namespace | state        |
+==============+======================================+====================+===========+==============+
| wordpress    | f24ac04c-e476-4089-9475-686848457587 | uscentral1-cluster | wordpress | ready        |
+--------------+--------------------------------------+--------------------+-----------+--------------+
| wordpress-bg | 9107cc78-525e-4b2b-9122-3504ce4d2115 | uscentral1-cluster |           | provisioning |
+--------------+--------------------------------------+--------------------+-----------+--------------+
```

## Namespace Mappings

### Single-Namespace Apps

Per the examples above, omitting `--newNamespace` results in the new app being created in a namespace that matches the `appName` value.  If a different namespace is desired, specify that value with `--newNamespace`:

```text
$ actoolkit restore -b 0d96b454-ed5f-4d9b-827f-63b75ffc14ef wordpress-new 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --newNamespace wordpress-dr
{"type": "application/astra-app", "version": "2.2", "id": "b76ee991-dc9c-4d0c-aca2-3f12013bbbc8", ...
Submitting restore succeeded.
Background restore flag selected, run 'list apps' to get status.
$ actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| wordpress       | 090019ce-6e54-4635-85d6-4727ee1fe125 | prod-cluster  | wordpress            | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| wordpress-new   | b76ee991-dc9c-4d0c-aca2-3f12013bbbc8 | dr-cluster    | wordpress-dr         | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```

### Multi-Namespace Apps

For multi-namespace apps, the `--multiNsMapping` argument **must** be provided.  The number of namespace mappings must match the number of namespaces on the source app, they must be of the `sourcenamespace=destnamespace` format, and `sourcenamespace` must be present within the source app definition.

Either separating the arguments with a space, or specifying multiple flags are both supported:

```text
$ actoolkit restore -b a0480785-9d77-4df8-a671-5007303c3736 example-restore 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --multiNsMapping sourcens1=destns1 sourcens2=destns2
{"type": "application/astra-app", "version": "2.2", "id": "3d998134-7a4b-42f0-9065-98650e7a2799", ...
Submitting restore succeeded.
Background restore flag selected, run 'list apps' to get status.
$ actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| example-app     | b94f474d-da0e-4f7e-b52b-9271fae78e0c | prod-cluster  | sourcens1, sourcens2 | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| example-restore | 3d998134-7a4b-42f0-9065-98650e7a2799 | dr-cluster    | destns1, destns2     | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```

```text
$ actoolkit restore -b 05ff6f45-fac4-4b31-a023-c09624f99b15 example-restore 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --multiNsMapping sourcens1=destns1 --multiNsMapping sourcens2=destns2
{"type": "application/astra-app", "version": "2.2", "id": "9b081642-a695-4cec-b17c-2193b0aea55d", ...
Submitting restore succeeded.
Background restore flag selected, run 'list apps' to get status.
$ actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| example-app     | b94f474d-da0e-4f7e-b52b-9271fae78e0c | prod-cluster  | sourcens1, sourcens2 | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| example-restore | 9b081642-a695-4cec-b17c-2193b0aea55d | dr-cluster    | destns1, destns2     | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```

## Resource Filters

To restore a subset of resources through filters, **both** the `--filterSelection` and `--filterSet` arguments must be provided. The `--filterSelection` argument must be either `include` or `exclude`. The `--filterSet` argument can be provided multiple times for any number of filter sets.

Within a single filter set, if specifying multiple `key=value` pairs (which are treated as logical AND), these pairs can be comma or space separated. To specify distinct sets of filters, the `--filterSet` argument should be specified again. The `key` must be one of 6 options:

* `namespace`: any number of namespaces (useful for multi-namespace apps)
* `name`: the name of a resource
* `label`: a Kubernetes [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
* `group`: the group of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `version`: the version of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `kind`: the kind of a GVK schema, must match an existing [app asset](../list/README.md#assets)

To restore only the persistent volumes of an application:

```text
$ actoolkit restore -b 294cc14e-2d39-4286-9fb9-f325963e3c53 wordpress-restore c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection include --filterSet version=v1,kind=PersistentVolumeClaim
{"type": "application/astra-app", "version": "2.2", "id": "3d60a9e5-d235-42ba-a7e6-147e4b3ec6c9", ...
Submitting restore succeeded.
Background restore flag selected, run 'list apps' to get status.
```

To restore the entire application other than the secrets (perhaps an external secret manager is used):

```text
$ actoolkit restore d4b3be8c-9b28-4cc3-ad0b-e58a67e132eb cassandra-restore c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection exclude --filterSet version=v1 kind=Secret
{"type": "application/astra-app", "version": "2.2", "id": "a6bb7e82-1275-4b79-a18f-1525ae2d3555", ...
Submitting restore succeeded.
Waiting for restore to become available..................restoring operation complete.
```

To restore any `pod` which also has the label `app.kubernetes.io/name=wordpress` (logical AND due to using a single `--filterSet` argument):

```text
$ actoolkit restore 42a8431e-2e41-47a0-9912-e34843a47720 wordpress-l-and c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection include --filterSet version=v1,kind=Pod,label=app.kubernetes.io/name=wordpress
{"type": "application/astra-app", "version": "2.2", "id": "2060ae94-c006-461b-9a2c-a9e16534fed5", ...
Submitting restore succeeded.
Waiting for restore to become available....................restoring operation complete.
```

To restore all `pods`, and any resource which has the label `app.kubernetes.io/name=wordpress` (logical OR due to using two `--filterSet` arguments):

```text
$ actoolkit restore 42a8431e-2e41-47a0-9912-e34843a47720 wordpress-l-or c5a86c5b-9dc8-4709-8897-61c20fdb8d8c \
    --filterSelection include --filterSet version=v1 kind=Pod --filterSet label=app.kubernetes.io/name=wordpress
{"type": "application/astra-app", "version": "2.2", "id": "ba6ce35c-58f3-4873-b24d-ff656b507bd9", ...
Submitting restore succeeded.
Waiting for restore to become available.......................restoring operation complete.
```
