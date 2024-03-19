# NetApp Astra Control SDK Docs

## Installation and Configuration

See [the main README](../README.md) for information on how to install the NetApp Astra Control SDK, and/or the following videos:

* [Python SDK Installation](https://www.youtube.com/watch?v=r6lBQ2I7O7M)
* [Astra Control API Credentials](https://www.youtube.com/watch?v=o-q-q_41A5A)

## Astra SDK Classes

High level overview of the `astraSDK/` classes can be found in the following pages:

* [Common](astrasdk/common/README.md)
* [Apps](astrasdk/apps/README.md)
* [Backups](astrasdk/backups/README.md)
* [Buckets](astrasdk/buckets/README.md)
* [Clouds](astrasdk/clouds/README.md)
* [Clusters](astrasdk/clusters/README.md)
* [Credentials](astrasdk/credentials/README.md)
* [Entitlements](astrasdk/entitlements/README.md)
* [Hooks](astrasdk/hooks/README.md)
* [Namespaces](astrasdk/namespaces/README.md)
* [Protections](astrasdk/protections/README.md)
* [Replications](astrasdk/replications/README.md)
* [Scripts](astrasdk/scripts/README.md)
* [Snapshots](astrasdk/snapshots/README.md)
* [Storageclasses](astrasdk/storageclasses/README.md)
* [Users](astrasdk/users/README.md)

## Toolkit Functions

actoolkit / toolkit.py utilizes `argparse` to provide an interactive CLI.  To view the possible arguments, run `actoolkit -h`:

```text
$ actoolkit -h
usage: actoolkit [-h] [-v] [-o {json,yaml,table}] [-q] [-f] [--v3] [--dry-run {client,server}] {deploy,clone,restore,ipr,list,get,copy,create,manage,define,destroy,unmanage,update} ...

positional arguments:
  {deploy,clone,restore,ipr,list,get,copy,create,manage,define,destroy,unmanage,update}
                        subcommand help
    deploy              Deploy kubernetes resources into current context
    clone               Live clone a running app to a new namespace
    restore             Restore an app from a backup or snapshot to a new namespace
    ipr                 In-Place Restore an app (destructive action for app) from a backup or snapshot
    list (get)          List all items in a class
    copy                Copy resources from one app to another app
    create              Create an object
    manage (define)     Manage an object
    destroy             Destroy an object
    unmanage            Unmanage an object
    update              Update an object

options:
  -h, --help            show this help message and exit
  -v, --verbose         print verbose/verbose output
  -o {json,yaml,table}, --output {json,yaml,table}
                        command output format
  -q, --quiet           supress output
  -f, --fast            prioritize speed over validation (using this will not validate arguments, which may have unintended consequences)

v3 group:
  use CR-driven Kubernetes workflows rather than the Astra Control API

  --v3                  create a v3 CR directly on the Kubernetes cluster (defaults to current context, but optionally specify a different context, kubeconfig_file, or kubeconfig_file:context mapping)
  --dry-run {client,server}
                        client: output YAML to standard out; server: submit request without persisting the resource
```

For more information on the positional arguments, see the following pages:

* [Deploy](toolkit/deploy/README.md)
* [Clone](toolkit/clone/README.md)
* [Restore](toolkit/restore/README.md)
* [IPR (In-Place-Restore)](toolkit/ipr/README.md)
* [List](toolkit/list/README.md)
* [Copy](toolkit/copy/README.md)
* [Create](toolkit/create/README.md)
* [Manage](toolkit/manage/README.md)
* [Destroy](toolkit/destroy/README.md)
* [Unmanage](toolkit/unmanage/README.md)
* [Update](toolkit/update/README.md)

For more information on the optional arguments, please see the following page:

* [Optional Global Arguments](toolkit/optionalargs/README.md).
