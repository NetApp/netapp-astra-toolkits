# Optional Global Arguments

There are currently 4 global arguments that modify command output.  Most of these arguments (all but `--help`) should be placed immediately after `./toolkit.py` invocation, and before positional verbs (like deploy or clone):

* [Help](#help)
* [Verbose](#verbose)
* [Output](#output)
  * [Table](#table)
  * [Json](#json)
  * [Yaml](#yaml)
* [Quiet](#quiet)

## Help

The `--help` / `-h` argument can be utilized at any location within `./toolkit.py`.  If it's used immediately after `./toolkit.py`, then positional level arguments are shown.

```text
$ ./toolkit.py --help
usage: toolkit.py [-h] [-v] [-o {json,yaml,table}] [-q] {deploy,clone,restore,list,get,create,manage,define,destroy,unmanage} ...

positional arguments:
  {deploy,clone,restore,list,get,create,manage,define,destroy,unmanage}
                        subcommand help
    deploy              Deploy a helm chart
    clone               Clone an app
    restore             Restore an app from a backup or snapshot
    list (get)          List all items in a class
    create              Create an object
    manage (define)     Manage an object
    destroy             Destroy an object
    unmanage            Unmanage an object

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         print verbose/verbose output
  -o {json,yaml,table}, --output {json,yaml,table}
                        command output format
  -q, --quiet           supress output
```

If utilized after positional arguments, then information about that specific command is shown.

```text
$ ./toolkit.py list --help
usage: toolkit.py list [-h] {apps,backups,clouds,clusters,namespaces,snapshots,storageclasses} ...

optional arguments:
  -h, --help            show this help message and exit

objectType:
  {apps,backups,clouds,clusters,namespaces,snapshots,storageclasses}
    apps                list apps
    backups             list backups
    clouds              list clouds
    clusters            list clusters
    namespaces          list namespaces
    snapshots           list snapshots
    storageclasses      list storageclasses
```

Additionally, if the positional arguments require sub-arguments, the `--help` displays further information.

```text
usage: toolkit.py list apps [-h] [-n NAMESPACE] [-c CLUSTER]

optional arguments:
  -h, --help            show this help message and exit
  -n NAMESPACE, --namespace NAMESPACE
                        Only show apps from this namespace
  -c CLUSTER, --cluster CLUSTER
                        Only show apps from this cluster
```

## Verbose

The `--verbose` global argument prints additional output, such API call information (which is useful when modifying the `toolkit.py` or `astraSDK.py` files.  It **must** be placed immediately after the `./toolkit.py` invocation.

**Caution**: be mindful of running this command in front of others, as API credential information is displayed.

```text
$ ./toolkit.py --verbose list apps
API URL: https://hidden.astra.netapp.io/accounts/737c6a6e-930f-48ce-82ba-afcafc0633dd/k8s/v2/apps
API Method: GET
API Headers: {'Authorization': 'Bearer KroeirTcUoMs6baBcUhXcAGK0-4tbm_ol1hJC2OtaDg='}
API data: {}
API params: {}
API HTTP Status Code: 200

+------------------------------+--------------------------------------+--------------------+-------------+--------------+
| appName                      | appID                                | clusterName        | namespace   | state        |
+==============================+======================================+====================+=============+==============+
| wordpress                    | 79c608be-828d-4b3b-92d4-5589c0a4e515 | uscentral1-cluster | wordpress   | ready        |
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
| cassandra                    | 79871ad1-2f69-4532-806a-42ba11cc45ac | uscentral1-cluster | cassandra   | ready        |
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
| wordpress-clone-202207271713 | 7c212175-9cbd-4bb9-96a4-3a61a8ea0fda | useast4-cluster    |             | provisioning |
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
```

## Output

The `--output {json,yaml,table`} argument modifies the output method of `list` commands.  The default option is `table`, which is most useful for manual `toolkit` operation.  The `json` and `yaml` are useful to gather more information about the various objects, and/or further automated processing.

### Table

The `table` output is the default option, so it's not necessary to explicitly use.

```text
$ ./toolkit.py -o table list apps
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
| appName                      | appID                                | clusterName        | namespace   | state        |
+==============================+======================================+====================+=============+==============+
| wordpress                    | 79c608be-828d-4b3b-92d4-5589c0a4e515 | uscentral1-cluster | wordpress   | ready        |
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
| cassandra                    | 79871ad1-2f69-4532-806a-42ba11cc45ac | uscentral1-cluster | cassandra   | ready        |
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
| wordpress-clone-202207271713 | 7c212175-9cbd-4bb9-96a4-3a61a8ea0fda | useast4-cluster    |             | provisioning |
+------------------------------+--------------------------------------+--------------------+-------------+--------------+
```

### Json

The `json` output prints the full API object in json format.

```text
$ ./toolkit.py -o json list apps
{"items": [{"type": "application/astra-app", "version": "2.0", "id": "79c608be-828d-4b3b-92d4-5589c0a4e515", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress"}], "state": "ready", "lastResourceCollectionTimestamp": "2022-07-27T21:09:26Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "partial", "protectionStateDetails": [], "namespaces": ["wordpress"], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T21:07:28Z", "modificationTimestamp": "2022-07-27T21:09:54Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}, {"type": "application/astra-app", "version": "2.0", "id": "79871ad1-2f69-4532-806a-42ba11cc45ac", "name": "cassandra", "namespaceScopedResources": [{"namespace": "cassandra", "labelSelectors": ["app.kubernetes.io/instance=cassandra"]}], "state": "ready", "lastResourceCollectionTimestamp": "2022-07-27T21:09:31Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "partial", "protectionStateDetails": [], "namespaces": ["cassandra"], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T21:07:33Z", "modificationTimestamp": "2022-07-27T21:09:54Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}], "metadata": {}}
```

This is useful in conjunction with the [jq](https://stedolan.github.io/jq/) utility, first for pretty-printing the output:

```text
$ ./toolkit.py -o json list apps | jq
{
  "items": [
    {
      "type": "application/astra-app",
      "version": "2.0",
      "id": "79c608be-828d-4b3b-92d4-5589c0a4e515",
      "name": "wordpress",
      "namespaceScopedResources": [
        {
          "namespace": "wordpress"
        }
      ],
      "state": "ready",
      "lastResourceCollectionTimestamp": "2022-07-27T21:09:26Z",
      "stateTransitions": [
        {
          "to": [
            "pending"
          ]
        },
        {
          "to": [
            "provisioning"
          ]
        },
        {
          "from": "pending",
          "to": [
            "discovering",
            "failed"
          ]
        },
        {
          "from": "discovering",
          "to": [
            "ready",
            "failed"
          ]
        },
        {
          "from": "ready",
          "to": [
            "discovering",
            "restoring",
            "unavailable",
            "failed"
          ]
        },
        {
          "from": "unavailable",
          "to": [
            "ready",
            "restoring"
          ]
        },
        {
          "from": "provisioning",
          "to": [
            "discovering",
            "failed"
          ]
        },
        {
          "from": "restoring",
          "to": [
            "discovering",
            "failed"
          ]
        }
      ],
      "stateDetails": [],
      "protectionState": "protected",
      "protectionStateDetails": [],
      "namespaces": [
        "wordpress"
      ],
      "clusterName": "uscentral1-cluster",
      "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d",
      "clusterType": "gke",
      "metadata": {
        "labels": [],
        "creationTimestamp": "2022-07-27T21:07:28Z",
        "modificationTimestamp": "2022-07-27T21:20:03Z",
        "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"
      }
    },
    {
      "type": "application/astra-app",
      "version": "2.0",
      "id": "79871ad1-2f69-4532-806a-42ba11cc45ac",
      "name": "cassandra",
      "namespaceScopedResources": [
        {
          "namespace": "cassandra",
          "labelSelectors": [
            "app.kubernetes.io/instance=cassandra"
          ]
        }
      ],
      "state": "ready",
      "lastResourceCollectionTimestamp": "2022-07-27T21:16:27Z",
      "stateTransitions": [
        {
          "to": [
            "pending"
          ]
        },
        {
          "to": [
            "provisioning"
          ]
        },
        {
          "from": "pending",
          "to": [
            "discovering",
            "failed"
          ]
        },
        {
          "from": "discovering",
          "to": [
            "ready",
            "failed"
          ]
        },
        {
          "from": "ready",
          "to": [
            "discovering",
            "restoring",
            "unavailable",
            "failed"
          ]
        },
        {
          "from": "unavailable",
          "to": [
            "ready",
            "restoring"
          ]
        },
        {
          "from": "provisioning",
          "to": [
            "discovering",
            "failed"
          ]
        },
        {
          "from": "restoring",
          "to": [
            "discovering",
            "failed"
          ]
        }
      ],
      "stateDetails": [],
      "protectionState": "partial",
      "protectionStateDetails": [],
      "namespaces": [
        "cassandra"
      ],
      "clusterName": "uscentral1-cluster",
      "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d",
      "clusterType": "gke",
      "metadata": {
        "labels": [],
        "creationTimestamp": "2022-07-27T21:07:33Z",
        "modificationTimestamp": "2022-07-27T21:20:03Z",
        "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"
      }
    },
    {
      "type": "application/astra-app",
      "version": "2.0",
      "id": "7c212175-9cbd-4bb9-96a4-3a61a8ea0fda",
      "name": "wordpress-clone-202207271713",
      "namespaceScopedResources": [
        {
          "namespace": "wordpress-clonens-202207271713",
          "labelSelectors": []
        }
      ],
      "state": "provisioning",
      "lastResourceCollectionTimestamp": "2022-07-27T21:13:22Z",
      "stateTransitions": [
        {
          "to": [
            "pending"
          ]
        },
        {
          "to": [
            "provisioning"
          ]
        },
        {
          "from": "pending",
          "to": [
            "discovering",
            "failed"
          ]
        },
        {
          "from": "discovering",
          "to": [
            "ready",
            "failed"
          ]
        },
        {
          "from": "ready",
          "to": [
            "discovering",
            "restoring",
            "unavailable",
            "failed"
          ]
        },
        {
          "from": "unavailable",
          "to": [
            "ready",
            "restoring"
          ]
        },
        {
          "from": "provisioning",
          "to": [
            "discovering",
            "failed"
          ]
        },
        {
          "from": "restoring",
          "to": [
            "discovering",
            "failed"
          ]
        }
      ],
      "stateDetails": [],
      "protectionState": "none",
      "protectionStateDetails": [],
      "namespaces": [],
      "clusterName": "useast4-cluster",
      "clusterID": "9857d628-dc4b-4227-8470-7b7dd4ed84e9",
      "clusterType": "gke",
      "sourceClusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d",
      "backupID": "22b699cf-5a0f-4598-9840-1be055dd672b",
      "metadata": {
        "labels": [
          {
            "name": "astra.netapp.io/labels/read-only/appType",
            "value": "clone"
          }
        ],
        "creationTimestamp": "2022-07-27T21:13:21Z",
        "modificationTimestamp": "2022-07-27T21:20:03Z",
        "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"
      }
    }
  ],
  "metadata": {}
}
```

Second, it can be used to extract certain information, for instance if you wanted to determine the `protectionState` of your managed applications:

```text
$ ./toolkit.py -o json list apps | jq '.items[] | {id, name, protectionState}'
{
  "id": "79c608be-828d-4b3b-92d4-5589c0a4e515",
  "name": "wordpress",
  "protectionState": "protected"
}
{
  "id": "79871ad1-2f69-4532-806a-42ba11cc45ac",
  "name": "cassandra",
  "protectionState": "partial"
}
{
  "id": "7c212175-9cbd-4bb9-96a4-3a61a8ea0fda",
  "name": "wordpress-clone-202207271713",
  "protectionState": "none"
}
```

Lastly, it's useful for short shell scripts which require multiple object IDs.  For instance, say you wanted to [destroy](../destroy/README.md) all [snapshots](../destroy/README.md#snapshot) for a particular application.

You can first just gather the snapshot IDs:

```text
$ ./toolkit.py -o json list snapshots --app cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0 \
    | jq -r '.items[].id'
4e0c53cc-820b-4935-a65a-c89f665e7fbd
5700cc40-f446-46a1-ab36-bc053616d84e
```

You can then enclose that command in a simple for loop:

```text
$ for i in `./toolkit.py -o json list snapshots --app cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0 \
    | jq -r '.items[].id'`; do echo "=== destroying snapshot $i ==="; ./toolkit.py destroy \
    snapshot cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0 $i; done
=== destroying snapshot 4e0c53cc-820b-4935-a65a-c89f665e7fbd ===
Snapshot 4e0c53cc-820b-4935-a65a-c89f665e7fbd destroyed
=== destroying snapshot 5700cc40-f446-46a1-ab36-bc053616d84e ===
Snapshot 5700cc40-f446-46a1-ab36-bc053616d84e destroyed
```

Or, say you wanted to [protect](../create/README.md#protectionpolicy) all of your apps that are currently unprotected:

```text
$ for i in `./toolkit.py -o json list apps \
    | jq -r '.items[] | select(.protectionState == "none") | {id} | join(" ")'`; \
    do echo "=== protecting app $i ==="; \
    ./toolkit.py create protectionpolicy $i -g hourly -b 2 -s 3; done
=== protecting app a8dc676e-d182-4d7c-9113-43f5a2963b54 ===
{"type": "application/astra-schedule", "version": "1.1", "id": "a8dc676e-d182-4d7c-9113-43f5a2963b54", "name": "hourly-trpvk", "enabled": "true", "granularity": "hourly", "minute": "0", "snapshotRetention": "3", "backupRetention": "2", "metadata": {"labels": [], "creationTimestamp": "2022-05-24T20:24:14Z", "modificationTimestamp": "2022-05-24T20:24:14Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
=== protecting app ad125374-e090-425b-a048-d719b93b0feb ===
{"type": "application/astra-schedule", "version": "1.1", "id": "ad125374-e090-425b-a048-d719b93b0feb", "name": "hourly-d4bcx", "enabled": "true", "granularity": "hourly", "minute": "0", "snapshotRetention": "3", "backupRetention": "2", "metadata": {"labels": [], "creationTimestamp": "2022-05-24T20:24:15Z", "modificationTimestamp": "2022-05-24T20:24:15Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
=== protecting app cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0 ===
{"type": "application/astra-schedule", "version": "1.1", "id": "cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0", "name": "hourly-r8pr3", "enabled": "true", "granularity": "hourly", "minute": "0", "snapshotRetention": "3", "backupRetention": "2", "metadata": {"labels": [], "creationTimestamp": "2022-05-24T20:24:17Z", "modificationTimestamp": "2022-05-24T20:24:17Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

### Yaml

If you prefer `yaml` over json, the `--output yaml` argument can be utilized.  It can also be used in conjunction with [yq](https://github.com/mikefarah/yq) in similar fashion as jq.

```text
$ ./toolkit.py -o yaml list clusters
items:
- cloudID: e7a0bf84-0256-4ab6-a4ec-4aa5a4e49705
  clusterCreationTimestamp: '2022-07-26T20:33:55Z'
  clusterType: gke
  clusterVersion: '1.21'
  clusterVersionString: v1.21.11-gke.1100
  defaultStorageClass: 81a9302a-d4dd-473c-b386-93c67508c823
  id: b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
  inUse: 'true'
  isMultizonal: 'true'
  location: us-central1-b
  managedState: managed
  managedStateUnready: []
  managedTimestamp: '2022-07-27T21:06:27Z'
  metadata:
    createdBy: 12a5d9dd-851e-4235-af27-86c0b63bf3a9
    creationTimestamp: '2022-07-20T17:40:45Z'
    labels:
    - name: astra.netapp.io/labels/read-only/gcp/HostVpcProjectID
      value: xxxxxxx01169
    - name: astra.netapp.io/labels/read-only/gcp/projectNumber
      value: '239048101169'
    - name: astra.netapp.io/labels/read-only/hasNonTridentCSIDriverSupport
      value: 'true'
    - name: astra.netapp.io/labels/read-only/hasTridentDriverSupport
      value: 'true'
    - name: astra.netapp.io/labels/read-only/cloudName
      value: GCP
    modificationTimestamp: '2022-07-27T21:13:28Z'
  name: uscentral1-cluster
  namespaces:
  - cassandra
  - default
  - kube-node-lease
  - kube-public
  - kube-system
  - trident
  - wordpress
  restoreTargetSupported: 'true'
  snapshotSupported: 'true'
  state: running
  stateUnready: []
  type: application/astra-cluster
  version: '1.1'
- cloudID: e7a0bf84-0256-4ab6-a4ec-4aa5a4e49705
  clusterCreationTimestamp: '2022-07-27T20:37:06Z'
  clusterType: gke
  clusterVersion: '1.21'
  clusterVersionString: v1.21.11-gke.1100
  defaultStorageClass: 81a9302a-d4dd-473c-b386-93c67508c823
  id: 9857d628-dc4b-4227-8470-7b7dd4ed84e9
  inUse: 'true'
  isMultizonal: 'true'
  location: us-east4-b
  managedState: managed
  managedStateUnready: []
  managedTimestamp: '2022-07-27T21:06:21Z'
  metadata:
    createdBy: 12a5d9dd-851e-4235-af27-86c0b63bf3a9
    creationTimestamp: '2022-07-27T20:38:58Z'
    labels:
    - name: astra.netapp.io/labels/read-only/gcp/projectNumber
      value: '239048101169'
    - name: astra.netapp.io/labels/read-only/gcp/HostVpcProjectID
      value: xxxxxxx01169
    - name: astra.netapp.io/labels/read-only/hasNonTridentCSIDriverSupport
      value: 'true'
    - name: astra.netapp.io/labels/read-only/hasTridentDriverSupport
      value: 'true'
    - name: astra.netapp.io/labels/read-only/cloudName
      value: GCP
    modificationTimestamp: '2022-07-27T21:13:28Z'
  name: useast4-cluster
  namespaces: []
  restoreTargetSupported: 'true'
  snapshotSupported: 'true'
  state: pending
  stateUnready: []
  type: application/astra-cluster
  version: '1.1'
```

## Quiet

The `--quiet` argument suppresses output, while still utilizing proper exit codes, and throwing error messages for incorrect commands.  Consider this command (without the `--quiet` argument):

```text
$ ./toolkit.py manage app cassandra default -l name=cassandra b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{'clusterID': 'b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d', 'name': 'cassandra', 'namespaceScopedResources': [{'namespace': 'default', 'labelSelectors': ['name=cassandra']}], 'type': 'application/astra-app', 'version': '2.0'}
{"type": "application/astra-app", "version": "2.0", "id": "9dc08664-3d5d-4f7d-b2fd-266d12114f3b", "name": "cassandra", "namespaceScopedResources": [{"namespace": "default", "labelSelectors": ["name=cassandra"]}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-27T17:38:05Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T17:38:05Z", "modificationTimestamp": "2022-07-27T17:38:05Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

With the `--quiet` argument instead:

```text
$ ./toolkit.py manage app cassandra default -l name=cassandra b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
$ echo $?
0
```

While incorrect commands still display output even with the `--quiet` argument:

```text
$ ./toolkit.py --quiet manage app cassandra default -l name=cassandra 11111111-1111-1111-1111-111111111111
usage: toolkit.py manage app [-h] [-l LABELSELECTORS] appName {cassandra,default,wordpress} {b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d}
toolkit.py manage app: error: argument clusterID: invalid choice: '11111111-1111-1111-1111-111111111111' (choose from 'b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d')
$ echo $?
2
```
