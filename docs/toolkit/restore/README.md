# Restore

The `restore` argument allows you to perform an in-place restore of a [managed application](../manage/README.md#app) (that has at least one [snapshot](../create/README.md#snapshot) or [backup](../create/README.md#backup)) to a previous version.

**Note**: this command **replaces** the current running application without confirmation; if you do not wish to destroy the current app, please see the [clone command](../clone/README.md).

The overall command usage is:

```text
./toolkit.py restore [<optionalBackgroundArg>] <appID> \
    (--backupID <backupID> | --snapshotID <snapshotID>) \
    [--pollTimer <seconds>] [--filterSelection <include|exclude>] \
    [--filterSelection <key1=value1 key2=value2>] [--filterSelection <key3=value3>]
```

* [appID](../list/README.md#apps): the appID of the to-be-restored app, which can be gathered from the [list](../list/README.md) command
* **Only one** of the following two arguments must also be specified:
  * `--backupID`: the [backupID](../list/README.md#backups) used to perform the in-place restore
  * `--snapshotID`: the [snapshotID](../list/README.md#snapshots) used to perform the in-place restore
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

When the optional `--background`/`-b` argument is **not** specified, the command polls for the status of the restore operation every 5 seconds (which can be overridden by the `--pollTimer`/`-t` argument), and reports back once complete.

```text
./toolkit.py restore a643b5dc-bfa0-4624-8bdd-5ad5325f20fd \
    --snapshotID 136c0d8e-d4a7-4034-a846-021f0afc0b2b
Restore job in progress.....................................Success!
```

When the optional `--background`/`-b` argument **is** specified, the command simply initiates the restore task, and leaves it to the user to validate the restore operation completion.

```text
$ ./toolkit.py restore -b a643b5dc-bfa0-4624-8bdd-5ad5325f20fd \
    --backupID 7be82451-7e89-43fb-8251-9a347ce513e0
Restore job submitted successfully
Background restore flag selected, run 'list apps' to get status
$ ./toolkit.py list apps
+-----------+--------------------------------------+-----------------+-------------+-----------+-----------+
| appName   | appID                                | clusterName     | namespace   | state     | source    |
+===========+======================================+=================+=============+===========+===========+
| wordpress | a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | useast1-cluster | wordpress   | restoring | namespace |
+-----------+--------------------------------------+-----------------+-------------+-----------+-----------+
```

## Resource Filters

To in-place restore a subset of resources through filters, **both** the `--filterSelection` and `--filterSet` arguments must be provided. The `--filterSelection` argument must be either `include` or `exclude`. The `--filterSet` argument can be provided multiple times for any number of filter sets.

Within a single filter set, if specifying multiple `key=value` pairs (which are treated as logical AND), these pairs can be comma or space separated. To specify distinct sets of filters, the `--filterSet` argument should be specified again. The `key` must be one of 6 options:

* `namespace`: any number of namespaces (useful for multi-namespace apps)
* `name`: the name of a resource
* `label`: a Kubernetes [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
* `group`: the group of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `version`: the version of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `kind`: the kind of a GVK schema, must match an existing [app asset](../list/README.md#assets)

To in-place restore only the persistent volumes of an application:

```text
$ ./toolkit.py restore 5391204b-9974-4f51-a052-b83e685f04e5 \
    --snapshotID 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection include \
    --filterSet version=v1,kind=PersistentVolumeClaim
Restore job in progress.......................Success!
```

To in-place restore the entire application other than the secrets (perhaps an external secret manager is used):

```text
$ ./toolkit.py restore 5391204b-9974-4f51-a052-b83e685f04e5
    --snapshotID 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection exclude \
    --filterSet version=v1 kind=Secret
Restore job in progress......................Success!
```

To in-place restore any `pod` which also has the label `app.kubernetes.io/name=wordpress` (logical AND due to using a single `--filterSet` argument):

```text
$ ./toolkit.py restore 5391204b-9974-4f51-a052-b83e685f04e5 \
    --snapshotID 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection include \
    --filterSet version=v1,kind=Pod,label=app.kubernetes.io/name=wordpress
Restore job in progress.......................Success!
```

To in-place restore all `pods`, and any resource which has the label `app.kubernetes.io/name=wordpress` (logical OR due to using two `--filterSet` arguments):

```text
$ ./toolkit.py restore 5391204b-9974-4f51-a052-b83e685f04e5 \
    --snapshotID 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection include \
    --filterSet version=v1 kind=Pod --filterSet label=app.kubernetes.io/name=wordpress
Restore job in progress......................Success!
```
