# NetApp Astra Control SDK Docs

## Installation and Configuration

See [the main README](../README.md) for information on how to install the NetApp Astra Control SDK.

## Astra SDK Classes

Coming soon.

## Toolkit Functions

toolkit.py utilizes `argparse` to provide an interactive CLI.  To view the possible arguments, run `./toolkit.py -h`:

```text
$ ./toolkit.py -h
usage: toolkit.py [-h] [-v] [-o {json,yaml,table}] [-q] [-f] {deploy,clone,restore,list,get,create,manage,define,destroy,unmanage,update} ...

positional arguments:
  {deploy,clone,restore,list,get,create,manage,define,destroy,unmanage,update}
                        subcommand help
    deploy              Deploy a helm chart
    clone               Clone an app
    restore             Restore an app from a backup or snapshot
    list (get)          List all items in a class
    create              Create an object
    manage (define)     Manage an object
    destroy             Destroy an object
    unmanage            Unmanage an object
    update              Update an object

optional arguments:
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
