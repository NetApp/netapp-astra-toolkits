# Destroy

The `destroy` argument allows you to destroy Astra resources.  Its opposite command is [create](../create/README.md), which allows you to create these resources.

**Use with caution**, as there is no confirmation required for these commands.

* [Backup](#backup)
* [Credential](#credential)
* [Hook](#hook)
* [Protection](#protection)
* [Replication](#replication)
* [Script](#script)
* [Snapshot](#snapshot)

```text
$ ./toolkit.py destroy -h
usage: toolkit.py destroy [-h] {backup,credential,hook,protection,replication,script,snapshot} ...

optional arguments:
  -h, --help            show this help message and exit

objectType:
  {backup,credential,hook,protection,replication,script,snapshot}
    backup              destroy backup
    credential          destroy credential
    hook                destroy hook (executionHook)
    protection          destroy protection policy
    replication         destroy replication policy
    script              destroy script (hookSource)
    snapshot            destroy snapshot
```

## Backup

The `destroy backup` command allows you to destroy a specific application backup.  The command usage is:

```text
./toolkit.py destroy backup <appID> <backupID>
```

The command initiates the backup destruction, and then returns the command prompt, so it make take a minute for the backup to no longer be present when performing a `list backups`.

```text
$ ./toolkit.py destroy backup a643b5dc-bfa0-4624-8bdd-5ad5325f20fd \
    c06ec1e4-ae3d-4a32-bea0-771505f88203
Backup c06ec1e4-ae3d-4a32-bea0-771505f88203 destroyed
```

## Credential

The `destroy credential` command allows you to destroy a specific credential.  Use with caution, as there is no going back.  The command usage is:

```text
./toolkit.py destroy credential <credentialID>
```

Sample output:

```text
$ ./toolkit.py destroy credential 8c2469f3-fcc6-469a-a952-30b7c76b9dad
Credential 8c2469f3-fcc6-469a-a952-30b7c76b9dad destroyed
```

## Hook

The `destroy hook` command allows you to destroy a specific application execution hook.  The command usage is:

```text
./toolkit.py destroy hook <appID> <hookID>
```

Sample output:

```text
$ ./toolkit.py destroy hook 7b647ab6-834b-4553-9b23-02ecdd8562f7 \
    6f9e8190-96fd-420c-be36-7324c6b54ce1
Hook 6f9e8190-96fd-420c-be36-7324c6b54ce1 destroyed
```

## Protection

The `destroy protection` command allows you to destroy a single protection policy.  The command usage is:

```text
./toolkit.py destroy protection <appID> <protectionID>
```

Sample output:

```text
$ ./toolkit.py destroy protection 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 \
    abc3c28b-d8bc-4a91-9aa7-18c3a2db6e8b
Protection policy abc3c28b-d8bc-4a91-9aa7-18c3a2db6e8b destroyed
```

## Replication

The `destroy replication` command allows you to destroy a single replication policy.  The command usage is:

```text
./toolkit.py destroy replication <replicationID>
```

Sample output:

```text
$ ./toolkit.py destroy replication a0342d41-3c9c-447f-9d61-650bee68c21a
Replication policy a0342d41-3c9c-447f-9d61-650bee68c21a destroyed
Underlying replication schedule a81b0cdf-af1e-4194-ab61-ccc8c8ff21ab destroyed
```

## Script

The `destroy script` command allows you to destroy a specific script (aka hook source).  The command usage is:

```text
./toolkit.py destroy script <scriptID>
```

Sample output:

```text
$ ./toolkit.py destroy script 879655c8-29e2-4131-bff2-1c654e093291
Script 879655c8-29e2-4131-bff2-1c654e093291 destroyed
```

## Snapshot

The `destroy snapshot` command allows you to destroy a specific application snapshot.  The command usage is:

```text
./toolkit.py destroy snapshot <appID> <snapshotID>
```

The command initiates the snapshot destruction, and then returns the command prompt, so it make take a minute for the snapshot to no longer be present when performing a `list snapshot`.

```text
$ ./toolkit.py destroy snapshot a643b5dc-bfa0-4624-8bdd-5ad5325f20fd \
    3cb65a44-62a1-4157-a314-3840b761c6c8
Snapshot 3cb65a44-62a1-4157-a314-3840b761c6c8 destroyed
```
