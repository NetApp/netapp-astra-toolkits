# Destroy

The `destroy` argument allows you to destroy Astra resources.  Its opposite command is [create](../create/README.md), which allows you to create these resources.

**Use with caution**, as there is no confirmation required for these commands.

* [Asup](#asup)
* [Backup](#backup)
* [Credential](#credential)
* [Group](#group)
* [Hook](#hook)
* [LDAP](#ldap)
* [Protection](#protection)
* [Replication](#replication)
* [Script](#script)
* [Snapshot](#snapshot)
* [User](#user)

```text
$ actoolkit destroy -h
usage: actoolkit destroy [-h] {asup,backup,cluster,credential,secret,group,hook,exechook,ldap,protection,schedule,replication,script,snapshot,user} ...

options:
  -h, --help            show this help message and exit

objectType:
  {asup,backup,cluster,credential,secret,group,hook,exechook,ldap,protection,schedule,replication,script,snapshot,user}
    asup                destroy managed-cluster auto-support bundle
    backup              destroy backup
    cluster             destroy cluster
    credential (secret)
                        destroy credential
    group               destroy group
    hook (exechook)     destroy execution hook
    ldap                destroy (disconnect) an LDAP(S) server
    protection (schedule)
                        destroy protection policy
    replication         destroy replication policy
    script              destroy script (hookSource)
    snapshot            destroy snapshot
    user                destroy user
```

## Asup

The `destroy asup` command allows you to destroy a managed-cluster auto-support bundle. The command usage is:

```text
actoolkit destroy asup <asupID>
```

Sample output:

```text
$ actoolkit destroy asup f0510a66-0c89-483c-83dd-feba9add9d6e
Asup f0510a66-0c89-483c-83dd-feba9add9d6e destroyed
```

## Backup

The `destroy backup` command allows you to destroy a specific application backup.  The command usage is:

```text
actoolkit destroy backup <appID> <backupID>
```

The command initiates the backup destruction, and then returns the command prompt, so it make take a minute for the backup to no longer be present when performing a `list backups`.

```text
$ actoolkit destroy backup a643b5dc-bfa0-4624-8bdd-5ad5325f20fd \
    c06ec1e4-ae3d-4a32-bea0-771505f88203
Backup c06ec1e4-ae3d-4a32-bea0-771505f88203 destroyed
```

## Credential

The `destroy credential` command allows you to destroy a specific credential.  Use with caution, as there is no going back.  The command usage is:

```text
actoolkit destroy credential <credentialID>
```

Sample output:

```text
$ actoolkit destroy credential 8c2469f3-fcc6-469a-a952-30b7c76b9dad
Credential 8c2469f3-fcc6-469a-a952-30b7c76b9dad destroyed
```

## Group

The `destroy group` command allows you to destroy a specific group. The command usage is:

```text
actoolkit destroy group <groupID>
```

Sample output:

```text
$ actoolkit destroy group 55d38501-3946-4790-8cff-bcbbe5363597
RoleBinding f04b94b4-a751-41d2-9144-02181d5603fe destroyed
Group 55d38501-3946-4790-8cff-bcbbe5363597 destroyed
```

## Hook

The `destroy hook` command allows you to destroy a specific application execution hook.  The command usage is:

```text
actoolkit destroy hook <appID> <hookID>
```

Sample output:

```text
$ actoolkit destroy hook 7b647ab6-834b-4553-9b23-02ecdd8562f7 \
    6f9e8190-96fd-420c-be36-7324c6b54ce1
Hook 6f9e8190-96fd-420c-be36-7324c6b54ce1 destroyed
```

## LDAP

The `destroy ldap` command removes the connection to the configured LDAP server, and the associated service account credential. If you'd prefer to unmanage the LDAP server (which allows for [re-managing](../manage/README.md#ldap) the connection later), please see the [unmanage](../unmanage/README.md#ldap) page. The command usage is:

```text
actoolkit destroy ldap
```

Sample output:

```text
# actoolkit destroy ldap
{"type": "application/astra-setting", "version": "1.1", "metadata": {"creationTimestamp": "2024-03-11T13:39:50Z", "modificationTimestamp": "2024-03-15T20:11:34Z", "labels": [], "createdBy": "00000000-0000-0000-0000-000000000000", "modifiedBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d"}, "id": "32267c96-5da8-4174-bd59-1a4674aab7bf", "name": "astra.account.ldap", "desiredConfig": {"connectionHost": "", "credentialId": "", "groupBaseDN": "ou=groups,dc=example,dc=com", "groupSearchCustomFilter": "", "isEnabled": "false", "loginAttribute": "mail", "port": 636, "secureMode": "LDAPS", "userBaseDN": "ou=users,dc=example,dc=com", "userSearchFilter": "(objectClass=Person)", "vendor": "Active Directory"}, "currentConfig": {"connectionHost": "10.10.10.200", "credentialId": "136db44e-d4b9-4d2e-9823-1be89a629164", "groupBaseDN": "OU=e2e,DC=astra-example,DC=com", "isEnabled": "true", "loginAttribute": "mail", "port": 389, "secureMode": "LDAP", "userBaseDN": "OU=e2e,DC=astra-example,DC=com", "userSearchFilter": "(objectClass=Person)", "vendor": "Active Directory"}, "configSchema": {"$schema": "http://json-schema.org/draft-07/schema#", "title": "astra.account.ldap", "type": "object", "properties": {"connectionHost": {"type": "string", "description": "The hostname or IP address of your LDAP server."}, "credentialId": {"type": "string", "description": "The ID of the Astra credential containing the bind DN and credential."}, "groupBaseDN": {"type": "string", "description": "The base DN of the tree used to start the group search. The system searches the subtree from the specified location."}, "groupSearchCustomFilter": {"type": "string", "description": "A custom LDAP filter to use to search for groups"}, "isEnabled": {"type": "string", "description": "This property determines if this setting is enabled or not."}, "loginAttribute": {"type": "string", "description": "The LDAP attribute to be used to map to user email. Only mail or userPrincipalName is allowed."}, "port": {"type": "integer", "description": "The port on which the LDAP server is listening."}, "secureMode": {"type": "string", "description": "The secure mode LDAPS or LDAP."}, "userBaseDN": {"type": "string", "description": "The base DN of the tree used to start the user search. The system searches the subtree from the specified location."}, "userSearchFilter": {"type": "string", "description": "The filter used to search for users according to a search criteria."}, "vendor": {"type": "string", "description": "The LDAP provider you are using.", "enum": ["Active Directory"]}}, "additionalProperties": false, "required": ["connectionHost", "secureMode", "credentialId", "userBaseDN", "userSearchFilter", "groupBaseDN", "vendor", "isEnabled"]}, "state": "pending", "stateUnready": []}
Credential 136db44e-d4b9-4d2e-9823-1be89a629164 destroyed
```

## Protection

The `destroy protection` command allows you to destroy a single protection policy.  The command usage is:

```text
actoolkit destroy protection <appID> <protectionID>
```

Sample output:

```text
$ actoolkit destroy protection 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 \
    abc3c28b-d8bc-4a91-9aa7-18c3a2db6e8b
Protection policy abc3c28b-d8bc-4a91-9aa7-18c3a2db6e8b destroyed
```

## Replication

The `destroy replication` command allows you to destroy a single replication policy.  The command usage is:

```text
actoolkit destroy replication <replicationID>
```

Sample output:

```text
$ actoolkit destroy replication a0342d41-3c9c-447f-9d61-650bee68c21a
Replication policy a0342d41-3c9c-447f-9d61-650bee68c21a destroyed
Underlying replication schedule a81b0cdf-af1e-4194-ab61-ccc8c8ff21ab destroyed
```

## Script

The `destroy script` command allows you to destroy a specific script (aka hook source).  The command usage is:

```text
actoolkit destroy script <scriptID>
```

Sample output:

```text
$ actoolkit destroy script 879655c8-29e2-4131-bff2-1c654e093291
Script 879655c8-29e2-4131-bff2-1c654e093291 destroyed
```

## Snapshot

The `destroy snapshot` command allows you to destroy a specific application snapshot.  The command usage is:

```text
actoolkit destroy snapshot <appID> <snapshotID>
```

The command initiates the snapshot destruction, and then returns the command prompt, so it make take a minute for the snapshot to no longer be present when performing a `list snapshot`.

```text
$ actoolkit destroy snapshot a643b5dc-bfa0-4624-8bdd-5ad5325f20fd \
    3cb65a44-62a1-4157-a314-3840b761c6c8
Snapshot 3cb65a44-62a1-4157-a314-3840b761c6c8 destroyed
```

## User

The `destroy user` command allows you to destroy a specific user and its associated roleBinding.  The command usage is:

```text
actoolkit destroy user <userID>
```

Sample output:

```text
$ actoolkit destroy user 431aadcc-e568-4aef-bdd8-6df31eff1669
RoleBinding d1501dc7-3eb0-4f78-82fa-ea0d27b77b91 destroyed
User 431aadcc-e568-4aef-bdd8-6df31eff1669 destroyed
```
