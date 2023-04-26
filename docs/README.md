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

toolkit.py utilizes `argparse` to provide an interactive CLI.  To view the possible arguments, run `./toolkit.py -h`:

```text
$ ./toolkit.py -h
usage: toolkit.py [-h] [-v] [-o {json,yaml,table}] [-q] [-f] {deploy,clone,restore,list,get,create,manage,define,destroy,unmanage,update} ...

positional arguments:
  {deploy,clone,restore,list,get,create,manage,define,destroy,unmanage,update}
                        subcommand help
    deploy              Deploy a helm chart
    clone               Clone an app from a backup, snapshot, or running app (live clone)
    restore             In-Place Restore (IPR) an app from a backup or snapshot
    list (get)          List all items in a class
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
```

For more information on the positional arguments, see the following pages:

* [Deploy](toolkit/deploy/README.md)
* [Clone](toolkit/clone/README.md)
* [Restore](toolkit/restore/README.md)
* [List](toolkit/list/README.md)
* [Create](toolkit/create/README.md)
* [Manage](toolkit/manage/README.md)
* [Destroy](toolkit/destroy/README.md)
* [Unmanage](toolkit/unmanage/README.md)
* [Update](toolkit/update/README.md)

For more information on the optional arguments, please see the following page:

* [Optional Global Arguments](toolkit/optionalargs/README.md).
