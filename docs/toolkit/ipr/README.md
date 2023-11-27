# IPR

The `ipr` argument allows you to perform an in-place-restore of a [managed application](../manage/README.md#app) (that has at least one [snapshot](../create/README.md#snapshot) or [backup](../create/README.md#backup)) to a previous version.

**Note**: this command **replaces** the current running application without confirmation; if you do not wish to destroy the current app, please see the [clone](../clone/README.md) or [restore](../restore/README.md) commands.

The overall command usage is:

```text
actoolkit ipr  <app> (--backup <backup> | --snapshot <snapshot>) \
    [--filterSelection <include|exclude> --filterSelection <key1=val1 key2=val2>] --filterSelection <key3=val3>] \
    [--background | --pollTimer <integer>]
```

* [app](../list/README.md#apps): the app of the to-be-restored app, which can be gathered from the [list](../list/README.md) command
* **Only one** of the following two arguments must also be specified:
  * `--backup`: the [backup](../list/README.md#backups) used to perform the in-place-restore
  * `--snapshot`: the [snapshot](../list/README.md#snapshots) used to perform the in-place-restore
* **Neither or both** of the following resource filter group arguments must be specified to optionally clone a subset of resources:
  * `--filterSelection`: whether the filters should `include` or `exclude` resources from the cloned application
  * `--filterSet`: a set of `key=value` pair rules to filter the number of resources to be cloned. This argument can be specified any number of times, within a filter set a resource must match *all* filters (logical AND), but a resource only needs to match any single filter set to be included (logical OR). The `key` field must be one of 6 possible options:
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
actoolkit ipr a643b5dc-bfa0-4624-8bdd-5ad5325f20fd --snapshot 136c0d8e-d4a7-4034-a846-021f0afc0b2b
In-Place-Restore job in progress..................................Success!
```

When the optional `--background`/`-b` argument **is** specified, the command simply initiates the in-place-restore task, and leaves it to the user to validate the in-place-restore operation completion.

```text
$ actoolkit ipr -b a643b5dc-bfa0-4624-8bdd-5ad5325f20fd --backup 7be82451-7e89-43fb-8251-9a347ce513e0
In-Place-Restore job submitted successfully
Background flag selected, run 'list apps' to get status
$ actoolkit list apps
+-----------+--------------------------------------+-----------------+-------------+-----------+-----------+
| appName   | appID                                | clusterName     | namespace   | state     | source    |
+===========+======================================+=================+=============+===========+===========+
| wordpress | a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | useast1-cluster | wordpress   | restoring | namespace |
+-----------+--------------------------------------+-----------------+-------------+-----------+-----------+
```

## Resource Filters

To in-place-restore a subset of resources through filters, **both** the `--filterSelection` and `--filterSet` arguments must be provided. The `--filterSelection` argument must be either `include` or `exclude`. The `--filterSet` argument can be provided multiple times for any number of filter sets.

Within a single filter set, if specifying multiple `key=value` pairs (which are treated as logical AND), these pairs can be comma or space separated. To specify distinct sets of filters, the `--filterSet` argument should be specified again. The `key` must be one of 6 options:

* `namespace`: any number of namespaces (useful for multi-namespace apps)
* `name`: the name of a resource
* `label`: a Kubernetes [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
* `group`: the group of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `version`: the version of a GVK schema, must match an existing [app asset](../list/README.md#assets)
* `kind`: the kind of a GVK schema, must match an existing [app asset](../list/README.md#assets)

To in-place-restore only the persistent volumes of an application:

```text
$ actoolkit ipr 5391204b-9974-4f51-a052-b83e685f04e5 \
    --snapshot 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection include \
    --filterSet version=v1,kind=PersistentVolumeClaim
In-Place-Restore job in progress.......................Success!
```

To in-place-restore the entire application other than the secrets (perhaps an external secret manager is used):

```text
$ actoolkit ipr 5391204b-9974-4f51-a052-b83e685f04e5
    --snapshot 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection exclude \
    --filterSet version=v1 kind=Secret
In-Place-Restore job in progress......................Success!
```

To in-place-restore any `pod` which also has the label `app.kubernetes.io/name=wordpress` (logical AND due to using a single `--filterSet` argument):

```text
$ actoolkit ipr 5391204b-9974-4f51-a052-b83e685f04e5 \
    --snapshot 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection include \
    --filterSet version=v1,kind=Pod,label=app.kubernetes.io/name=wordpress
In-Place-Restore job in progress.......................Success!
```

To in-place-restore all `pods`, and any resource which has the label `app.kubernetes.io/name=wordpress` (logical OR due to using two `--filterSet` arguments):

```text
$ actoolkit ipr 5391204b-9974-4f51-a052-b83e685f04e5 \
    --snapshot 7a7f8293-7d32-427c-a896-7aae133c0603 --filterSelection include \
    --filterSet version=v1 kind=Pod --filterSet label=app.kubernetes.io/name=wordpress
In-Place-Restore job in progress......................Success!
```
