# Unmanage

The `unmanage` argument allows you to unmanage a currently managed object:

* [App](#app)
* [Bucket](#bucket)
* [Cloud](#cloud)
* [Cluster](#cluster)
* [LDAP](#ldap)

```text
$ actoolkit unmanage -h
usage: actoolkit unmanage [-h] {app,application,bucket,appVault,cloud,cluster,ldap} ...

options:
  -h, --help            show this help message and exit

objectType:
  {app,application,bucket,appVault,cloud,cluster,ldap}
    app (application)   unmanage app
    bucket (appVault)   unmanage bucket
    cloud               unmanage cloud
    cluster             unmanage cluster
    ldap                unmanage (disable) an LDAP(S) server
```

## App

Prior to unmanaging an appplication, it is recommended to first [destroy](../destroy/README.md) all [snapshots](../destroy/README.md#snapshot) and [backups](../destroy/README.md#backup) of the app.  Once that is complete, the [app ID](../list/README.md#apps) is utilized with the following command.

```text
actoolkit unmanage app <appID>
```

Sample output:

```text
$ actoolkit unmanage app 1d16c9f0-1b7f-4f21-804c-4162b0cfd56e
App unmanaged
```

## Bucket

Prior to unmanaging a bucket, it is **required** to first [destroy](../destroy/README.md) all [backups](../destroy/README.md#backup) that are stored within the object storage bucket.  Once that is complete, the [bucketID](../list/README.md#buckets) is utilized with the following command.

```text
actoolkit unmanage bucket <bucketID>
```

Sample output:

```text
$ actoolkit unmanage bucket d6c59f83-fcb2-4475-87de-cd5dc7277ac6
Bucket unmanaged
```

## Cloud

Prior to unmanaging a cloud, it is recommended to first unmanage all [clusters](#cluster) running in the environment.  Once that is complete, utilize the [cloud ID](../list/README.md#clouds) with the following command.

```text
actoolkit unmanage cloud <cloudID>
```

For all non-`private` cloudTypes, the associated credential is also destroyed.

Sample output:

```text
$ actoolkit unmanage cloud bd63bd2e-c6d5-4435-a5b2-71163d5c5dc1
Cloud unmanaged
Credential deleted
```

## Cluster

Prior to unmanaging a cluster, it is recommended to first unmanage all [applications](#app) running in the cluster.  Once that is complete, utilize the [cluster ID](../list/README.md#clusters) with the following command.

```text
actoolkit unmanage cluster <clusterID>
```

Sample output:

```text
$ actoolkit unmanage cluster 80d6bef8-300c-44bd-9e36-04ef874bdc29
Cluster unmanaged
```

In the event the cluster in question is a **non-public-cloud-managed** Kubernetes cluster (meaning it was added via a [create cluster](../create/README.md#cluster) command), the `unmanage cluster` command **also** deletes the cluster and cluster kubeconfig credentials from the system.

```text
$ actoolkit unmanage cluster 1fe9f33e-a560-41db-a72a-9544e2a4adcf
Cluster unmanaged
Cluster deleted
Credential deleted
```

## LDAP

The `unmanage ldap` command disables an LDAP server connection. This removes the ability for LDAP users/groups to log in to Astra Control, however it persists the rest of the information in the even you wish to [re-manage](../manage/README.md#ldap) the LDAP connection.

If you're looking to entirely remove the connection to an LDAP server, please see the [destroy LDAP](../destroy/README.md#ldap) command.

This command does not take any arguments:

```text
actoolkit unmanage ldap
```

Here's an example of the output:

```text
$ actoolkit unmanage ldap
{"type": "application/astra-setting", "version": "1.1", "metadata": {"creationTimestamp": "2024-03-11T13:39:50Z", "modificationTimestamp": "2024-03-15T14:28:31Z", "labels": [], "createdBy": "00000000-0000-0000-0000-000000000000", "modifiedBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d"}, "id": "32267c96-5da8-4174-bd59-1a4674aab7bf", "name": "astra.account.ldap", "desiredConfig": {"connectionHost": "10.10.10.200", "credentialId": "60a77224-a02d-403a-9c30-4aecc9ef984e", "groupBaseDN": "OU=e2e,DC=astra-example,DC=com", "isEnabled": "false", "loginAttribute": "mail", "port": 389, "secureMode": "LDAP", "userBaseDN": "OU=e2e,DC=astra-example,DC=com", "userSearchFilter": "(objectClass=Person)", "vendor": "Active Directory"}, "currentConfig": {"connectionHost": "10.10.10.200", "credentialId": "60a77224-a02d-403a-9c30-4aecc9ef984e", "groupBaseDN": "OU=e2e,DC=astra-example,DC=com", "isEnabled": "true", "loginAttribute": "mail", "port": 389, "secureMode": "LDAP", "userBaseDN": "OU=e2e,DC=astra-example,DC=com", "userSearchFilter": "(objectClass=Person)", "vendor": "Active Directory"}, "configSchema": {"$schema": "http://json-schema.org/draft-07/schema#", "title": "astra.account.ldap", "type": "object", "properties": {"connectionHost": {"type": "string", "description": "The hostname or IP address of your LDAP server."}, "credentialId": {"type": "string", "description": "The ID of the Astra credential containing the bind DN and credential."}, "groupBaseDN": {"type": "string", "description": "The base DN of the tree used to start the group search. The system searches the subtree from the specified location."}, "groupSearchCustomFilter": {"type": "string", "description": "A custom LDAP filter to use to search for groups"}, "isEnabled": {"type": "string", "description": "This property determines if this setting is enabled or not."}, "loginAttribute": {"type": "string", "description": "The LDAP attribute to be used to map to user email. Only mail or userPrincipalName is allowed."}, "port": {"type": "integer", "description": "The port on which the LDAP server is listening."}, "secureMode": {"type": "string", "description": "The secure mode LDAPS or LDAP."}, "userBaseDN": {"type": "string", "description": "The base DN of the tree used to start the user search. The system searches the subtree from the specified location."}, "userSearchFilter": {"type": "string", "description": "The filter used to search for users according to a search criteria."}, "vendor": {"type": "string", "description": "The LDAP provider you are using.", "enum": ["Active Directory"]}}, "additionalProperties": false, "required": ["connectionHost", "secureMode", "credentialId", "userBaseDN", "userSearchFilter", "groupBaseDN", "vendor", "isEnabled"]}, "state": "pending", "stateUnready": []}
```
