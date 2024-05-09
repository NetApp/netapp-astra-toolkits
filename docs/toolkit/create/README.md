# Create

The `create` argument allows you to create an Astra resource, including:

* [Asup](#asup)
* [Backup](#backup)
* [Cluster](#cluster)
* [Group](#group)
* [Hook](#hook)
* [LDAP](#ldap)
* [Protection](#protection)
* [Replication](#replication)
* [Script](#script)
* [Snapshot](#snapshot)
* [User](#user)

Its opposite command is [destroy](../destroy/README.md), which allows you to destroy these same resources.  **Create** and **destroy** are similar to [manage](../manage/README.md) and [unmanage](../unmanage/README.md), however create/destroy objects live entirely within Astra Control, while manage/unmanage objects do not.  If you create and then destroy a [snapshot](../create/README.md#snapshot), it is gone forever.  However if you manage and then unmanage a cluster, the cluster still exists to re-manage again.

```text
$ actoolkit create -h
usage: actoolkit create [-h] {asup,backup,cluster,group,hook,exechook,ldap,protection,schedule,replication,script,snapshot,user} ...

options:
  -h, --help            show this help message and exit

objectType:
  {asup,backup,cluster,group,hook,exechook,ldap,protection,schedule,replication,script,snapshot,user}
    asup                create auto-support bundle
    backup              create backup
    cluster             create cluster (upload a K8s cluster kubeconfig to then manage)
    group               create a remote group (requires LDAP)
    hook (exechook)     create execution hook
    ldap                create an LDAP(S) server connection for remote authentication
    protection (schedule)
                        create protection policy
    replication         create replication policy
    script              create script (hookSource)
    snapshot            create snapshot
    user                create a user
```

## Asup

The `create asup` command allows you to manually trigger an auto-support bundle. The command usage is:

```text
actoolkit create asup <optionalArguments>
```

Additional information on each argument is as follows:

* `-u`/`--upload`: specify this flag to have the auto-support bundle automatically uploaded to the NetApp Support Site when generated (default is to not have it uploaded)
* Custom Time Frame (cannot be used in conjunction with Quick Time Frame):
  * `--dataWindowStart`: an ISO-8601 timestamp, like `2024-05-08T14:11:07Z`. You must include a timezone, either via `Z` (UTC) or an offset `+04:00`. This argument defaults to 24 hours before `--dateWindowEnd`, and the maximum value is 7 days before the current time.
  * `--dataWindowEnd`: an ISO-8601 timestamp, like `2024-05-09T14:11:07Z`. You must include a timezone, either via `Z` (UTC) or an offset `+04:00`. This argument defaults to the current time of request.
* Quick Time Frame (cannot be used in conjunction with Custom Time Frame):
  * `-H`/`--hours`: specify the auto-support bundle to span the last X hours (anywhere from 1 to 24, inclusive). This field is mutually exclusive with `--days`.
  * `-d`/`--days`: specify the auto-support bundle to span the last X days (anywhere from 1 to 7, inclusive). This field is mutually exclusive with `--hours`.

To create an auto-support bundle covering the last 24 hours, and not upload it to the NetApp Support Site:

```text
$ actoolkit create asup
{"metadata": {"creationTimestamp": "2024-05-08T15:56:19Z", "modificationTimestamp": "2024-05-08T15:56:19Z", "createdBy": "62f49133-da54-4ce5-a4bb-9a20b5d9b000", "labels": []}, "type": "application/astra-asup", "version": "1.0", "id": "9bc7e099-ff24-4255-bd48-65167b087cec", "upload": "false", "creationState": "running", "triggerType": "manual", "dataWindowStart": "2024-05-07T15:56:19Z", "dataWindowEnd": "2024-05-08T15:56:19Z"}
```

To create an auto-support bundle covering the last 2 days, and upload it to the NetApp Support Site:

```text
$ actoolkit create asup --upload -d 2
{"metadata": {"creationTimestamp": "2024-05-09T15:01:35Z", "modificationTimestamp": "2024-05-09T15:01:35Z", "createdBy": "62f49133-da54-4ce5-a4bb-9a20b5d9b000", "labels": []}, "type": "application/astra-asup", "version": "1.0", "id": "3d395cd3-5fa8-43ba-a882-805eb4e6741b", "upload": "true", "creationState": "running", "uploadState": "pending", "triggerType": "manual", "dataWindowStart": "2024-05-07T15:01:35Z", "dataWindowEnd": "2024-05-09T15:01:35Z"}
```

To create an auto-support bundle covering March 7th, 2023 in the EDT timezone, and not have it automatically upload to the NetApp Support Site:

```text
$ actoolkit create asup --dataWindowStart 2024-05-07T00:00:00+04:00 --dataWindowEnd 2024-05-07T23:59:59+04:00
{"metadata": {"creationTimestamp": "2024-05-09T15:21:39Z", "modificationTimestamp": "2024-05-09T15:21:39Z", "createdBy": "62f49133-da54-4ce5-a4bb-9a20b5d9b000", "labels": []}, "type": "application/astra-asup", "version": "1.0", "id": "649de606-2b9d-4f82-88b9-239b45e7f24c", "upload": "false", "creationState": "running", "triggerType": "manual", "dataWindowStart": "2024-05-07T00:00:00+04:00", "dataWindowEnd": "2024-05-07T23:59:59+04:00"}
```

## Backup

The `create backup` command allows you to take an ad-hoc backup.  The command usage is:

```text
actoolkit create backup <optionalBackgroundArg> <optionalPollTimer> <appID> <backupName> \
    <optionalBucketID> <optionalSnapshotID>
```

Additional information on each argument is as follows:

* `-b`/`--background`: when specified, the terminal prompt is returned after initiating the backup.  If **not** specified (default behavior), the command polls for the status of the backup operation
* `-t`/`--pollTimer`: the frequency to check the status of the backup operation (default is 5 seconds)
* `-u`/`--bucketID`: the [bucketID](../list/README.md#buckets) to store the backup, if not specified, the default bucket for the cloud is used
* `-s`/`--snapshotID`: the [snapshotID](../list/README.md#snapshots) to create the backup from, if not specified, a new snapshot is created

To create a foreground backup based on a new snapshot and store it in the default bucket:

```text
$ actoolkit create backup a643b5dc-bfa0-4624-8bdd-5ad5325f20fd 20220523-cli-backup1
Starting backup of a643b5dc-bfa0-4624-8bdd-5ad5325f20fd
Waiting for backup to complete.....................................................................
..................................................................complete!
```

To create a background backup based on a new snapshot and store it in the default bucket:

```text
$ actoolkit create backup -b a643b5dc-bfa0-4624-8bdd-5ad5325f20fd 20220523-cli-backup2
Starting backup of a643b5dc-bfa0-4624-8bdd-5ad5325f20fd
Background backup flag selected, run 'list backups' to get status
$ actoolkit list backups
+--------------------------------------+----------------------+--------------------------------------+-------------+
| AppID                                | backupName           | backupID                             | backupState |
+======================================+======================+======================================+=============+
| a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | hourly-cpesy-g82fd   | 2ce7996a-3b21-4dc7-ae5f-7c287c479f7e | completed   |
+--------------------------------------+----------------------+--------------------------------------+-------------+
| a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | 20220523-cli-backup1 | 7be82451-7e89-43fb-8251-9a347ce513e0 | completed   |
+--------------------------------------+----------------------+--------------------------------------+-------------+
| a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | 20220523-cli-backup2 | c06ec1e4-ae3d-4a32-bea0-771505f88203 | ready       |
+--------------------------------------+----------------------+--------------------------------------+-------------+
```

To create a foreground backup from an existing snapshot while polling on the status ever 60 seconds:

```text
$ actoolkit create backup 92020880-a2e1-4ae2-aed0-40bd74c3d0bf from-snap \
    -s 0a71b847-5677-4d66-ae7d-5e34117910b5 \
    -t 60
Starting backup of 92020880-a2e1-4ae2-aed0-40bd74c3d0bf
Waiting for backup to complete...complete!
```

To create a background backup based on a new snapshot and store it in a non-default bucket:

```text
$ actoolkit create backup -b 92020880-a2e1-4ae2-aed0-40bd74c3d0bf new-bucket-backup \
    --bucketID 30132ef3-d1a1-4385-8e10-43b5b7740299
Starting backup of 92020880-a2e1-4ae2-aed0-40bd74c3d0bf
Background backup flag selected, run 'list backups' to get status
```

## Cluster

The `create cluster` command allows you to create non-public-cloud-managed Kubernetes clusters from a kubeconfig file.  After the cluster is "created" it **must** still be [managed](../manage/README.md#cluster) to be fully brought under Astra's control.  The command usage is:

```text
actoolkit create cluster <kubeconfig-filePath> -c <optionalCloudIdArg> \
    <--privateRouteID optionalPrivateRouteID>
```

Additional information on each argument is as follows:

* `filePath` is the local filesystem path to the [kubeconfig](https://docs.netapp.com/us-en/astra-control-center/get-started/add-cluster-reqs.html#create-an-admin-role-kubeconfig) file which has an admin-role for the Kubernetes cluster
* `-c`/`--cloudID` can be gathered from a [list clouds](../list/README.md#clouds) command, however it is only needed in the event there are multiple, **non-public** clouds on the system.  In the event there is only a single non-public cloud within Astra Control, then that cloudID is automatically used.
* `--privateRouteID` is an optional value, only needed for managing private clusters that are not accessible from the internet. The Astra Connector must first be installed on the cluster in question, and then the private route ID can be gathered from the operator output. See the [main docs](https://docs.netapp.com/us-en/astra-control-service/get-started/manage-private-cluster.html) for more information.

When running the `create cluster` command, you will notice two API responses, the first for creating the kubeconfig credential, the second for creating the cluster object which references the same credential.

```text
$ actoolkit create cluster ~/.kube/oc-tmecluster02-config.yaml
{"type": "application/astra-credential", "version": "1.1", "id": "68af1e92-1b5a-439b-935c-b0605b7efd3a", "name": "openshift-tmecluster02", "keyType": "kubeconfig", "metadata": {"creationTimestamp": "2022-08-17T17:09:47Z", "modificationTimestamp": "2022-08-17T17:09:47Z", "createdBy": "79b66aad-aba6-4673-9cef-994fa91c8de6", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "kubeconfig"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "private"}]}}
{"type": "application/astra-cluster", "version": "1.1", "id": "1fe9f33e-a560-41db-a72a-9544e2a4adcf", "name": "openshift-tmecluster02", "state": "running", "stateUnready": [], "managedState": "unmanaged", "managedStateUnready": [], "inUse": "false", "clusterType": "openshift", "namespaces": [], "defaultStorageClass": "5f71d427-bee2-44cf-9ce3-30649676f6d4", "cloudID": "bd976721-6d70-464b-8c84-fa70b5009b1e", "credentialID": "68af1e92-1b5a-439b-935c-b0605b7efd3a", "isMultizonal": "false", "tridentVersion": "22.01.0", "metadata": {"labels": [], "creationTimestamp": "2022-08-17T17:09:49Z", "modificationTimestamp": "2022-08-17T17:09:49Z", "createdBy": "79b66aad-aba6-4673-9cef-994fa91c8de6"}}
```

```text
$ actoolkit create cluster ~/.kube/private-config \
    --privateRouteID 863a3c08-34e6-463a-b479-1b1bdbdf7178
{"type": "application/astra-credential", "version": "1.1", "id": "378fcfef-f9e0-4c25-ab67-91977f8188da", "name": "api-j0rpeqpa-westeurope-aroapp-io:6443", "keyType": "kubeconfig", "valid": "true", "metadata": {"creationTimestamp": "2023-06-27T18:03:23Z", "modificationTimestamp": "2023-06-27T18:03:23Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "kubeconfig"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "private"}]}}
{"type": "application/astra-cluster", "version": "1.5", "id": "0aa6fd87-8534-41d7-bef4-4eaedfed4ffa", "name": "api-j0rpeqpa-westeurope-aroapp-io:6443", "state": "running", "stateUnready": [], "managedState": "unmanaged", "protectionState": "full", "protectionStateDetails": [], "managedStateUnready": [], "inUse": "false", "clusterType": "openshift", "connectorCapabilities": [], "namespaces": [], "defaultStorageClass": "e78e4b0f-1e4c-46ed-976f-6f6df5ea07e4", "cloudID": "91ef340d-6ce2-4d54-846a-cf9ba3a4f4ae", "credentialID": "378fcfef-f9e0-4c25-ab67-91977f8188da", "isMultizonal": "false", "tridentManagedStateAllowed": ["unmanaged"], "tridentVersion": "", "privateRouteID": "863a3c08-34e6-463a-b479-1b1bdbdf7178", "apiServiceID": "984888f5-f345-41a1-b207-3a9bd726368f", "metadata": {"labels": [], "creationTimestamp": "2023-06-27T18:03:31Z", "modificationTimestamp": "2023-06-27T18:03:31Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Group

The `create group` command allows you to create an Astra Control group from an LDAP group definition, enabling group-wide remote authentication. This is only applicable with ACC environments with an [LDAP](#ldap) server configured. The command usage is:

```text
actoolkit create group <dn> <role> \
    <-a optional labelConstraint> <-n optional namespaceConstraint>
```

The `dn` argument must be a distinguished name present in your LDAP server (see [list ldapgroups](../list/README.md#ldapgroups) for information on how to query LDAP for groups).

The role argument must be one of the following four values:

* viewer
* member
* admin
* owner

```text
$ actoolkit create group "CN=michael,OU=Users,OU=e2e,DC=astra-example,DC=com" member
PI HTTP Status Code: 201
{"type": "application/astra-group", "version": "1.1", "id": "55d38501-3946-4790-8cff-bcbbe5363597", "name": "michael", "authProvider": "ldap", "authID": "cn=michael,ou=users,ou=e2e,dc=astra-example,dc=com", "metadata": {"creationTimestamp": "2024-03-18T17:14:55Z", "modificationTimestamp": "2024-03-18T17:14:55Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": []}}
PI HTTP Status Code: 201
{"metadata": {"creationTimestamp": "2024-03-18T17:14:55Z", "modificationTimestamp": "2024-03-18T17:14:55Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": []}, "type": "application/astra-roleBinding", "principalType": "group", "version": "1.1", "id": "f04b94b4-a751-41d2-9144-02181d5603fe", "userID": "00000000-0000-0000-0000-000000000000", "groupID": "55d38501-3946-4790-8cff-bcbbe5363597", "accountID": "1792ed1d-d55f-4a98-b07d-532b17ac2e77", "role": "member", "roleConstraints": ["*"]}
```

Any number of labelConstraints (`-a`/`--labelConstraint`) and/or namespaceConstraints (`-n`/`--namespaceConstraint`) can be provided (note that multiple values can be provided, either with space separated values, or specifying the argument again).

```text
$ actoolkit create group "CN=michael,OU=Users,OU=e2e,DC=astra-example,DC=com" \
    member -a kubernetes.io/metadata.name=wordpress -n 89a3965f-b52c-5397-9236-e214dca5a241
{"type": "application/astra-group", "version": "1.1", "id": "e19f6b87-f788-41d6-9958-85190e77479e", "name": "michael", "authProvider": "ldap", "authID": "cn=michael,ou=users,ou=e2e,dc=astra-example,dc=com", "metadata": {"creationTimestamp": "2024-03-18T17:38:28Z", "modificationTimestamp": "2024-03-18T17:38:28Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": []}}
{"metadata": {"creationTimestamp": "2024-03-18T17:38:29Z", "modificationTimestamp": "2024-03-18T17:38:29Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": []}, "type": "application/astra-roleBinding", "principalType": "group", "version": "1.1", "id": "f266bb40-e204-4543-9366-bcbec9738671", "userID": "00000000-0000-0000-0000-000000000000", "groupID": "e19f6b87-f788-41d6-9958-85190e77479e", "accountID": "1792ed1d-d55f-4a98-b07d-532b17ac2e77", "role": "member", "roleConstraints": ["namespaces:id='89a3965f-b52c-5397-9236-e214dca5a241'.*", "namespaces:kubernetesLabels='kubernetes.io/metadata.name=wordpress'.*"]}
```

## Hook

The `create hook` command allows you to create an application execution hook for an [application](../manage/README.md#app).  The high level command usage is:

```text
actoolkit create hook <appID> <hookName> <scriptID> -o <operationType> \
    -a <optionalHookArg1> <optionalHookArgX> \
    -i <optionalContainerImageFilter1> <optionalContainerImageFilterX> \
    -n <optionalNamespaceFilter1> <optionalNamespaceFilterX> \
    -p <optionalPodNameFilter1> <optionalPodNameFilterX> \
    -l <optionalLabelFilter1> <optionalLabelFilterX> \
    -c <optionalContainerNameFilter1> <optionalContainerNameFilterX>
```

Additional information on each argument is as follows:

* `appID` can be gathered from a [list apps](../list/README.md#apps) command
* `hookName` is the friendly name of your choice
* `scriptID` can be gathered from a [list scripts](../list/README.md#scripts) command
* `-o`/`--operation` must be one of:
  * pre-snapshot
  * post-snapshot
  * pre-backup
  * post-backup
  * post-restore
* `-a`/`--hookArguments` are (optional) command line arguments that *may* be required depending upon the script defined via the `scriptID`.  Any number of arguments can be provided.
* `filterGroup` is a list of five optional logical AND [regex](https://docs.netapp.com/us-en/astra-control-service/use/manage-app-execution-hooks.html) filters to minimize the number of containers where the hook will execute (if no filterGroup arguments are provided, then this execution hook applies to **all** container images within the application):
  * `-i`/`--containerImage`: regex filter for container images
  * `-n`/`--namespace`: regex filter for namespaces (useful for multi-namespace apps)
  * `-p`/`--podName`: regex filters for pod names
  * `-l`/`--label`: regex filter for Kubernetes labels
  * `-c`/`--containerName`: regex filter for container names

This example creates a "post-snapshot" execution hook for appID "7b647ab6-834b-4553-9b23-02ecdd8562f7" named "wordpress-mariadb-post-snapshot", and provides the command line argument "post" to scriptID "41bd1ee4-6283-4e6b-a9f0-a4b29de3fb3d".  Since no filters are provided, it matches on all images within the app.

```text
$ actoolkit create hook 7b647ab6-834b-4553-9b23-02ecdd8562f7 wordpress-post-snapshot \
    41bd1ee4-6283-4e6b-a9f0-a4b29de3fb3d -o post-snapshot -a post
{"metadata": {"labels": [], "creationTimestamp": "2022-08-03T18:43:58Z", "modificationTimestamp": "2022-08-03T18:43:58Z", "createdBy": "59c784bb-9b28-4da5-ae8a-f20794ec562f"}, "type": "application/astra-executionHook", "version": "1.0", "id": "6f9e8190-96fd-420c-be36-7324c6b54ce1", "name": "wordpress-post-snapshot", "hookType": "custom", "action": "snapshot", "stage": "post", "hookSourceID": "41bd1ee4-6283-4e6b-a9f0-a4b29de3fb3d", "arguments": ["post"], "appID": "7b647ab6-834b-4553-9b23-02ecdd8562f7", "enabled": "true"}
```

This example creates a "pre-backup" execution hook for appID "7b647ab6-834b-4553-9b23-02ecdd8562f7" named "wordpress-mariadb-pre-snap", provides the command line argument "pre" to scriptID "41bd1ee4-6283-4e6b-a9f0-a4b29de3fb3d", and only runs agains container images with a matching regex of "\bmariadb\b" (**note** the quotes).

```text
$ actoolkit create hook 7b647ab6-834b-4553-9b23-02ecdd8562f7 wordpress-mariadb-pre-snap \
    41bd1ee4-6283-4e6b-a9f0-a4b29de3fb3d -o pre-backup -a pre -i "\bmariadb\b"
{"metadata": {"labels": [], "creationTimestamp": "2022-08-03T18:57:39Z", "modificationTimestamp": "2022-08-03T18:57:39Z", "createdBy": "59c784bb-9b28-4da5-ae8a-f20794ec562f"}, "type": "application/astra-executionHook", "version": "1.0", "id": "f2da43bd-0278-4f21-b9b6-ea64a7247423", "name": "wordpress-mariadb-pre-snap", "hookType": "custom", "matchingCriteria": [{"type": "containerImage", "value": "\\bmariadb\\b"}], "action": "backup", "stage": "pre", "hookSourceID": "41bd1ee4-6283-4e6b-a9f0-a4b29de3fb3d", "arguments": ["pre"], "appID": "7b647ab6-834b-4553-9b23-02ecdd8562f7", "enabled": "true"}
```

This example creates a "post-restore" execution hook for appID "eebd59f2-e9b3-47b0-b0e8-1306d805f104" named "cassandra-post-restore", provides two separate command line arguments ("post-restore" and "false") to scriptID "db17a907-9518-4836-850f-1d21bc7651d7", and only runs against container names of cassandra.

```text
$ actoolkit create hook eebd59f2-e9b3-47b0-b0e8-1306d805f104 cassandra-post-restore \
    db17a907-9518-4836-850f-1d21bc7651d7 -o post-restore -a post-restore false -c cassandra
{"metadata": {"labels": [], "creationTimestamp": "2022-08-03T19:01:22Z", "modificationTimestamp": "2022-08-03T19:01:22Z", "createdBy": "59c784bb-9b28-4da5-ae8a-f20794ec562f"}, "type": "application/astra-executionHook", "version": "1.0", "id": "a1a1ca43-1aee-4707-a514-0f251a336e06", "name": "cassandra-post-restore", "hookType": "custom", "matchingCriteria": [{"type": "containerName", "value": "cassandra"}], "action": "restore", "stage": "post", "hookSourceID": "db17a907-9518-4836-850f-1d21bc7651d7", "arguments": ["post-restore", "false"], "appID": "eebd59f2-e9b3-47b0-b0e8-1306d805f104", "enabled": "true"}
```

This example creates a "pre-snapshot" execution hook for appID "187f0f70-c879-40d4-87d4-64219612bc60" named "mdb-presnap", and filters to only run on containers with images matching a regex of "\bmariadb\b", and belonging to the namespace "wordpress", and with a pod name of "wordpress-mariadb-0", and labels matching "app.kubernetes.io/name=mariadb" and "app.kubernetes.io/app=wordpress", and container name of "mariadb".

```text
$ actoolkit create hook 187f0f70-c879-40d4-87d4-64219612bc60 mdb-presnap \
    f402940e-c9ef-4c49-b5e8-4d126ab8d072 -o pre-snapshot -i "\bmariadb\b" -n wordpress \
    -p wordpress-mariadb-0 -l "app.kubernetes.io/name=mariadb" "app.kubernetes.io/app=wordpress" -c mariadb
{"metadata": {"labels": [], "creationTimestamp": "2022-12-22T19:59:21Z", "modificationTimestamp": "2022-12-22T19:59:21Z", "createdBy": "ebbc0fde-da6d-4939-a9ad-0f8fd0d70f1c"}, "type": "application/astra-executionHook", "version": "1.2", "id": "2f4f0b8a-b1d1-4119-a185-1850c7550aa6", "name": "mdb-presnap", "hookType": "custom", "matchingCriteria": [{"type": "containerImage", "value": "\\bmariadb\\b"}, {"type": "namespaceName", "value": "wordpress"}, {"type": "podName", "value": "wordpress-mariadb-0"}, {"type": "podLabel", "value": "app.kubernetes.io/name=mariadb"}, {"type": "podLabel", "value": "app.kubernetes.io/app=wordpress"}, {"type": "containerName", "value": "mariadb"}], "action": "snapshot", "stage": "pre", "hookSourceID": "f402940e-c9ef-4c49-b5e8-4d126ab8d072", "arguments": [], "appID": "187f0f70-c879-40d4-87d4-64219612bc60", "enabled": "true"}
```

## LDAP

The `create ldap` command allows you to set up a connection to a remote authentication server. For more information on this feature, please see the [official docs](https://docs.netapp.com/us-en/astra-control-center/use/manage-remote-authentication.html). The high level command usage is:

```text
actoolkit manage ldap <url-or-ip> <port> [--secure] \
    -u USERNAME -p PASSWORD \
    --userBaseDN USERBASEDN [--userSearchFilter USERSEARCHFILTER] [--userLoginAttribute {mail,userPrincipalName}] \
    --groupBaseDN GROUPBASEDN [--groupSearchFilter GROUPSEARCHFILTER]
```

Additional information on each argument is as follows:

* `url-or-ip`: the URL or IP Address of the LDAP(S) server
* `port`: the port to be used for connectiong to the LDAP(S) server (typically `389` for LDAP and `636` for LDAPS)
* `--secure`: specify to use LDAPS instead of LDAP
* Service Account arguments:
  * `-u`/`--username`: the username (in email format) of the service account used to connect to the LDAP server (**required**)
  * `-p`/`--password`: the password of the service account used to connect to the LDAP server (**required**)
* User Match arguments:
  * `--userBaseDN`: the user search base DN used when retrieving user information from the LDAP server (**required**)
  * `--userSearchFilter`: the user search filter used when retrieving user information from the LDAP server
  * `--userLoginAttribute`: the user login attribute to use (must be either `mail` or `userPrincipalName`)
* Group Match arguments:
  * `--groupBaseDN`: the group search base DN used when retrieving group information from the LDAP server (**required**)
  * `--groupSearchFilter`: an optional custom group search filter

This is an example command and response:

```text
$ actoolkit manage ldap 10.10.10.200 389 -u service-account@astra-example.com -p SA-Password --userBaseDN OU=e2e,DC=astra-example,DC=com --groupBaseDN OU=e2e,DC=astra-example,DC=com
{"type": "application/astra-credential", "version": "1.1", "id": "60a77224-a02d-403a-9c30-4aecc9ef984e", "name": "ldapBindCredential-service-account", "keyType": "generic", "valid": "true", "metadata": {"creationTimestamp": "2024-03-15T14:04:43Z", "modificationTimestamp": "2024-03-15T14:04:43Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "generic"}]}}
{"type": "application/astra-setting", "version": "1.1", "metadata": {"creationTimestamp": "2024-03-11T13:39:50Z", "modificationTimestamp": "2024-03-15T14:04:43Z", "labels": [], "createdBy": "00000000-0000-0000-0000-000000000000", "modifiedBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d"}, "id": "32267c96-5da8-4174-bd59-1a4674aab7bf", "name": "astra.account.ldap", "desiredConfig": {"connectionHost": "10.10.10.200", "credentialId": "60a77224-a02d-403a-9c30-4aecc9ef984e", "groupBaseDN": "OU=e2e,DC=astra-example,DC=com", "isEnabled": "true", "loginAttribute": "mail", "port": 389, "secureMode": "LDAP", "userBaseDN": "OU=e2e,DC=astra-example,DC=com", "userSearchFilter": "(objectClass=Person)", "vendor": "Active Directory"}, "currentConfig": {"connectionHost": "", "credentialId": "", "groupBaseDN": "ou=groups,dc=example,dc=com", "groupSearchCustomFilter": "", "isEnabled": "false", "loginAttribute": "mail", "port": 636, "secureMode": "LDAPS", "userBaseDN": "ou=users,dc=example,dc=com", "userSearchFilter": "(objectClass=Person)", "vendor": "Active Directory"}, "configSchema": {"$schema": "http://json-schema.org/draft-07/schema#", "title": "astra.account.ldap", "type": "object", "properties": {"connectionHost": {"type": "string", "description": "The hostname or IP address of your LDAP server."}, "credentialId": {"type": "string", "description": "The ID of the Astra credential containing the bind DN and credential."}, "groupBaseDN": {"type": "string", "description": "The base DN of the tree used to start the group search. The system searches the subtree from the specified location."}, "groupSearchCustomFilter": {"type": "string", "description": "A custom LDAP filter to use to search for groups"}, "isEnabled": {"type": "string", "description": "This property determines if this setting is enabled or not."}, "loginAttribute": {"type": "string", "description": "The LDAP attribute to be used to map to user email. Only mail or userPrincipalName is allowed."}, "port": {"type": "integer", "description": "The port on which the LDAP server is listening."}, "secureMode": {"type": "string", "description": "The secure mode LDAPS or LDAP."}, "userBaseDN": {"type": "string", "description": "The base DN of the tree used to start the user search. The system searches the subtree from the specified location."}, "userSearchFilter": {"type": "string", "description": "The filter used to search for users according to a search criteria."}, "vendor": {"type": "string", "description": "The LDAP provider you are using.", "enum": ["Active Directory"]}}, "additionalProperties": false, "required": ["connectionHost", "secureMode", "credentialId", "userBaseDN", "userSearchFilter", "groupBaseDN", "vendor", "isEnabled"]}, "state": "pending", "stateUnready": []}
```

## Protection

The `create protection` command allows you to create a protection policy for an [application](../manage/README.md#app).  The high level command usage is:

```text
actoolkit create protection <appID> -g <granularity> <date/time args> \
    -b <backupsToRetain> -s <snapshotsToRetain>
```

The \<appID\> argument can be gathered from a [list apps](../list/README.md#apps) command.

To configure a protection policy with all four protection schedules, the `create protection` command must be ran four times, once for each level of granularity:

* [Hourly](#hourly)
* [Daily](#daily)
* [Weekly](#weekly)
* [Monthly](#monthly)

There are four total \<date/time arguments\>, which either must be entered, must not be entered, are optional, or not applicable, depending upon the granularity level chosen:

| DateTime \ Granularity | Hourly   | Daily    | Weekly   | Monthly  |
| ---------------------- | -------- | -------- | -------- | -------- |
| `-m` / `--minute`      | Must     | Optional | Optional | Optional |
| `-H` / `--hour`        | Must Not | Must     | Must     | Must     |
| `-W` / `--dayOfWeek`   | N/A      | N/A      | Must     | Must Not |
| `-M` / `--dayOfMonth`  | N/A      | N/A      | N/A      | Must     |

The possible values for the \<date/time arguments\> are as follows:

* **`-m` / `--minute`**: Between 0 and 59, inclusive, with 0 as the default if not specified.
* **`-H` / `--hour`**: Between 0 and 23, inclusive (UTC).
* **`-W` / `--dayOfWeek`**: Between 0 and 6, inclusive, with 0 representing Sunday, and 6 Saturday.
* **`-M` / `--dayOfMonth`**: Between 1 and 31, inclusive.

The `--backupRetention`/`-b` and `--snapshotRetention`/`-s` arguments specify the number of backups and snapshots to store, respectively.  Both arguments are required, and can be any number between **0 and 59**, inclusive.

### Hourly

This example creates an `hourly` protection schedule, on the 15 minute mark, while keeping the last two backups and last three snapshots.

```text
$ actoolkit create protection a643b5dc-bfa0-4624-8bdd-5ad5325f20fd -g hourly \
    -m 15 -b 2 -s 3
{"type": "application/astra-schedule", "version": "1.1", "id": "c94a0c35-4e24-4664-b3f5-211e5aecf498", "name": "hourly-cpesy", "enabled": "true", "granularity": "hourly", "minute": "15", "snapshotRetention": "3", "backupRetention": "2", "metadata": {"labels": [], "creationTimestamp": "2022-05-23T16:03:23Z", "modificationTimestamp": "2022-05-23T16:03:23Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Daily

This example creates a `daily` protection schedule, at 05:30 UTC, while keeping the last two backups and last two snapshots.

```text
$ actoolkit create protection a643b5dc-bfa0-4624-8bdd-5ad5325f20fd -g daily \
    -H 5 -m 30 -b 2 -s 2
{"type": "application/astra-schedule", "version": "1.1", "id": "cbd5edd2-21c9-4283-a7cc-4eaae5c25952", "name": "daily-xok21", "enabled": "true", "granularity": "daily", "minute": "30", "hour": "5", "snapshotRetention": "2", "backupRetention": "2", "metadata": {"labels": [], "creationTimestamp": "2022-05-23T16:07:54Z", "modificationTimestamp": "2022-05-23T16:07:54Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Weekly

This example creates a `weekly` protection schedule, on Sundays at 04:45 UTC, while keeping the last backup and last snapshot.

```text
$ actoolkit create protection a643b5dc-bfa0-4624-8bdd-5ad5325f20fd -g weekly \
    -W 0 -H 4 -m 45 -b 1 -s 1
{"type": "application/astra-schedule", "version": "1.1", "id": "aa174808-4f8c-4a0b-839e-5ceecf7c0f2d", "name": "weekly-uh8hq", "enabled": "true", "granularity": "weekly", "minute": "45", "hour": "4", "dayOfWeek": "0", "snapshotRetention": "1", "backupRetention": "1", "metadata": {"labels": [], "creationTimestamp": "2022-05-23T16:23:36Z", "modificationTimestamp": "2022-05-23T16:23:36Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Monthly

This example creates a `monthly` protection schedule, on the 1st day of the month at 03:45 UTC, while keeping the last backup and last snapshot.

```text
actoolkit create protection a643b5dc-bfa0-4624-8bdd-5ad5325f20fd -g monthly \
    -M 1 -H 3 -m 45 -b 1 -s 1
{"type": "application/astra-schedule", "version": "1.1", "id": "f9dad3d7-a085-4e07-99be-88a90fc8362b", "name": "monthly-teds6", "enabled": "true", "granularity": "monthly", "minute": "45", "hour": "3", "dayOfMonth": "1", "snapshotRetention": "1", "backupRetention": "1", "metadata": {"labels": [], "creationTimestamp": "2022-05-23T16:24:52Z", "modificationTimestamp": "2022-05-23T16:24:52Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Script

The `create script` command allows you to create a script (aka hook source).  The command usage is:

```text
actoolkit create script <name> <filePath> -d <optionalDescription>
```

The `name` argument is the friendly name of the script, which must not already exist on the system (a 400 error will be thrown if the name is not unique).

The `filePath` argument must be the local filesystem location of the script, either relative or absolute path.

The `-d`/`--description` argument is completely optional, and can be placed anywhere after the third argument (script).

```text
$ actoolkit create script cassandra ~/Verda/Cassandra/cassandra-snap-hooks.sh
{"metadata": {"labels": [], "creationTimestamp": "2022-08-02T14:44:00Z", "modificationTimestamp": "2022-08-02T14:44:00Z", "createdBy": "7cc9170d-d227-49ac-bf9e-6b080ce59524"}, "type": "application/astra-hookSource", "version": "1.0", "id": "6d1f7589-7f0b-4211-99f7-63f69e2495bf", "name": "cassandra", "private": "false", "preloaded": "false", "sourceType": "script", "source": "IyEvYmluL3NoCiMKCiMgY2Fzc2FuZHJhLXNuYXAtaG9va3Muc2gKIwojIFByZS0gYW5kIHBvc3Qtc25hcHNob3QgZXhlY3V0aW9uIGhvb2tzIGZvciBDYXNzYW5kcmEuCiMgVGVzdGVkIHdpdGggQ2Fzc2FuZHJhIDQuMC40IChkZXBsb3llZCBieSBCaXRuYW1pIGhlbG0gY2hhcnQgOS4yLjUpIGFuZCBOZXRBcHAgQXN0cmEgQ29udHJvbCBTZXJ2aWNlIDIyLjA0LgojCiMgYXJnczogW3ByZXxwb3N0XQojIHByZTogZmx1c2ggYWxsIGtleXNwYWNlcyBhbmQgdGFibGVzIGJ5ICJub2RldG9vbCBmbHVzaCIKIyBwb3N0OiBjaGVjayBhbGwgdGFibGVzICgibm9kZXRvb2wgdmVyaWZ5IikKIwojIFRoZSBjdXJyZW50IHZlcnNpb24gb2YgQXN0cmEgQ29udHJvbCBjYW4gb25seSB0YXJnZXQgdGhlIGNvbnRhaW5lcnMgdG8gZXhlY3V0ZSBob29rcyBieSBpbWFnZSBuYW1lLiBUaGUgaG9vayB3aWxsIHJ1biBmb3IgYW55IGNvbnRhaW5lciBpbWFnZSAKIyB0aGF0IG1hdGNoZXMgdGhlIHByb3ZpZGVkIHJlZ3VsYXIgZXhwcmVzc2lvbiBydWxlIGluIEFzdHJhIENvbnRyb2wuCiMKIyBBIHJlc3RvcmUgb3BlcmF0aW9uIHRvIGEgbmV3IG5hbWVzcGFjZSBvciBjbHVzdGVyIHJlcXVpcmVzIHRoYXQgdGhlIG9yaWdpbmFsIGluc3RhbmNlIG9mIHRoZSBhcHBsaWNhdGlvbiB0byBiZSB0YWtlbiBkb3duLiBUaGlzIGlzIHRvIGVuc3VyZSAKIyB0aGF0IHRoZSBwZWVyIGdyb3VwIGluZm9ybWF0aW9uIGNhcnJpZWQgb3ZlciBkb2VzIG5vdCBsZWFkIHRvIGNyb3NzLWluc3RhbmNlIGNvbW11bmljYXRpb24uIENsb25pbmcgb2YgdGhlIGFwcCB3aWxsIG5vdCB3b3JrLgoKIyB1bmlxdWUgZXJyb3IgY29kZXMgZm9yIGV2ZXJ5IGVycm9yIGNhc2UKZWJhc2U9MTAwCmV1c2FnZT0kKChlYmFzZSsxKSkKZWJhZHN0YWdlPSQoKGViYXNlKzIpKQplcHJlPSQoKGViYXNlKzMpKQplcG9zdD0kKChlYmFzZSs0KSkKCiMKIyBXcml0ZXMgdGhlIGdpdmVuIG1lc3NhZ2UgdG8gc3RhbmRhcmQgb3V0cHV0CiMKIyAkKiAtIFRoZSBtZXNzYWdlIHRvIHdyaXRlCiMKbXNnKCkgewogICAgZWNobyAiJCoiCn0KCiMKIyBXcml0ZXMgdGhlIGdpdmVuIGluZm9ybWF0aW9uIG1lc3NhZ2UgdG8gc3RhbmRhcmQgb3V0cHV0CiMKIyAkKiAtIFRoZSBtZXNzYWdlIHRvIHdyaXRlCiMKaW5mbygpIHsKICAgIG1zZyAiSU5GTzogJCoiCn0KCiMKIyBXcml0ZXMgdGhlIGdpdmVuIGVycm9yIG1lc3NhZ2UgdG8gc3RhbmRhcmQgZXJyb3IKIwojICQqIC0gVGhlIG1lc3NhZ2UgdG8gd3JpdGUKIwplcnJvcigpIHsKICAgIG1zZyAiRVJST1I6ICQqIiAxPiYyCn0KCiMKIyBSdW4gcXVpZXNjZSBzdGVwcyBoZXJlCiMKcXVpZXNjZSgpIHsKICAgIGluZm8gIlF1aWVzY2luZyBDYXNzYW5kcmEgLSBmbHVzaGluZyBhbGwga2V5c3BhY2VzIGFuZCB0YWJsZXMiCiAgICBub2RldG9vbCBmbHVzaAogICAgcmM9JD8KICAgIGlmIFsgJHtyY30gLW5lIDAgXTsgdGhlbgogICAgICAgIHJjPSR7ZXByZX0KICAgIGZpCiAgICByZXR1cm4gJHtyY30KfQoKIwojIFJ1biB1bnF1aWVzY2Ugc3RlcHMgaGVyZQojCnVucXVpZXNjZSgpIHsKICAgIGluZm8gIlVucXVpZXNjaW5nIENhc3NhbmRyYSIKICAgIG5vZGV0b29sIHZlcmlmeQogICAgcmM9JD8KICAgIGlmIFsgJHtyY30gLW5lIDAgXTsgdGhlbgogICAgICAgIHJjPSR7ZXBvc3R9CiAgICBmaQogICAgcmV0dXJuICR7cmN9Cn0KCiMKIyBtYWluCiMKCiMgY2hlY2sgYXJnCnN0YWdlPSQxCmlmIFsgLXogIiR7c3RhZ2V9IiBdOyB0aGVuCiAgICBlY2hvICJVc2FnZTogJDAgPHByZXxwb3N0PiIKICAgIGV4aXQgJHtldXNhZ2V9CmZpCgppZiBbICIke3N0YWdlfSIgIT0gInByZSIgXSAmJiBbICIke3N0YWdlfSIgIT0gInBvc3QiIF07IHRoZW4KICAgIGVjaG8gIkludmFsaWQgYXJnOiAke3N0YWdlfSIKICAgIGV4aXQgJHtlYmFkc3RhZ2V9CmZpCgojIGxvZyBzb21ldGhpbmcgdG8gc3Rkb3V0CmluZm8gIlJ1bm5pbmcgJDAgJHtzdGFnZX0iCgppZiBbICIke3N0YWdlfSIgPSAicHJlIiBdOyB0aGVuCiAgICBxdWllc2NlCiAgICByYz0kPwogICAgaWYgWyAke3JjfSAtbmUgMCBdOyB0aGVuCiAgICAgICAgZXJyb3IgIkVycm9yIGR1cmluZyBwcmUtc25hcHNob3QgaG9vayIKICAgIGZpCmZpCgppZiBbICIke3N0YWdlfSIgPSAicG9zdCIgXTsgdGhlbgogICAgdW5xdWllc2NlCiAgICByYz0kPwogICAgaWYgWyAke3JjfSAtbmUgMCBdOyB0aGVuCiAgICAgICAgZXJyb3IgIkVycm9yIGR1cmluZyBwb3N0LXNuYXBzaG90IGhvb2siCiAgICBmaQpmaQoKZXhpdCAke3JjfQ==", "sourceMD5Checksum": "9242a7d82682b9ef15fb460b28d1767a"}
```

```text
$ actoolkit create script -d "example script upload" testScript example.sh
{"metadata": {"labels": [], "creationTimestamp": "2022-08-02T14:41:51Z", "modificationTimestamp": "2022-08-02T14:41:51Z", "createdBy": "7cc9170d-d227-49ac-bf9e-6b080ce59524"}, "type": "application/astra-hookSource", "version": "1.0", "id": "b5cb8496-65e9-4e62-addf-bbfe08b7f3bd", "name": "testScript", "private": "false", "preloaded": "false", "sourceType": "script", "source": "IyEvYmluL2Jhc2gKZWNobyAidGhpcyBpcyBqdXN0IGFuIGV4YW1wbGUi", "sourceMD5Checksum": "8ad9d02befca7ef9a0fd51f7ec4aebe7", "description": "test upload"}
```

## Replication

The `create replication` command allows you to create a replication policy for an [application](../manage/README.md#app).  It is currently **only** supported for ACC environments.  The high level command usage is:

```text
actoolkit create replication <appID> -c <destClusterID> -n <destNamespace> \
    -s <destStorageClass> -f <replicationFrequency> -o <offset>
```

The \<appID\> argument can be gathered from a [list apps](../list/README.md#apps) command, and the \<destClusterID\> argument can be gathered from a [list clusters](../list/README.md#clusters) command.

Both the \<destStorageClass\> and \<offset\> arguments are optional.  If either are not provided, the default storage class on the destination cluster is used, and the replications are based off of 00:00.

```text
$ actoolkit create replication 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c \
    -c 3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45 -n cassandra-repl -f 30m
{"type": "application/astra-appMirror", "version": "1.0", "id": "230f80a6-6312-4d14-a708-78b6b7826a6d", "sourceAppID": "28efc6fa-324e-42fd-8cd8-e1aacd7ada2c", "sourceClusterID": "7b4620be-cc20-4680-8ae7-2048dbd872c8", "destinationClusterID": "3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45", "namespaceMapping": [{"clusterID": "7b4620be-cc20-4680-8ae7-2048dbd872c8", "namespaces": ["cassandra"]}, {"clusterID": "3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45", "namespaces": ["cassandra-repl"]}], "state": "establishing", "stateTransitions": [{"from": "establishing", "to": ["established", "deleting"]}, {"from": "established", "to": ["failingOver", "deleting"]}, {"from": "failingOver", "to": ["failedOver", "deleting"]}, {"from": "failedOver", "to": ["establishing", "deleting"]}], "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [], "transferState": "idle", "transferStateTransitions": [{"from": "transferring", "to": ["idle"]}, {"from": "idle", "to": ["transferring"]}], "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-09T14:49:55Z", "modificationTimestamp": "2022-09-09T14:49:55Z", "createdBy": "a4569807-c217-4105-abbb-04ccc5ea6047"}}
{"type": "application/astra-schedule", "version": "1.1", "id": "72cee9b9-e994-47d1-80f0-ec5cc02c7cbe", "name": "replication-schedule-knwun", "enabled": "true", "granularity": "custom", "minute": "0", "recurrenceRule": "DTSTART:20220101T000000Z\nRRULE:FREQ=MINUTELY;INTERVAL=30", "snapshotRetention": "0", "backupRetention": "0", "replicate": "true", "metadata": {"labels": [], "creationTimestamp": "2022-09-09T14:49:55Z", "modificationTimestamp": "2022-09-09T14:49:55Z", "createdBy": "a4569807-c217-4105-abbb-04ccc5ea6047"}}
```

The \<offset\> argument can be provided in either a "hh:mm" or "mm" format.  In this example, a snapshot is created and replicated at 01:22, 05:22, 09:22, and so on.

```text
$ actoolkit create replication 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 \
    -c 3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45 -n wordpress-repl -f 4h -o 1:22
{"type": "application/astra-appMirror", "version": "1.0", "id": "a0342d41-3c9c-447f-9d61-650bee68c21a", "sourceAppID": "0c6cbc25-cd47-4418-8cdb-833f1934a9c0", "sourceClusterID": "7b4620be-cc20-4680-8ae7-2048dbd872c8", "destinationClusterID": "3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45", "namespaceMapping": [{"clusterID": "7b4620be-cc20-4680-8ae7-2048dbd872c8", "namespaces": ["wordpress2"]}, {"clusterID": "3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45", "namespaces": ["wordpress-repl"]}], "state": "establishing", "stateTransitions": [{"from": "establishing", "to": ["established", "deleting"]}, {"from": "established", "to": ["failingOver", "deleting"]}, {"from": "failingOver", "to": ["failedOver", "deleting"]}, {"from": "failedOver", "to": ["establishing", "deleting"]}], "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [], "transferState": "idle", "transferStateTransitions": [{"from": "transferring", "to": ["idle"]}, {"from": "idle", "to": ["transferring"]}], "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-09T14:52:57Z", "modificationTimestamp": "2022-09-09T14:52:57Z", "createdBy": "a4569807-c217-4105-abbb-04ccc5ea6047"}}
{"type": "application/astra-schedule", "version": "1.1", "id": "a81b0cdf-af1e-4194-ab61-ccc8c8ff21ab", "name": "replication-schedule-h4fyv", "enabled": "true", "granularity": "custom", "minute": "0", "recurrenceRule": "DTSTART:20220101T012200Z\nRRULE:FREQ=HOURLY;INTERVAL=4", "snapshotRetention": "0", "backupRetention": "0", "replicate": "true", "metadata": {"labels": [], "creationTimestamp": "2022-09-09T14:52:57Z", "modificationTimestamp": "2022-09-09T14:52:57Z", "createdBy": "a4569807-c217-4105-abbb-04ccc5ea6047"}}
```

This example specifies a destination storage class of "ontap-gold" with a snapshot being created and replicated at 00:07, 00:37, 01:07, and so on.

```text
$ actoolkit create replication 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c \
    -c 3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45 -n cassandra-repl -s ontap-gold \
    -f 30m -o 7
{"type": "application/astra-appMirror", "version": "1.0", "id": "d7ab2644-ce0b-464c-b93a-e78317a3e243", "sourceAppID": "28efc6fa-324e-42fd-8cd8-e1aacd7ada2c", "sourceClusterID": "7b4620be-cc20-4680-8ae7-2048dbd872c8", "destinationClusterID": "3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45", "namespaceMapping": [{"clusterID": "7b4620be-cc20-4680-8ae7-2048dbd872c8", "namespaces": ["cassandra"]}, {"clusterID": "3ee521b3-e0dc-4d36-9fe7-3a7945e4ce45", "namespaces": ["cassandra-repl"]}], "state": "establishing", "stateTransitions": [{"from": "establishing", "to": ["established", "deleting"]}, {"from": "established", "to": ["failingOver", "deleting"]}, {"from": "failingOver", "to": ["failedOver", "deleting"]}, {"from": "failedOver", "to": ["establishing", "deleting"]}], "stateDesired": "established", "stateAllowed": ["established"], "stateDetails": [], "transferState": "idle", "transferStateTransitions": [{"from": "transferring", "to": ["idle"]}, {"from": "idle", "to": ["transferring"]}], "transferStateDetails": [], "healthState": "normal", "healthStateTransitions": [], "healthStateDetails": [], "metadata": {"labels": [], "creationTimestamp": "2022-09-09T14:59:17Z", "modificationTimestamp": "2022-09-09T14:59:17Z", "createdBy": "a4569807-c217-4105-abbb-04ccc5ea6047"}}
{"type": "application/astra-schedule", "version": "1.1", "id": "f978c627-5448-4418-b81d-093b776a0591", "name": "replication-schedule-rxs83", "enabled": "true", "granularity": "custom", "minute": "0", "recurrenceRule": "DTSTART:20220101T000700Z\nRRULE:FREQ=MINUTELY;INTERVAL=30", "snapshotRetention": "0", "backupRetention": "0", "replicate": "true", "metadata": {"labels": [], "creationTimestamp": "2022-09-09T14:59:44Z", "modificationTimestamp": "2022-09-09T14:59:44Z", "createdBy": "a4569807-c217-4105-abbb-04ccc5ea6047"}}
```

## Snapshot

The `create snapshot` command allows you to take an ad-hoc snapshot.  The command usage is:

```text
actoolkit create snapshot <optionalBackgroundArg> <appID> <snapshotName>
```

When the optional `--background`/`-b` argument is **not** specified, the command polls for the status of the snapshot operation every 5 seconds (which can be overridden by the `--pollTimer`/`-t` argument), and reports back once complete.

```text
$ actoolkit create snapshot a643b5dc-bfa0-4624-8bdd-5ad5325f20fd 20220523-cli-snap1
Starting snapshot of a643b5dc-bfa0-4624-8bdd-5ad5325f20fd
Waiting for snapshot to complete.....complete!
```

When the optional `--background`/`-b` argument **is** specified, the command simply initiates the snapshot task, and leaves it to the user to validate the snapshot completion.

```text
$ actoolkit create snapshot -b a643b5dc-bfa0-4624-8bdd-5ad5325f20fd 20220523-cli-snap2
Starting snapshot of a643b5dc-bfa0-4624-8bdd-5ad5325f20fd
Background snapshot flag selected, run 'list snapshots' to get status
$ actoolkit list snapshots
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+
| appID                                | snapshotName                      | snapshotID                           | snapshotState |
+======================================+===================================+======================================+===============+
| a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | wordpress-snapshot-20220523161542 | 04354edd-3f53-4479-9829-ca3723021c3e | completed     |
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+
| a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | 20220523-cli-snap1                | 136c0d8e-d4a7-4034-a846-021f0afc0b2b | completed     |
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+
| a643b5dc-bfa0-4624-8bdd-5ad5325f20fd | 20220523-cli-snap2                | 3cb65a44-62a1-4157-a314-3840b761c6c8 | ready         |
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+

```

## User

The `create user` command allows you to create either a **local** (for ACC environments), **LDAP** (for ACC environments), or **cloud-central** (for ACS environments) user (and associated roleBinding). The command usage is:

```text
actoolkit create user <email> <role> <-p TEMPPASSWORD | --ldap> \
    <-f optional firstName> <-l optional lastName> \
    <-a optional labelConstraint> <-n optional namespaceConstraint>
```

The role argument must be one of the following four values:

* viewer
* member
* admin
* owner

### Local Users (ACC)

For **local** (ACC environments) users, the `-p`/`--tempPassword` argument is required.  This password must be changed after the user's first login.

```text
$ actoolkit create user jdoe@example.com member -p ThisIsAStrongPass123$ -f John -l Doe
{"metadata": {"creationTimestamp": "2022-09-30T20:46:16Z", "modificationTimestamp": "2022-09-30T20:46:16Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444", "labels": []}, "type": "application/astra-user", "version": "1.2", "id": "6b1551db-b7fa-473d-a05c-43524badb11b", "authProvider": "local", "authID": "jdoe@example.com", "firstName": "John", "lastName": "Doe", "companyName": "", "email": "jdoe@example.com", "postalAddress": {"addressCountry": "", "addressLocality": "", "addressRegion": "", "streetAddress1": "", "streetAddress2": "", "postalCode": ""}, "state": "active", "sendWelcomeEmail": "false", "isEnabled": "true", "isInviteAccepted": "true", "enableTimestamp": "2022-09-30T20:46:16Z", "lastActTimestamp": ""}
{"metadata": {"creationTimestamp": "2022-09-30T20:46:16Z", "modificationTimestamp": "2022-09-30T20:46:16Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444", "labels": []}, "type": "application/astra-roleBinding", "principalType": "user", "version": "1.1", "id": "ef8e5a91-13aa-4fac-96f7-26c78d619414", "userID": "6b1551db-b7fa-473d-a05c-43524badb11b", "groupID": "00000000-0000-0000-0000-000000000000", "accountID": "61edc0b9-0695-47d2-bdeb-4ad5a4ed65e1", "role": "member", "roleConstraints": ["*"]}
{"type": "application/astra-credential", "version": "1.1", "id": "6117fa73-de5b-4976-b178-8d5a1e2352dc", "name": "6b1551db-b7fa-473d-a05c-43524badb11b", "keyType": "passwordHash", "metadata": {"creationTimestamp": "2022-09-30T20:46:16Z", "modificationTimestamp": "2022-09-30T20:46:16Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "passwordHash"}]}}
```

### LDAP Users (ACC)

For **LDAP** (ACC Environments) users, the `--ldap` argument must be specified, along with an email address that is present in your LDAP  server (see [list ldapusers](../list/README.md#ldapusers) for information on how to query LDAP for users).

```text
$ actoolkit create user michael1@netapp.com member --ldap
{"metadata": {"creationTimestamp": "2024-03-18T17:09:50Z", "modificationTimestamp": "2024-03-18T17:09:50Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": []}, "type": "application/astra-user", "version": "1.2", "id": "67939b62-cc2c-4b5f-9a38-7dd189630227", "authProvider": "ldap", "authID": "", "firstName": "michael", "lastName": "tester", "companyName": "", "email": "michael1@netapp.com", "postalAddress": {"addressCountry": "", "addressLocality": "", "addressRegion": "", "streetAddress1": "", "streetAddress2": "", "postalCode": ""}, "state": "active", "sendWelcomeEmail": "false", "isEnabled": "true", "isInviteAccepted": "true", "enableTimestamp": "2024-03-18T17:09:50Z", "lastActTimestamp": ""}
{"metadata": {"creationTimestamp": "2024-03-18T17:09:50Z", "modificationTimestamp": "2024-03-18T17:09:50Z", "createdBy": "a33e249d-45c4-4f33-8483-a8b0b5b1236d", "labels": []}, "type": "application/astra-roleBinding", "principalType": "user", "version": "1.1", "id": "347c809a-3299-49b2-b15b-dfeab33cadf9", "userID": "67939b62-cc2c-4b5f-9a38-7dd189630227", "groupID": "00000000-0000-0000-0000-000000000000", "accountID": "1792ed1d-d55f-4a98-b07d-532b17ac2e77", "role": "member", "roleConstraints": ["*"]}
```

### Cloud Central (ACS)

For **cloud-central** (ACS environments) users, the `-p`/`--tempPassword` and `--ldap` arguments are not needed.  Instead, the user will be emailed an invitation to join the account.

```text
$ actoolkit create user jdoe@example.com viewer -f John -l Doe
{"metadata": {"creationTimestamp": "2022-09-30T21:01:37Z", "modificationTimestamp": "2022-09-30T21:01:37Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": []}, "type": "application/astra-user", "version": "1.2", "id": "b7d87db3-1896-4e03-b2ad-63b873244b53", "authProvider": "cloud-central", "authID": "", "firstName": "John", "lastName": "Doe", "companyName": "", "email": "jdoe@example.com", "postalAddress": {"addressCountry": "", "addressLocality": "", "addressRegion": "", "streetAddress1": "", "streetAddress2": "", "postalCode": ""}, "state": "pending", "sendWelcomeEmail": "true", "isEnabled": "true", "isInviteAccepted": "false", "enableTimestamp": "2022-09-30T21:01:37Z", "lastActTimestamp": ""}
{"metadata": {"creationTimestamp": "2022-09-30T21:01:38Z", "modificationTimestamp": "2022-09-30T21:01:38Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": []}, "type": "application/astra-roleBinding", "principalType": "user", "version": "1.1", "id": "4d732ae4-d0cd-4c65-aee8-98efc6a88140", "userID": "b7d87db3-1896-4e03-b2ad-63b873244b53", "groupID": "00000000-0000-0000-0000-000000000000", "accountID": "fc018f3d-e807-4fa7-98d5-fbe43be9aaa0", "role": "viewer", "roleConstraints": ["*"]}
```

### Constraints

Finally, any number of labelConstraints (`-a`/`--labelConstraint`) and/or namespaceConstraints (`-n`/`--namespaceConstraint`) can be provided (note that multiple values can be provided, either with space separated values, or specifying the argument again).

```text
$ actoolkit create user jdoe@example.com member -p ThisIsAStrongPass123$ \
    -a name=jenkins -a name=cicd-jenkins \
    -n dc3e076d-e104-47cd-b986-523017e85f27 f73ccf3c-65bb-47e0-9f62-0477a4dd7e89
{"metadata": {"creationTimestamp": "2022-10-03T14:57:41Z", "modificationTimestamp": "2022-10-03T14:57:41Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444", "labels": []}, "type": "application/astra-user", "version": "1.2", "id": "52a0f1db-f1c9-469b-b173-3d4d5d85f61a", "authProvider": "local", "authID": "jdoe@example.com", "firstName": "", "lastName": "", "companyName": "", "email": "jdoe@example.com", "postalAddress": {"addressCountry": "", "addressLocality": "", "addressRegion": "", "streetAddress1": "", "streetAddress2": "", "postalCode": ""}, "state": "active", "sendWelcomeEmail": "false", "isEnabled": "true", "isInviteAccepted": "true", "enableTimestamp": "2022-10-03T14:57:41Z", "lastActTimestamp": ""}
{"metadata": {"creationTimestamp": "2022-10-03T14:57:41Z", "modificationTimestamp": "2022-10-03T14:57:41Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444", "labels": []}, "type": "application/astra-roleBinding", "principalType": "user", "version": "1.1", "id": "5e870f0d-e892-414f-942e-49001e97165e", "userID": "52a0f1db-f1c9-469b-b173-3d4d5d85f61a", "groupID": "00000000-0000-0000-0000-000000000000", "accountID": "61edc0b9-0695-47d2-bdeb-4ad5a4ed65e1", "role": "member", "roleConstraints": ["namespaces:id='dc3e076d-e104-47cd-b986-523017e85f27'.*", "namespaces:id='f73ccf3c-65bb-47e0-9f62-0477a4dd7e89'.*", "namespaces:kubernetesLabels='name=jenkins'.*", "namespaces:kubernetesLabels='name=cicd-jenkins'.*"]}
{"type": "application/astra-credential", "version": "1.1", "id": "61da64d2-d39b-47cf-b8bc-d8a3443c2cba", "name": "52a0f1db-f1c9-469b-b173-3d4d5d85f61a", "keyType": "passwordHash", "metadata": {"creationTimestamp": "2022-10-03T14:57:41Z", "modificationTimestamp": "2022-10-03T14:57:41Z", "createdBy": "2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "passwordHash"}]}}
```
