# Clone

The `clone` argument allows you to live clone a [managed application](../manage/README.md#app) to a destination [cluster](..list/README.md#clusters) of your choice.

To restore an application from an existing backup or snapshot, please see the [restore](../restore/README.md) command. To perform an in-place-restore (which is a destructive action), please see the [ipr](../ipr/README.md) command.

After cloning an application, it is recommended to [create a protection policy](../create/README.md#protectionpolicy) for the new application.

The overall command usage is:

```text
actoolkit clone <sourceApp> <appName> <cluster> \
    [--newStorageClass <newStorageClass>] \
    [--newNamespace <newNamespace> | --multiNsMapping <sourcens1=destns1, sourcens2=destns2>] \
    [--background | --pollTimer <integer>]
```

* `sourceApp`: the running app to use as the source for the new app
* `appName`: the name of the new application
* `cluster`: the destination cluster (it can be any cluster manged by Astra Control)
* `--newStorageClass`: optionally provide a new storage class (must be available on the specified `cluster`) for the new application
* **Only one or zero** of the following arguments can be specified (if neither are specified, the single namespace is the same value as `appName`):
  * `--newNamespace`: for single-namespace apps, the name of the new namespace
  * `--multiNsMapping`: for multi-namespace apps, specify matching number of sourcens1=destns1 mappings (the number and name of namespace mappings must match the source app)
* Either of the following two arguments can be specified to modify the default mechanism which polls for the status of the clone operation every 5 seconds and reports back once complete:
  * `--background`/`-b`: initiate the clone task, and then leaves it to the user to validate completion
  * `--pollTimer`/`-t`: optionally specify how frequently (in seconds) to poll the operation status (default: 5 seconds)

Sample usage:

```text
$ actoolkit clone 9ef2fdc5-1f15-423c-ba57-b14af0f0b0e4 wordpress-fg 1a6242c8-b46c-431a-a5f8-584c4e4d7011
{"type": "application/astra-app", "version": "2.2", "id": "18d9e8c4-67ee-42e2-8647-c290bd0f3f25", ...
Submitting clone succeeded.
Waiting for clone to become available....................cloning operation complete.
```

```text
$ actoolkit clone -b 3eca3353-366b-4e86-be77-90f52d4e3ff1 wordpress-bg 1a6242c8-b46c-431a-a5f8-584c4e4d7011
{"type": "application/astra-app", "version": "2.2", "id": "9107cc78-525e-4b2b-9122-3504ce4d2115", ...
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
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
$ actoolkit clone -b 090019ce-6e54-4635-85d6-4727ee1fe125 wordpress-new 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --newNamespace wordpress-dr
{"type": "application/astra-app", "version": "2.2", "id": "b76ee991-dc9c-4d0c-aca2-3f12013bbbc8", ...
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
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
$ actoolkit clone -b b94f474d-da0e-4f7e-b52b-9271fae78e0c example-clone 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --multiNsMapping sourcens1=destns1 sourcens2=destns2
{"type": "application/astra-app", "version": "2.2", "id": "3d998134-7a4b-42f0-9065-98650e7a2799", ...
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
$ actoolkit clone -b b94f474d-da0e-4f7e-b52b-9271fae78e0c example-clone 47dfb3d2-1b53-45e7-b26d-c0e51af5de5a \
    --multiNsMapping sourcens1=destns1 --multiNsMapping sourcens2=destns2
{"type": "application/astra-app", "version": "2.2", "id": "9b081642-a695-4cec-b17c-2193b0aea55d", ...
Submitting clone succeeded.
Background clone flag selected, run 'list apps' to get status.
$ actoolkit list apps
+-----------------+--------------------------------------+---------------+----------------------+---------+
| appName         | appID                                | clusterName   | namespace            | state   |
+=================+======================================+===============+======================+=========+
| example-app     | b94f474d-da0e-4f7e-b52b-9271fae78e0c | prod-cluster  | sourcens1, sourcens2 | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
| example-clone   | 9b081642-a695-4cec-b17c-2193b0aea55d | dr-cluster    | destns1, destns2     | ready   |
+-----------------+--------------------------------------+---------------+----------------------+---------+
```
