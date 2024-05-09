# List

The `list` command shows various resources known to Astra.

* [Apiresources](#apiresources)
* [Apps](#apps)
* [Assets](#assets)
* [Asups](#asups)
* [Backups](#backups)
* [Buckets](#buckets)
* [Clouds](#clouds)
* [Clusters](#clusters)
* [Credentials](#credentials)
* [Hooks](#hooks)
* [Ldapgroups](#ldapgroups)
* [Ldapusers](#ldapusers)
* [Namespaces](#namespaces)
* [Notifications](#notifications)
* [Protections](#protections)
* [Replications](#replications)
* [Rolebindings](#rolebindings)
* [Scripts](#scripts)
* [Snapshots](#snapshots)
* [Storagebackends](#storagebackends)
* [Storageclasses](#storageclasses)
* [Users](#users)

```text
$ actoolkit list -h
usage: actoolkit list [-h]
                      {apiresources,apps,applications,assets,asups,backups,buckets,appVaults,clouds,clusters,credentials,secrets,groups,hooks,exechooks,ldapgroups,ldapusers,namespaces,notifications,protections,schedules,replications,rolebindings,scripts,snapshots,storagebackends,storageclasses,users}
                      ...

options:
  -h, --help            show this help message and exit

objectType:
  {apiresources,apps,applications,assets,asups,backups,buckets,appVaults,clouds,clusters,credentials,secrets,groups,hooks,exechooks,ldapgroups,ldapusers,namespaces,notifications,protections,schedules,replications,rolebindings,scripts,snapshots,storagebackends,storageclasses,users}
    apiresources        list api resources
    apps (applications)
                        list apps
    assets              list app assets
    asups               list auto-support bundles
    backups             list backups
    buckets (appVaults)
                        list buckets
    clouds              list clouds
    clusters            list clusters
    credentials (secrets)
                        list credentials
    groups              list groups
    hooks (exechooks)   list hooks (executionHooks)
    ldapgroups          queries a connected LDAP(S) server and lists available groups
    ldapusers           queries a connected LDAP(S) server and lists available users
    namespaces          list namespaces
    notifications       list notifications
    protections (schedules)
                        list protection policies
    replications        list replication policies
    rolebindings        list role bindings
    scripts             list scripts (hookSources)
    snapshots           list snapshots
    storagebackends     list storagebackends
    storageclasses      list storageclasses
    users               list users
```

## Apiresources

`list apiresources` provides read access to Kubernetes API resources to be used for managing cluster scoped resources within an application.  API resources can also be filtered by a cluster name or ID (exact match).

Command usage:

```text
actoolkit list apiresources <optional-arguments>
```

Sample output:

```text
$ actoolkit list apiresources
+------------------------------+-----------+--------------------------------+--------------------------------------+
| group                        | version   | kind                           | clusterID                            |
+==============================+===========+================================+======================================+
| rbac.authorization.k8s.io    | v1        | ClusterRole                    | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| admissionregistration.k8s.io | v1        | MutatingWebhookConfiguration   | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| admissionregistration.k8s.io | v1        | ValidatingWebhookConfiguration | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| apiextensions.k8s.io         | v1        | CustomResourceDefinition       | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| rbac.authorization.k8s.io    | v1        | ClusterRoleBinding             | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| rbac.authorization.k8s.io    | v1        | ClusterRole                    | c9456cae-b2d4-400b-ac53-60637d57da57 |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| apiextensions.k8s.io         | v1        | CustomResourceDefinition       | c9456cae-b2d4-400b-ac53-60637d57da57 |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| rbac.authorization.k8s.io    | v1        | ClusterRoleBinding             | c9456cae-b2d4-400b-ac53-60637d57da57 |
+------------------------------+-----------+--------------------------------+--------------------------------------+
```

```text
$ actoolkit list apiresources -c prod-cluster
+------------------------------+-----------+--------------------------------+--------------------------------------+
| group                        | version   | kind                           | clusterID                            |
+==============================+===========+================================+======================================+
| rbac.authorization.k8s.io    | v1        | ClusterRole                    | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| admissionregistration.k8s.io | v1        | MutatingWebhookConfiguration   | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| admissionregistration.k8s.io | v1        | ValidatingWebhookConfiguration | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| apiextensions.k8s.io         | v1        | CustomResourceDefinition       | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| rbac.authorization.k8s.io    | v1        | ClusterRoleBinding             | 690deba1-bc57-4771-ab72-88758cab2afd |
+------------------------------+-----------+--------------------------------+--------------------------------------+
```

```text
$ actoolkit list apiresources --cluster c9456cae-b2d4-400b-ac53-60637d57da57
+------------------------------+-----------+--------------------------------+--------------------------------------+
| group                        | version   | kind                           | clusterID                            |
+==============================+===========+================================+======================================+
| rbac.authorization.k8s.io    | v1        | ClusterRole                    | c9456cae-b2d4-400b-ac53-60637d57da57 |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| apiextensions.k8s.io         | v1        | CustomResourceDefinition       | c9456cae-b2d4-400b-ac53-60637d57da57 |
+------------------------------+-----------+--------------------------------+--------------------------------------+
| rbac.authorization.k8s.io    | v1        | ClusterRoleBinding             | c9456cae-b2d4-400b-ac53-60637d57da57 |
+------------------------------+-----------+--------------------------------+--------------------------------------+
```

## Apps

`list apps` displays applications that have been defined in Astra.  Apps may also be filtered by a cluster name (exact match), cluster ID (exact match), app name filter (partial match), or namespace name (exact match).

Command usage:

```text
actoolkit list apps <optional-arguments>
```

Sample output:

```text
$ actoolkit list apps
+----------------+--------------------------------------+-----------------+----------------+--------------+
| appName        | appID                                | clusterName     | namespace      | state        |
+================+======================================+=================+================+==============+
| wordpress-east | 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | useast1-cluster | wordpress      | ready        |
+----------------+--------------------------------------+-----------------+----------------+--------------+
| wordpress-west | a8dc676e-d182-4d7c-9113-43f5a2963b54 | uswest1-cluster | wordpress-prod | ready        |
+----------------+--------------------------------------+-----------------+----------------+--------------+
| temp-clone     | ad125374-e090-425b-a048-d719b93b0feb | uswest1-cluster | clonens        | provisioning |
+----------------+--------------------------------------+-----------------+----------------+--------------+
```

```text
$ actoolkit list apps --cluster useast1-cluster
+----------------+--------------------------------------+-----------------+-------------+-------+
| appName        | appID                                | clusterName     | namespace   | state |
+================+======================================+=================+=============+=======+
| wordpress-east | 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | useast1-cluster | wordpress   | ready |
+----------------+--------------------------------------+-----------------+-------------+-------+
```

```text
$ actoolkit list apps --nameFilter word
+----------------+--------------------------------------+-----------------+----------------+-------+
| appName        | appID                                | clusterName     | namespace      | state |
+================+======================================+=================+================+=======+
| wordpress-east | 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | useast1-cluster | wordpress      | ready |
+----------------+--------------------------------------+-----------------+----------------+-------+
| wordpress-west | a8dc676e-d182-4d7c-9113-43f5a2963b54 | uswest1-cluster | wordpress-prod | ready |
+----------------+--------------------------------------+-----------------+----------------+-------+
```

```text
$ actoolkit list apps --namespace wordpress-prod
+----------------+--------------------------------------+-----------------+----------------+-------+
| appName        | appID                                | clusterName     | namespace      | state |
+================+======================================+=================+================+=======+
| wordpress-west | a8dc676e-d182-4d7c-9113-43f5a2963b54 | uswest1-cluster | wordpress-prod | ready |
+----------------+--------------------------------------+-----------------+----------------+-------+
```

## Assets

`list assets` shows a single application's assets which are managed via Astra Control.

Command usage:

```text
actoolkit list assets <appID>
```

Sample output:

```text
$ actoolkit list assets fad776eb-f80f-4a2b-b297-c4d4ff255b14
+---------------------------------+---------+-----------+-----------------------+
| assetName                       | group   | version   | kind                  |
+=================================+=========+===========+=======================+
| data-cassandra-0                |         | v1        | PersistentVolumeClaim |
+---------------------------------+---------+-----------+-----------------------+
| cassandra                       |         | v1        | Service               |
+---------------------------------+---------+-----------+-----------------------+
| cassandra-headless              |         | v1        | Service               |
+---------------------------------+---------+-----------+-----------------------+
| cassandra                       |         | v1        | Secret                |
+---------------------------------+---------+-----------+-----------------------+
| sh.helm.release.v1.cassandra.v1 |         | v1        | Secret                |
+---------------------------------+---------+-----------+-----------------------+
| cassandra                       | apps    | v1        | StatefulSet           |
+---------------------------------+---------+-----------+-----------------------+
| cassandra-metrics-conf          |         | v1        | ConfigMap             |
+---------------------------------+---------+-----------+-----------------------+
| kube-root-ca.crt                |         | v1        | ConfigMap             |
+---------------------------------+---------+-----------+-----------------------+
| cassandra-0                     |         | v1        | Pod                   |
+---------------------------------+---------+-----------+-----------------------+
| cassandra                       |         | v1        | ServiceAccount        |
+---------------------------------+---------+-----------+-----------------------+
| default                         |         | v1        | ServiceAccount        |
+---------------------------------+---------+-----------+-----------------------+
```

## Asups

`list asups` shows all auto-support bundles. They can be filtered by triggerType and whether they were automatically updloaded. Auto-support bundles can be initiated via the [create asup](../create/README.md#asup) command, and can also by copied to your local workstation with the [copy asup](../copy/README.md#asup) command.

Command usage:

```text
actoolkit list asups <optional-arguments>
```

Sample output:

```text
$ actoolkit list asups
+--------------------------------------+-----------+----------+---------------+---------------+----------------------+---------------------------+
| asupID                               | state     | upload   | uploadState   | triggerType   | dataWindowStart      | dataWindowEnd             |
+======================================+===========+==========+===============+===============+======================+===========================+
| 22339089-caff-4fe7-b1e0-0357f481ae8c | completed | false    |               | manual        | 2024-05-03T01:01:00Z | 2024-05-07T20:38:31+10:00 |
+--------------------------------------+-----------+----------+---------------+---------------+----------------------+---------------------------+
| 1c135518-ffd7-4db6-bce9-bc9ce8a15799 | completed | true     | completed     | scheduled     | 2024-05-08T00:10:00Z | 2024-05-09T00:10:00Z      |
+--------------------------------------+-----------+----------+---------------+---------------+----------------------+---------------------------+
```

```text
$ actoolkit list asups --triggerTypeFilter manual
+--------------------------------------+-----------+----------+---------------+---------------+----------------------+---------------------------+
| asupID                               | state     | upload   | uploadState   | triggerType   | dataWindowStart      | dataWindowEnd             |
+======================================+===========+==========+===============+===============+======================+===========================+
| 22339089-caff-4fe7-b1e0-0357f481ae8c | completed | false    |               | manual        | 2024-05-03T01:01:00Z | 2024-05-07T20:38:31+10:00 |
+--------------------------------------+-----------+----------+---------------+---------------+----------------------+---------------------------+
```

## Backups

`list backups` shows all app backups.  They can also be filtered by an application.

Command usage:

```text
actoolkit list backups <optional-arguments>
```

Sample output:

```text
$ actoolkit list backups
+--------------------------------------+--------------------+--------------------------------------+-------------+
| AppID                                | backupName         | backupID                             | backupState |
+======================================+====================+======================================+=============+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | hourly-mslr6-dr8rl | c695dfe2-5245-49a1-8a79-8d5c49deac5e | completed   |
+--------------------------------------+--------------------+--------------------------------------+-------------+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | hourly-mslr6-jjw1g | ddb30a46-fca9-4705-8b89-31f87aa6c20b | ready       |
+--------------------------------------+--------------------+--------------------------------------+-------------+
| a8dc676e-d182-4d7c-9113-43f5a2963b54 | hourly-vydir-roxw8 | ec3cbcb7-cc27-43da-b670-7cf8b2416552 | completed   |
+--------------------------------------+--------------------+--------------------------------------+-------------+
| a8dc676e-d182-4d7c-9113-43f5a2963b54 | hourly-vydir-n1hfv | b1a74715-680a-4217-971e-d4deabce72e0 | ready       |
+--------------------------------------+--------------------+--------------------------------------+-------------+
```

```text
$ actoolkit list backups --app wordpress
+--------------------------------------+--------------------+--------------------------------------+-------------+
| AppID                                | backupName         | backupID                             | backupState |
+======================================+====================+======================================+=============+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | hourly-mslr6-dr8rl | c695dfe2-5245-49a1-8a79-8d5c49deac5e | completed   |
+--------------------------------------+--------------------+--------------------------------------+-------------+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | hourly-mslr6-jjw1g | ddb30a46-fca9-4705-8b89-31f87aa6c20b | ready       |
+--------------------------------------+--------------------+--------------------------------------+-------------+
```

## Buckets

The `list buckets` command shows all the object storage buckets available to Astra Control to store backups.  It also has several optional arguments to minimize output.

Command usage:

```text
actoolkit list buckets
```

Sample output:

```text
$ actoolkit list buckets
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| bucketID                             | name                            | credentialID                         | provider   | state     |   retentionTime |
+======================================+=================================+======================================+============+===========+=================+
| 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac | astra-gcp-backup-fbe43be9aaa0   | 987ab72d-3e48-4b9f-879f-1d14059efa8e | gcp        | available |          259200 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| ceb69272-ee61-4876-aef5-d6cc21a3e20c | astra-azure-backup-fbe43be9aaa0 | ad544328-1fbb-48af-bff8-ebb21e874540 | azure      | available |                 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| 225080bb-ff5b-4cb6-a834-50604904bfc9 | gcp-secondary-fbe43be9aaa0      | 987ab72d-3e48-4b9f-879f-1d14059efa8e | gcp        | available |                 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
```

```text
$ actoolkit list buckets --provider gcp
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| bucketID                             | name                            | credentialID                         | provider   | state     |   retentionTime |
+======================================+=================================+======================================+============+===========+=================+
| 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac | astra-gcp-backup-fbe43be9aaa0   | 987ab72d-3e48-4b9f-879f-1d14059efa8e | gcp        | available |                 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| 225080bb-ff5b-4cb6-a834-50604904bfc9 | gcp-secondary-fbe43be9aaa0      | 987ab72d-3e48-4b9f-879f-1d14059efa8e | gcp        | available |          259200 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
```

```text
$ actoolkit list buckets --nameFilter backup
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| bucketID                             | name                            | credentialID                         | provider   | state     |   retentionTime |
+======================================+=================================+======================================+============+===========+=================+
| 361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac | astra-gcp-backup-fbe43be9aaa0   | 987ab72d-3e48-4b9f-879f-1d14059efa8e | gcp        | available |          259200 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
| ceb69272-ee61-4876-aef5-d6cc21a3e20c | astra-azure-backup-fbe43be9aaa0 | ad544328-1fbb-48af-bff8-ebb21e874540 | azure      | available |                 |
+--------------------------------------+---------------------------------+--------------------------------------+------------+-----------+-----------------+
```

## Clouds

`list clouds` shows the clouds that have been added to Astra.  Currently only displaying clouds is possible through the SDK, please utilize the UI for adding or removing clouds.

Command usage:

```text
actoolkit list clouds
```

Sample output:

```text
$ actoolkit list clouds
+-------------+--------------------------------------+-----------+
| cloudName   | cloudID                              | cloudType |
+=============+======================================+===========+
| GCP         | 0ec2e027-80bc-426a-b844-692de243b29e | GCP       |
+-------------+--------------------------------------+-----------+
| Azure       | 7b8d4252-293c-4c70-b101-7fd6b7d08e15 | Azure     |
+-------------+--------------------------------------+-----------+
| AWS         | 929befc5-7342-4391-bb5c-a5ecbaf6764a | AWS       |
+-------------+--------------------------------------+-----------+
```

```text
$ actoolkit list clouds --cloudType GCP
+-------------+--------------------------------------+-----------+
| cloudName   | cloudID                              | cloudType |
+=============+======================================+===========+
| GCP         | 0ec2e027-80bc-426a-b844-692de243b29e | GCP       |
+-------------+--------------------------------------+-----------+
```

## Clusters

`list clusters` shows all clusters deployed within the clouds managed by Astra.  By default both managed and unmanaged clusters are displayed, with arguments for hiding either.  Additionaly a partial match name filter argument is possible to minimize output.

Command usage:

```text
actoolkit list clusters <optional-arguments>
```

Sample output:

```text
$ actoolkit list clusters
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
| clusterName        | clusterID                            | clusterType   | location      | state   | managedState  | defaultBucketID                      |
+====================+======================================+===============+===============+=========+===============+======================================+
| prod-cluster       | 062728da-ef0c-4dc2-83f9-bedb07c30511 | gke           | us-east4-a    | running | managed       | 5758451c-f3ad-4061-8396-0cf96016a11e |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
| dr-cluster         | 001007b8-315a-4b06-be51-4933fc4363fe | gke           | us-central1-b | running | managed       |                                      |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
| aks-eastus-cluster | 2d326da8-6f87-4f1f-91f9-1efe481854a7 | aks           | eastus        | running | unmanaged     |                                      |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
```

```text
$ actoolkit list clusters --hideManaged
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+-------------------+
| clusterName        | clusterID                            | clusterType   | location      | state   | managedState  | defaultBucketID   |
+====================+======================================+===============+===============+=========+===============+===================+
| aks-eastus-cluster | 2d326da8-6f87-4f1f-91f9-1efe481854a7 | aks           | eastus        | running | unmanaged     |                   |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+-------------------+
```

```text
$ actoolkit list clusters --hideUnmanaged
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
| clusterName        | clusterID                            | clusterType   | location      | state   | managedState  | defaultBucketID                      |
+====================+======================================+===============+===============+=========+===============+======================================+
| prod-cluster       | 062728da-ef0c-4dc2-83f9-bedb07c30511 | gke           | us-east4-a    | running | managed       | 5758451c-f3ad-4061-8396-0cf96016a11e |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
| dr-cluster         | 001007b8-315a-4b06-be51-4933fc4363fe | gke           | us-central1-b | running | managed       |                                      |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+--------------------------------------+
```

```text
$ actoolkit list clusters --nameFilter east
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+-------------------+
| clusterName        | clusterID                            | clusterType   | location      | state   | managedState  | defaultBucketID   |
+====================+======================================+===============+===============+=========+===============+===================+
| aks-eastus-cluster | 2d326da8-6f87-4f1f-91f9-1efe481854a7 | aks           | eastus        | running | unmanaged     |                   |
+--------------------+--------------------------------------+---------------+---------------+---------+---------------+-------------------+
```

## Credentials

The `list credentials` command shows all credentials within Astra Control.  It can also be filtered to only show kubeconfigs.

```text
actoolkit list credentials <optional-arguments>
```

Sample output:

```text
$ actoolkit list credentials
+------------------------+--------------------------------------+-----------------+-------------+---------------+
| credName               | credID                               | credType        | cloudName   | clusterName   |
+========================+======================================+=================+=============+===============+
| astragcptmedemo        | 987ab72d-3e48-4b9f-879f-1d14059efa8e | service-account | GCP         | N/A           |
+------------------------+--------------------------------------+-----------------+-------------+---------------+
| kubeconfig             | aa4a8f75-1568-49ec-a450-b1b021e9a696 | kubeconfig      | GCP         | prod-cluster  |
+------------------------+--------------------------------------+-----------------+-------------+---------------+
| AzureTMEDemo2          | ad544328-1fbb-48af-bff8-ebb21e874540 | service-account | Azure       | N/A           |
+------------------------+--------------------------------------+-----------------+-------------+---------------+
| AWS-astra-tme-demo     | f4c061fd-b4c8-4dcd-8b3f-317b07fccd0c | service-account | AWS         | N/A           |
+------------------------+--------------------------------------+-----------------+-------------+---------------+
```

```text
$ actoolkit list credentials -k
+------------+--------------------------------------+------------+-------------+---------------+
| credName   | credID                               | credType   | cloudName   | clusterName   |
+============+======================================+============+=============+===============+
| kubeconfig | aa4a8f75-1568-49ec-a450-b1b021e9a696 | kubeconfig | GCP         | prod-cluster  |
+------------+--------------------------------------+------------+-------------+---------------+
```

## Hooks

`list hooks` shows all application execution hooks.  They can also be filtered by an application.

Command usage:

```text
actoolkit list hooks <optional-arguments>
```

Sample output:

```text
$ actoolkit list hooks
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
| appID                                | hookName                   | hookID                               | matchingImages                                 |
+======================================+============================+======================================+================================================+
| eebd59f2-e9b3-47b0-b0e8-1306d805f104 | cassandra-pre-snap         | 3e9bb6f4-9433-4dc3-b256-cf9837aeb2e7 | docker.io/bitnami/cassandra:4.0.5-debian-11-r4 |
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
| eebd59f2-e9b3-47b0-b0e8-1306d805f104 | cassandra-post-snap        | 50f0ece4-43c8-42a6-8826-b438e476883c | docker.io/bitnami/cassandra:4.0.5-debian-11-r4 |
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
| 7b647ab6-834b-4553-9b23-02ecdd8562f7 | wordpress-mariadb-pre-snap | 8f748130-5202-45d3-9e86-0cf0e8ee97c2 | docker.io/bitnami/mariadb:10.6.8-debian-11-r20 |
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
```

```text
$ actoolkit list hooks --app cassandra
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
| appID                                | hookName                   | hookID                               | matchingImages                                 |
+======================================+============================+======================================+================================================+
| eebd59f2-e9b3-47b0-b0e8-1306d805f104 | cassandra-pre-snap         | 3e9bb6f4-9433-4dc3-b256-cf9837aeb2e7 | docker.io/bitnami/cassandra:4.0.5-debian-11-r4 |
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
| eebd59f2-e9b3-47b0-b0e8-1306d805f104 | cassandra-post-snap        | 50f0ece4-43c8-42a6-8826-b438e476883c | docker.io/bitnami/cassandra:4.0.5-debian-11-r4 |
+--------------------------------------+----------------------------+--------------------------------------+------------------------------------------------+
```

## Ldapgroups

`list ldapgroups` allows you to query your LDAP server to list available groups. Since responses can be quite large depending on the organization size, response size is limited by default, and using filters are recommended.

Command usage:

```text
actoolkit list ldapgroups <-l LIMIT> <--continue continue-token> \
    <--matchType {partial,exact}> <--cnFilter CNFILTER> <--dnFilter DNFILTER>
```

The available arguments are as follows:

* `-l`/`--limit`: the maximum number of responses to return (default is 25)
* `--continue`: when the number of responses from the LDAP server exceeds the `limit` specified, a `continue` token will be provided with the output. Specify this token with the `--continue` argument to have the next page of values in the response.
* Filters (multiple filters are treated as logical AND):
  * `--matchType`: whether the filters are treated as `partial` or `exact` matches (partial is equivalent to using `in` keyword, exact is `eq`)
  * `--cnFilter`: filter LDAP groups by common name
  * `--dnFilter`: filter LDAP groups by distinguished name

Sample output:

Limiting the response to 3 entries:

```text
$ actoolkit list ldapgroups -l 3
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
| ldapGroupID                          | cn                                   | dn                                                                              |
+======================================+======================================+=================================================================================+
| cbd5f408-5353-4e3c-9e8b-36f05c861b5c | 01333abe-b88b-4b44-81ae-c931ed32ee6f | CN=01333abe-b88b-4b44-81ae-c931ed32ee6f,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
| 7eafe1d4-9a73-4015-af56-988e5e5537f3 | 0169e839-3122-41cd-a268-e14551482846 | CN=0169e839-3122-41cd-a268-e14551482846,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
| 5fbb46b9-e2e7-421a-b521-707917e49a11 | 017ea5dd-b437-49a2-9baa-8b88b9ba3ed1 | CN=017ea5dd-b437-49a2-9baa-8b88b9ba3ed1,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
continue-token: eyJjb2xsZWN0aW9uSW5kZXgiOjZ9
```

Utilizing a continue token to list the next page:

```text
$ actoolkit list ldapgroups -l 3 --continue eyJjb2xsZWN0aW9uSW5kZXgiOjZ9
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
| ldapGroupID                          | cn                                   | dn                                                                              |
+======================================+======================================+=================================================================================+
| 21692657-fa8b-4f84-a582-3f79af507330 | 048c8526-de0d-4e13-999d-a77b8ce70105 | CN=048c8526-de0d-4e13-999d-a77b8ce70105,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
| 2d53fab6-f736-4e8b-bf5a-1a9f96106190 | 050ed45f-8845-4023-a43a-30b139812a01 | CN=050ed45f-8845-4023-a43a-30b139812a01,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
| e4182157-e3ea-465d-8ff0-cd5123b7bdf9 | 052a959b-1639-4afe-ad9a-5eb317e0c558 | CN=052a959b-1639-4afe-ad9a-5eb317e0c558,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+--------------------------------------+---------------------------------------------------------------------------------+
```

Filtering by common name:

```text
$ actoolkit list ldapgroups --dn michael
+--------------------------------------+---------+----------------------------------------------------+
| ldapGroupID                          | cn      | dn                                                 |
+======================================+=========+====================================================+
| 3a4b7bf6-8dbf-48ac-be95-796308d6d48c | michael | CN=michael,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+---------+----------------------------------------------------+
```

## Ldapusers

`list ldapusers` allows you to query your LDAP server to list available users. Since responses can be quite large depending on the organization size, response size is limited by default, and using filters are recommended.

Command usage:

```text
actoolkit list ldapusers <-l LIMIT> <--continue continue-token> \
    <--matchType {partial,exact}> <--cnFilter CNFILTER> <-e EMAILFILTER> \
    <--firstNameFilter FIRSTNAMEFILTER> <--lastNameFilter LASTNAMEFILTER>
```

The available arguments are as follows:

* `-l`/`--limit`: the maximum number of responses to return (default is 25)
* `--continue`: when the number of responses from the LDAP server exceeds the `limit` specified, a `continue` token will be provided with the output. Specify this token with the `--continue` argument to have the next page of values in the response.
* Filters (multiple filters are treated as logical AND):
  * `--matchType`: whether the filters are treated as `partial` or `exact` matches (partial is equivalent to using `in` keyword, exact is `eq`)
  * `--cnFilter`: filter LDAP users by common name
  * `-e`/`--emailFilter`: filter LDAP users by email address
  * `--firstNameFilter`: filter LDAP users by first name
  * `--lastNameFilter`: filter LDAP users by last name

Sample output:

Limiting the response to 2 entries:

```text
$ actoolkit list ldapusers -l 2
+--------------------------------------+-------------------------------------------------+---------------+------------+--------------------------------------+---------------------------------------------------------------------------------+
| ldapUserID                           | email                                           | firstName     | lastName   | cn                                   | dn                                                                              |
+======================================+=================================================+===============+============+======================================+=================================================================================+
| a9ac008f-65c7-4706-9993-c5bb97df4d2f | 00a67be5-f978-45a9-9f0f-7353fc99aa8d@netapp.com | ldap-viewer-0 | group      | 00a67be5-f978-45a9-9f0f-7353fc99aa8d | CN=00a67be5-f978-45a9-9f0f-7353fc99aa8d,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+-------------------------------------------------+---------------+------------+--------------------------------------+---------------------------------------------------------------------------------+
| b585ad27-1608-4410-8ceb-da46bdd236fe | 00d2b99f-2321-4d97-824e-f75e00af0343@netapp.com | ldap-admin-0  | group      | 00d2b99f-2321-4d97-824e-f75e00af0343 | CN=00d2b99f-2321-4d97-824e-f75e00af0343,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+-------------------------------------------------+---------------+------------+--------------------------------------+---------------------------------------------------------------------------------+
continue-token: eyJjb2xsZWN0aW9uSW5kZXgiOjd9
```

Utilizing a continue token to list the next page:

```text
$ actoolkit list ldapusers -l 2 --continue eyJjb2xsZWN0aW9uSW5kZXgiOjd9
+--------------------------------------+-------------------------------------------------+--------------+------------+--------------------------------------+---------------------------------------------------------------------------------+
| ldapUserID                           | email                                           | firstName    | lastName   | cn                                   | dn                                                                              |
+======================================+=================================================+==============+============+======================================+=================================================================================+
| 3022293a-9d84-406f-9eab-059fc19121f7 | 02d81198-c93d-47e6-a58c-ef4d247c4550@netapp.com | ldap-owner-0 | no-group   | 02d81198-c93d-47e6-a58c-ef4d247c4550 | CN=02d81198-c93d-47e6-a58c-ef4d247c4550,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+-------------------------------------------------+--------------+------------+--------------------------------------+---------------------------------------------------------------------------------+
| 36be515f-1e4d-46cb-8a0a-42d4d4a51ed8 | 02e79be7-b100-4cd0-983b-bf44e58d8876@netapp.com | ldap-owner-0 | group      | 02e79be7-b100-4cd0-983b-bf44e58d8876 | CN=02e79be7-b100-4cd0-983b-bf44e58d8876,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+-------------------------------------------------+--------------+------------+--------------------------------------+---------------------------------------------------------------------------------+
```

Filtering by email:

```text
$ actoolkit list ldapusers -e michael
+--------------------------------------+---------------------+---------------+------------+----------------+-----------------------------------------------------------+
| ldapUserID                           | email               | firstName     | lastName   | cn             | dn                                                        |
+======================================+=====================+===============+============+================+===========================================================+
| a880dbe5-af89-475a-8785-a9cbb54407fd | michael1@netapp.com | michael       | tester     | michael tester | CN=michael tester,OU=Users,OU=e2e,DC=astra-example,DC=com |
+--------------------------------------+---------------------+---------------+------------+----------------+-----------------------------------------------------------+
```

## Namespaces

`list namespaces` shows all non-system namespaces of all of the managed clusters.  They can also be filtered by:

* `--clusterID`/`-c`: show namespaces only from the matching cluster ID
* `--nameFilter`/`-f`: show namespaces which *contain* the filter provided (`ss` would match on both `cassandra` and `wordpress`)
* `--showRemoved`/`-r`: *also* show namespaces which are in a `removed` namespaceState
* `--unassociated`/`-u`: *only* show namespaces which do not have any associated apps
* `--minutes`/`-m`: show namespaces only created within the last X minutes

Command usage:

```text
actoolkit list namespaces <optional-arguments>
```

Sample output:

```text
$ actoolkit list namespaces
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| name      | namespaceID                          | namespaceState | associatedApps | clusterID                            |
+===========+======================================+================+================+======================================+
| default   | 06951563-6f6f-41aa-a612-6a8e95646737 | discovered     | jfrog, gitlab  | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| default   | 06951563-6f6f-41aa-a612-6a8e95646737 | discovered     |                | b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| cassandra | 0c81f720-ab01-42a5-bb48-8bb3abab8817 | discovered     | cassandra      | b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| wordpress | 1d1f210a-f37a-4474-b8df-1b4605090f10 | discovered     | wordpress      | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
```

```text
$ actoolkit list namespaces --clusterID af0aecb9-9b18-473f-b417-54fb38e1e28d
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| name      | namespaceID                          | namespaceState | associatedApps | clusterID                            |
+===========+======================================+================+================+======================================+
| default   | 06951563-6f6f-41aa-a612-6a8e95646737 | discovered     | jfrog, gitlab  | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| wordpress | 1d1f210a-f37a-4474-b8df-1b4605090f10 | discovered     | wordpress      | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
```

```text
$ actoolkit list namespaces --nameFilter word
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| name      | namespaceID                          | namespaceState | associatedApps | clusterID                            |
+===========+======================================+================+================+======================================+
| wordpress | 1d1f210a-f37a-4474-b8df-1b4605090f10 | discovered     | wordpress      | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
```

```text
$ actoolkit list namespaces --showRemoved
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
| name           | namespaceID                          | namespaceState | associatedApps | clusterID                            |
+================+======================================+================+================+======================================+
| default        | 06951563-6f6f-41aa-a612-6a8e95646737 | discovered     | jfrog, gitlab  | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
| default        | 06951563-6f6f-41aa-a612-6a8e95646737 | discovered     |                | b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d |
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
| cassandra      | 0c81f720-ab01-42a5-bb48-8bb3abab8817 | discovered     | cassandra      | b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d |
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
| wordpress      | 1d1f210a-f37a-4474-b8df-1b4605090f10 | discovered     | wordpress      | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
| wordpressclone | 9d54366c-ba9b-46e6-8dec-3bbc55699ffd | removed        | wordpressclone | af0aecb9-9b18-473f-b417-54fb38e1e28d |
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
```

```text
$ actoolkit list namespaces --unassociated
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
| name           | namespaceID                          | namespaceState | associatedApps | clusterID                            |
+================+======================================+================+================+======================================+
| default        | 06951563-6f6f-41aa-a612-6a8e95646737 | discovered     |                | b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d |
+----------------+--------------------------------------+----------------+----------------+--------------------------------------+
```

```text
$ actoolkit list namespaces --minutes 60
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
| name      | namespaceID                          | namespaceState | associatedApps | clusterID                            |
+===========+======================================+================+================+======================================+
| cassandra | 0c81f720-ab01-42a5-bb48-8bb3abab8817 | discovered     | cassandra      | b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d |
+-----------+--------------------------------------+----------------+----------------+--------------------------------------+
```

## Notifications

`list notifications` shows all of the notifications of an Astra Control environment.  Due to the likelyhood of a large number of results, it is recommended to make use of filters:

* `--limit`/`-l`: limit the output to only show the last X number of notifications (implemented server-side)
* `--offset`/`-o`: typically used in conjunction with `--limit`, this "skips" the first X number of notifications (implemented server-side)
* `--minutes`/`-m`: show notifications only created within the last X minutes (this is implemented client-side, so if used without `--limit` and `--offset`, this can be an expensive operation)
* `--severity`/`-s`: only show notifications with a matching severity of either `informational`, `warning`, or `critical` ((this is implemented client-side, so if used without `--limit` and `--offset`, this can be an expensive operation))

Command usage:

```text
actoolkit list notifications <optional-arguments>
```

Sample output:

```text
$ actoolkit list notifications
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| notificationID                       | summary                                                            | severity      | eventTime            |
+======================================+====================================================================+===============+======================+
| 706f1a18-c18d-4e52-87dc-00b62e413e67 | Application removed                                                | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| a86aa237-394c-48e8-95aa-940d63742daf | Application removed                                                | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| 9fa774dc-8ba7-4fff-a46b-18ed3cae17c4 | Application removed                                                | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| 75651887-99c6-4d7e-89dc-2d0af1006c3e | Application removed                                                | informational | 2022-11-29T15:28:48Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
... output omitted ...
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| 3e149c65-88e4-4ad6-a6b0-ca5a50d6516d | Failure in discovering cluster                                     | informational | 2022-04-28T20:39:01Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| fff6d2bd-3f24-47a2-a2f1-8a13d7862ee5 | Application backup failed                                          | warning       | 2022-04-28T20:04:09Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
| 8d1d98f5-17df-47e8-baf1-7370b8ae2cfa | Pre-snapshot execution hook 'NetApp-MariaDB-pre-snapshot' failed   | warning       | 2022-04-28T20:01:47Z |
+--------------------------------------+--------------------------------------------------------------------+---------------+----------------------+
pre-filtered count: 648
```

```text
$ actoolkit list notifications -l 5
+--------------------------------------+---------------------------------+---------------+----------------------+
| notificationID                       | summary                         | severity      | eventTime            |
+======================================+=================================+===============+======================+
| 706f1a18-c18d-4e52-87dc-00b62e413e67 | Application removed             | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| a86aa237-394c-48e8-95aa-940d63742daf | Application removed             | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 9fa774dc-8ba7-4fff-a46b-18ed3cae17c4 | Application removed             | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 75651887-99c6-4d7e-89dc-2d0af1006c3e | Application removed             | informational | 2022-11-29T15:28:48Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 28251b11-503d-4070-a754-6fd7f606df81 | Application not cloned/restored | warning       | 2022-11-29T15:05:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
pre-filtered count: 648
```

```text
$ actoolkit list notifications -l 5 -o 5
+--------------------------------------+---------------------------------+---------------+----------------------+
| notificationID                       | summary                         | severity      | eventTime            |
+======================================+=================================+===============+======================+
| bf633249-f3de-4bfa-a98f-f42c2f0c45b5 | Clone wordpress-backup failed   | warning       | 2022-11-29T15:05:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 580243fa-e3fe-41be-b69e-836f8ed15b46 | Application removed             | informational | 2022-11-29T14:50:03Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 0715a53d-5a56-41cf-8f7b-5bfb60910ebb | Application not cloned/restored | warning       | 2022-11-29T03:55:05Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 76d74de3-4a7d-4197-bbdd-687378b32455 | Clone wordpress-clone failed    | warning       | 2022-11-29T03:55:05Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 3a96e0d5-bda9-41de-bd6f-0f48fc762441 | Schedule created                | informational | 2022-11-29T01:57:59Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
pre-filtered count: 648
```

```text
$ actoolkit list notifications -m 300
+--------------------------------------+---------------------------------+---------------+----------------------+
| notificationID                       | summary                         | severity      | eventTime            |
+======================================+=================================+===============+======================+
| 706f1a18-c18d-4e52-87dc-00b62e413e67 | Application removed             | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| a86aa237-394c-48e8-95aa-940d63742daf | Application removed             | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 9fa774dc-8ba7-4fff-a46b-18ed3cae17c4 | Application removed             | informational | 2022-11-29T15:50:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 75651887-99c6-4d7e-89dc-2d0af1006c3e | Application removed             | informational | 2022-11-29T15:28:48Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 28251b11-503d-4070-a754-6fd7f606df81 | Application not cloned/restored | warning       | 2022-11-29T15:05:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| bf633249-f3de-4bfa-a98f-f42c2f0c45b5 | Clone wordpress-backup failed   | warning       | 2022-11-29T15:05:33Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
| 580243fa-e3fe-41be-b69e-836f8ed15b46 | Application removed             | informational | 2022-11-29T14:50:03Z |
+--------------------------------------+---------------------------------+---------------+----------------------+
pre-filtered count: 648
```

```text
$ actoolkit list notifications -s critical
+--------------------------------------+--------------------+------------+----------------------+
| notificationID                       | summary            | severity   | eventTime            |
+======================================+====================+============+======================+
| 07a9c65d-ae1c-42fb-ac19-78dc3598b2e1 | Cluster removed    | critical   | 2022-11-10T09:38:11Z |
+--------------------------------------+--------------------+------------+----------------------+
| aa72bd6f-f676-4319-81a0-624fd57e4d8c | Cluster removed    | critical   | 2022-11-06T21:12:10Z |
+--------------------------------------+--------------------+------------+----------------------+
| bb51eed0-c33a-45f6-b01a-249d4fbda733 | Cluster removed    | critical   | 2022-11-02T17:10:00Z |
+--------------------------------------+--------------------+------------+----------------------+
| cda82c7e-e210-4495-8d34-729906dce0f6 | Cluster removed    | critical   | 2022-10-10T16:27:32Z |
+--------------------------------------+--------------------+------------+----------------------+
| a09ed194-5fc7-404a-9321-c412ff24e66d | Cluster removed    | critical   | 2022-09-22T18:47:50Z |
+--------------------------------------+--------------------+------------+----------------------+
| b610187f-11ab-4307-a401-0e6593b5340c | Cluster removed    | critical   | 2022-06-22T14:37:01Z |
+--------------------------------------+--------------------+------------+----------------------+
```

## Protections

`list protections` shows all of the protecion policies for all apps managed by Astra Control.  The command can also be modified to only display a single application's protection policies.

Command usage:

```text
actoolkit list protections <optional-arguments>
```

Sample output:

```text
$ actoolkit list protections
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| appID                                | protectionID                         | granularity   |   minute | hour   | dayOfWeek   | dayOfMonth   |   snapRetention |   backupRetention |
+======================================+======================================+===============+==========+========+=============+==============+=================+===================+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | 19f100be-e0a0-4cf6-a7c8-9b90e6d98d28 | hourly        |        0 |        |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | 5f219662-f2df-479c-9496-04994e6fb99d | daily         |        0 | 2      |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | c29f08bc-e655-4f5e-9fcc-609ac1b03d06 | weekly        |        0 | 2      | 0           |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | e598cde7-743c-4eb4-bdb4-c7952bf031ab | monthly       |        0 | 2      |             | 1            |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 | abc3c28b-d8bc-4a91-9aa7-18c3a2db6e8b | hourly        |        0 |        |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 | 28d11b8e-740f-4e92-8f35-98c286e7b3d3 | daily         |        0 | 2      |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 | 89f42127-0882-45ed-8989-02588d50c72a | weekly        |        0 | 2      | 0           |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 0c6cbc25-cd47-4418-8cdb-833f1934a9c0 | 43f7e235-65f5-4973-a389-8b35222e0cab | monthly       |        0 | 2      |             | 1            |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
```

```text
$ actoolkit list protections -a 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| appID                                | protectionID                         | granularity   |   minute | hour   | dayOfWeek   | dayOfMonth   |   snapRetention |   backupRetention |
+======================================+======================================+===============+==========+========+=============+==============+=================+===================+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | 19f100be-e0a0-4cf6-a7c8-9b90e6d98d28 | hourly        |        0 |        |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | 5f219662-f2df-479c-9496-04994e6fb99d | daily         |        0 | 2      |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | c29f08bc-e655-4f5e-9fcc-609ac1b03d06 | weekly        |        0 | 2      | 0           |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | e598cde7-743c-4eb4-bdb4-c7952bf031ab | monthly       |        0 | 2      |             | 1            |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
```

```text
$ actoolkit list protections -a cassandra
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| appID                                | protectionID                         | granularity   |   minute | hour   | dayOfWeek   | dayOfMonth   |   snapRetention |   backupRetention |
+======================================+======================================+===============+==========+========+=============+==============+=================+===================+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | 19f100be-e0a0-4cf6-a7c8-9b90e6d98d28 | hourly        |        0 |        |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | 5f219662-f2df-479c-9496-04994e6fb99d | daily         |        0 | 2      |             |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | c29f08bc-e655-4f5e-9fcc-609ac1b03d06 | weekly        |        0 | 2      | 0           |              |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
| 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | e598cde7-743c-4eb4-bdb4-c7952bf031ab | monthly       |        0 | 2      |             | 1            |               1 |                 1 |
+--------------------------------------+--------------------------------------+---------------+----------+--------+-------------+--------------+-----------------+-------------------+
```

## Replications

The `list replications` command shows all of the snap-mirror application replications configured on Astra Control Center.  The command can also be modified to only display a single application's replication policies.

Command usage:

```text
actoolkit list replications <optional-arguments>
```

Sample output:

```text
$ actoolkit list replications
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
| replicationID                        | sourceAppID                          | state       | sourceNamespace   | destNamespace   |
+======================================+======================================+=============+===================+=================+
| d069da86-d629-43df-875d-a869135ef196 | f0d5e243-5bfe-4aa5-9c98-f1d3da83110d | established | wordpress         | wordpress-repl  |
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
| d7ab2644-ce0b-464c-b93a-e78317a3e243 | 28efc6fa-324e-42fd-8cd8-e1aacd7ada2c | failedOver  | cassandra         | cassandra-repl  |
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
```

```text
$ actoolkit list replications -a wordpress
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
| replicationID                        | sourceAppID                          | state       | sourceNamespace   | destNamespace   |
+======================================+======================================+=============+===================+=================+
| d069da86-d629-43df-875d-a869135ef196 | f0d5e243-5bfe-4aa5-9c98-f1d3da83110d | established | wordpress         | wordpress-repl  |
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
```

```text
$ actoolkit list replications -a f0d5e243-5bfe-4aa5-9c98-f1d3da83110d
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
| replicationID                        | sourceAppID                          | state       | sourceNamespace   | destNamespace   |
+======================================+======================================+=============+===================+=================+
| d069da86-d629-43df-875d-a869135ef196 | f0d5e243-5bfe-4aa5-9c98-f1d3da83110d | established | wordpress         | wordpress-repl  |
+--------------------------------------+--------------------------------------+-------------+-------------------+-----------------+
```

## Rolebindings

`list rolebindings` shows all of the role bindings in the account, which are tightly coupled with [users](#users).

Command usage:

```text
actoolkit list rolebindings <optional-arguments>
```

Sample output:

```text
$ actoolkit list rolebindings
+--------------------------------------+-----------------+--------------------------------------+--------+-----------------------------------------+
| roleBindingID                        | principalType   | userID                               | role   | roleConstraints                         |
+======================================+=================+======================================+========+=========================================+
| 5c278d5c-1d10-427a-b4e8-e5f3ef343e07 | user            | 2b7a3f5e-c7da-4835-bfe2-6dd51c9b1444 | owner  | *                                       |
+--------------------------------------+-----------------+--------------------------------------+--------+-----------------------------------------+
| d9e34b4b-899d-4b98-b5ea-bfbcca8ac394 | user            | 74563903-c15a-471e-9320-4a447c8e400c | member | namespaces:kubernetesLabels='app=dev'.* |
+--------------------------------------+-----------------+--------------------------------------+--------+-----------------------------------------+
| 27dffe3f-d9ae-470c-8f96-917cad71c4d2 | user            | bb06c170-8dbd-40be-99aa-3b3114434705 | viewer | *                                       |
+--------------------------------------+-----------------+--------------------------------------+--------+-----------------------------------------+
| fc6ceeb9-895e-44af-97aa-919168763937 | user            | 109403b2-3bcb-4967-a1b6-200c4f1382eb | member | *                                       |
+--------------------------------------+-----------------+--------------------------------------+--------+-----------------------------------------+
```

```text
$ actoolkit list rolebindings -i bb06c170-8dbd-40be-99aa-3b3114434705
+--------------------------------------+-----------------+--------------------------------------+--------+-------------------+
| roleBindingID                        | principalType   | userID                               | role   | roleConstraints   |
+======================================+=================+======================================+========+===================+
| 27dffe3f-d9ae-470c-8f96-917cad71c4d2 | user            | bb06c170-8dbd-40be-99aa-3b3114434705 | viewer | *                 |
+--------------------------------------+-----------------+--------------------------------------+--------+-------------------+
```

## Scripts

`list scripts` shows all of the account's scripts, which are used with [execution hooks](../create/README.md#execution-hook).  With the `-s`/`--getScriptSource` argument, the body of the script(s) will be outputted (scripts can be optionally filtered with the `-f`/`--nameFilter` argument).

Command usage:

```text
actoolkit list scripts <optional-arguments>
```

Sample output:

```text
$ actoolkit list scripts
+---------------+--------------------------------------+----------------------------------+
| scriptName    | scriptID                             | description                      |
+===============+======================================+==================================+
| postgres      | e3daff37-5611-4f33-86d2-e64eeb48b7c0 | Validated on PostgreSQL 14.4.0   |
+---------------+--------------------------------------+----------------------------------+
| mongoDB       | c842e867-bafd-4490-a0b1-a77311633456 | Validated on MongoDB 5.0.8       |
+---------------+--------------------------------------+----------------------------------+
| elasticsearch | 29c97315-8cc0-43aa-acec-12ff02998fa4 | Validated on Elasticsearch 8.2.3 |
+---------------+--------------------------------------+----------------------------------+
| exampleScript | e6e633f7-5ed3-4598-b773-e0d13631f5a6 |                                  |
+---------------+--------------------------------------+----------------------------------+
```

```text
$ actoolkit list scripts -s -f exampleScript
#####################
### exampleScript ###
#####################
#!/bin/bash
echo "this is just an example"
```

## Snapshots

`list snapshots` shows all app snapshots.  They can also be filtered by an app name.

Command usage:

```text
actoolkit list snapshots <optional-arguments>
```

Sample output:

```text
$ actoolkit list snapshots
+--------------------------------------+-------------------------------------+--------------------------------------+---------------+
| appID                                | snapshotName                        | snapshotID                           | snapshotState |
+======================================+=====================================+======================================+===============+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | wordpress-snapshot-20220520000039   | 8daeed16-f4d3-4d24-90f0-34748161ef05 | completed     |
+--------------------------------------+-------------------------------------+--------------------------------------+---------------+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | wordpress-snapshot-20220520010028   | b586d51a-28b3-4dd2-aecf-057191c9fc77 | completed     |
+--------------------------------------+-------------------------------------+--------------------------------------+---------------+
| a8dc676e-d182-4d7c-9113-43f5a2963b54 | wordpress-w-snapshot-20220519200036 | 12a2f61c-23b2-4c98-bc51-638c9ab9f9c1 | ready         |
+--------------------------------------+-------------------------------------+--------------------------------------+---------------+
```

```text
$ actoolkit list snapshots --app wordpress-east
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+
| appID                                | snapshotName                      | snapshotID                           | snapshotState |
+======================================+===================================+======================================+===============+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | wordpress-snapshot-20220520000039 | 8daeed16-f4d3-4d24-90f0-34748161ef05 | completed     |
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+
| 8f462cea-a166-438d-85b1-8aa5cfb0ad9f | wordpress-snapshot-20220520010028 | b586d51a-28b3-4dd2-aecf-057191c9fc77 | completed     |
+--------------------------------------+-----------------------------------+--------------------------------------+---------------+
```

## Storagebackends

`list storagebackends` lists the storage backends of the Astra Control environment.

```text
actoolkit list storagebackends
```

Sample output:

```text
$ actoolkit list storagebackends
+---------------+--------------------------------------+---------------+---------------+----------------+
| backendName   | backendID                            | backendType   | healthState   | managedState   |
+===============+======================================+===============+===============+================+
| astra-ots-02  | 234b7b22-53e4-4ead-a683-cfd7b4b07b1c | ontap         | normal        | managed        |
+---------------+--------------------------------------+---------------+---------------+----------------+
```

## Storageclasses

`list storageclasses` lists the storageclasses of *all* clusters, whether managed or unmanaged.  This command is particularly relevent when [managing a cluster](../manage/README.md#cluster) as the default storageclassID is a required argument.

Command usage:

```text
actoolkit list storageclasses <--cloudType optionalCloudTypeArg> \
    <--cluster optionalClusterIDorNameArg>
```

Sample output:

```text
$ actoolkit list storageclasses
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| storageclassName         | storageclassID                       | isDefault   | clusterName        | clusterID                            | cloudType   |
+==========================+======================================+=============+====================+======================================+=============+
| premium-rwo              | 942221a0-92d8-45e9-820f-9ca0a41833a8 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| standard-rwo             | 670e2154-2fa4-48fb-95c8-0d8eabd3f5dc |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-standard | 81a9302a-d4dd-473c-b386-93c67508c823 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-premium  | f6322d5c-755d-42ad-96f0-552a20610741 | true        | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-extreme  | a908dda1-89ba-4122-9830-6637ab3cbf78 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-anf-perf-standard | ba6d5a64-a321-4fd7-9842-9adce829229a |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| default                  | 61ccd37a-d407-4252-9a42-82aced92b1f2 |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| managed                  | 4a373518-acab-4d45-b6f5-d3fd5777069d |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| managed-csi              | 9e50815c-c433-448b-9aba-d03fa2f5ec2b |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| managed-csi-premium      | f868b07a-6a33-4a85-8e88-eafffbd4bfdf |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| managed-premium          | 83740760-6d53-46e1-b44f-1cba6cdf4a0a |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| azurefile                | d36dad41-9457-4ee5-bfde-cf8d51d54569 |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| azurefile-csi            | b9adf548-97cf-4ac9-b9be-5b06f0a23451 |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| azurefile-csi-premium    | a5cf174c-0f48-48f7-8ec7-11aeb831b888 |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| azurefile-premium        | e1b9b067-20c5-4b4a-8023-8a873d4b25fc |             | aks-eastus-cluster | 27eda8fc-d093-482f-b361-e631c85a00cc | Azure       |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
```

```text
$ actoolkit list storageclasses --cloudType GCP
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| storageclassName         | storageclassID                       | isDefault   | clusterName        | clusterID                            | cloudType   |
+==========================+======================================+=============+====================+======================================+=============+
| premium-rwo              | 942221a0-92d8-45e9-820f-9ca0a41833a8 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| standard-rwo             | 670e2154-2fa4-48fb-95c8-0d8eabd3f5dc |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-standard | 81a9302a-d4dd-473c-b386-93c67508c823 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-premium  | f6322d5c-755d-42ad-96f0-552a20610741 | true        | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-extreme  | a908dda1-89ba-4122-9830-6637ab3cbf78 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
```

```text
$ actoolkit list storageclasses --cluster useast1-cluster
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| storageclassName         | storageclassID                       | isDefault   | clusterName        | clusterID                            | cloudType   |
+==========================+======================================+=============+====================+======================================+=============+
| premium-rwo              | 942221a0-92d8-45e9-820f-9ca0a41833a8 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| standard-rwo             | 670e2154-2fa4-48fb-95c8-0d8eabd3f5dc |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-standard | 81a9302a-d4dd-473c-b386-93c67508c823 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-premium  | f6322d5c-755d-42ad-96f0-552a20610741 | true        | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-extreme  | a908dda1-89ba-4122-9830-6637ab3cbf78 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
```

```text
$ actoolkit list storageclasses --cluster e8091962-232b-4f13-acfe-802b83f04974
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| storageclassName         | storageclassID                       | isDefault   | clusterName        | clusterID                            | cloudType   |
+==========================+======================================+=============+====================+======================================+=============+
| premium-rwo              | 942221a0-92d8-45e9-820f-9ca0a41833a8 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| standard-rwo             | 670e2154-2fa4-48fb-95c8-0d8eabd3f5dc |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-standard | 81a9302a-d4dd-473c-b386-93c67508c823 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-premium  | f6322d5c-755d-42ad-96f0-552a20610741 | true        | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
| netapp-cvs-perf-extreme  | a908dda1-89ba-4122-9830-6637ab3cbf78 |             | useast1-cluster    | e8091962-232b-4f13-acfe-802b83f04974 | GCP         |
+--------------------------+--------------------------------------+-------------+--------------------+--------------------------------------+-------------+
```

## Users

The `list users` command lists all of the users within the Astra Control account.  There's also an optional partial match `nameFilter` argument to minimize output.

Command usage:

```text
actoolkit list users -f <optionalNameFilter>
```

Sample output:

```text
actoolkit list users
+--------------------------------------+-------------+---------------------+----------------+---------+
| userID                               | name        | email               | authProvider   | state   |
+======================================+=============+=====================+================+=========+
| 8146d293-d897-4e16-ab10-8dca934637ab | John Doe    | jdoe@example.com    | cloud-central  | active  |
+--------------------------------------+-------------+---------------------+----------------+---------+
| f0d5e243-5bfe-4aa5-9c98-f1d3da83110d | Jane Smith  | jsmith@example.com  | cloud-central  | active  |
+--------------------------------------+-------------+---------------------+----------------+---------+
```

```text
actoolkit list users -f smith
+--------------------------------------+-------------+---------------------+----------------+---------+
| userID                               | name        | email               | authProvider   | state   |
+======================================+=============+=====================+================+=========+
| f0d5e243-5bfe-4aa5-9c98-f1d3da83110d | Jane Smith  | jsmith@example.com  | cloud-central  | active  |
+--------------------------------------+-------------+---------------------+----------------+---------+
```
