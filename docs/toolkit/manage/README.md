# Manage (aka Define)

The `manage` argument allows you to manage resources that live outside of Astra Control:

* [App](#app)
* [Bucket](#bucket)
* [Cloud](#cloud)
* [Cluster](#cluster)

It's opposite command is [unmanage](../unmanage/README.md).  **Manage** and **unmanage** are similar to [create](../create/README.md) and [destroy](../destroy/README.md), however create/destroy objects live entirely within Astra Control, while manage/unmanage objects do not.  If you create and then destroy a [snapshot](../create/README.md#snapshot), it is gone forever.  However if you manage and then unmanage a cluster, the cluster still exists to re-manage again.

```text
$ actoolkit manage -h
usage: actoolkit manage [-h] {app,bucket,cloud,cluster} ...

options:
  -h, --help            show this help message and exit

objectType:
  {app,bucket,cloud,cluster}
    app                 manage app
    bucket              manage bucket
    cloud               manage cloud
    cluster             manage cluster
```

## App

To define (or manage) an app, you must first gather the [namespace name](../list/README.md#namespaces) and [cluster ID](../list/README.md#clusters).  After an application is managed, it is recommended to [create a protectionpolicy](../create/README.md#protectionpolicy) for the app.

[Label selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) are optional strings to filter resources within a namespace to be included in or excluded from the application definition.  For instance, if you have multiple apps within the `default` namespace, label selectors allow you to define these applications separately within Astra Control.

Command usage:

```text
actoolkit manage app <appLogicalName> <namespaceName> <clusterID> \
    <--labelSelectors optionalLabelSelectors> \
    <--additionalNamespace optionalAdditionalNamespace optionalLabelSelectors> \
    <--clusterScopedResource optionalClusterScoped Resource optionalLabelSelectors>
```

Sample output:

```text
$ actoolkit manage app wordpress wordpress b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{"type": "application/astra-app", "version": "2.0", "id": "40f27720-5e6d-4ab7-8647-cc05f2019319", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress"}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-25T14:21:48Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-25T14:21:48Z", "modificationTimestamp": "2022-07-25T14:21:48Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

To use a single label, specify the `-l`/`--labelSelectors` argument and the [label selector](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) of your choice, *without spaces*:

```text
$ actoolkit manage app wordpress default -l app.kubernetes.io/instance=wordpress \
    b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{"type": "application/astra-app", "version": "2.0", "id": "07c67881-ae5b-4091-a881-23be39ae72ae", "name": "wordpress", "namespaceScopedResources": [{"namespace": "default", "labelSelectors": ["app.kubernetes.io/instance=wordpress"]}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-27T17:10:50Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T17:10:50Z", "modificationTimestamp": "2022-07-27T17:10:50Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

Multiple labels utilize comma separation:

```text
$ actoolkit manage app wordpress default \
    -l app.kubernetes.io/name=wordpress,app.kubernetes.io/managed-by=Helm \
    b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{'clusterID': 'b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d', 'name': 'wordpress', 'namespaceScopedResources': [{'namespace': 'default', 'labelSelectors': ['app.kubernetes.io/name=wordpress,app.kubernetes.io/managed-by=Helm']}], 'type': 'application/astra-app', 'version': '2.0'}
{"type": "application/astra-app", "version": "2.0", "id": "0d2fa973-4c9f-4e7b-9de3-2ac74c204a5c", "name": "wordpress", "namespaceScopedResources": [{"namespace": "default", "labelSelectors": ["app.kubernetes.io/name=wordpress,app.kubernetes.io/managed-by=Helm"]}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-27T17:33:02Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T17:33:02Z", "modificationTimestamp": "2022-07-27T17:33:02Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

Any label selectors which require spaces or characters that interfere with bash/zsh (for instance `!`) should be encased in quotes:

```text
$ actoolkit manage app cassandra default -l 'tier notin (frontend)' \
    b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{"type": "application/astra-app", "version": "2.0", "id": "736d1231-807b-4ee2-ba51-e8a35a2829d3", "name": "cassandra", "namespaceScopedResources": [{"namespace": "default", "labelSelectors": ["tier notin (frontend)"]}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-27T17:48:47Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T17:48:47Z", "modificationTimestamp": "2022-07-27T17:48:47Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

```text
$ actoolkit manage app cassandra default -l '!app' \
    b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d
{"type": "application/astra-app", "version": "2.0", "id": "8484c2b6-8496-41fb-b2d1-8bbb549609de", "name": "cassandra", "namespaceScopedResources": [{"namespace": "default", "labelSelectors": ["!app"]}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-07-27T17:58:25Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaces": [], "clusterName": "uscentral1-cluster", "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-07-27T17:58:25Z", "modificationTimestamp": "2022-07-27T17:58:25Z", "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"}}
```

Additional namespaces (and their optional labels) can be provided by any number of the `--additionalNamespace`/`-a` argument:

```text
$ actoolkit manage app wordpress wordpress \
    690deba1-bc57-4771-ab72-88758cab2afd -a default
{"type": "application/astra-app", "version": "2.1", "id": "863bd74f-030c-4d51-a56f-3d69a02c58cf", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress"}, {"namespace": "default"}], "clusterScopedResources": [], "state": "discovering", "lastResourceCollectionTimestamp": "2022-10-19T17:34:22Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaceMapping": [], "clusterName": "prod-cluster", "clusterID": "690deba1-bc57-4771-ab72-88758cab2afd", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-10-19T17:34:22Z", "modificationTimestamp": "2022-10-19T17:34:22Z", "createdBy": "022c5578-44b6-4f2a-8f25-862c7352205a"}}
```

```text
$ actoolkit manage app wordpress wordpress -l app.kubernetes.io/managed-by=Helm \
    690deba1-bc57-4771-ab72-88758cab2afd \
    -a default app.kubernetes.io/instance=wordpress
{"type": "application/astra-app", "version": "2.1", "id": "60ebee33-fea3-4664-80d7-df492dca62ee", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress", "labelSelectors": ["app.kubernetes.io/managed-by=Helm"]}, {"namespace": "default", "labelSelectors": ["app.kubernetes.io/instance=wordpress"]}], "clusterScopedResources": [], "state": "discovering", "lastResourceCollectionTimestamp": "2022-10-19T17:36:11Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaceMapping": [], "clusterName": "prod-cluster", "clusterID": "690deba1-bc57-4771-ab72-88758cab2afd", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-10-19T17:36:11Z", "modificationTimestamp": "2022-10-19T17:36:11Z", "createdBy": "022c5578-44b6-4f2a-8f25-862c7352205a"}}
```

```text
$ actoolkit manage app wordpress wordpress \
    690deba1-bc57-4771-ab72-88758cab2afd \
    -a default app.kubernetes.io/instance=wordpress,app.kubernetes.io/managed-by=Helm
{"type": "application/astra-app", "version": "2.1", "id": "84b18a22-c2fa-49d4-a6b7-82b687112bf4", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress"}, {"namespace": "default", "labelSelectors": ["app.kubernetes.io/instance=wordpress,app.kubernetes.io/managed-by=Helm"]}], "clusterScopedResources": [], "state": "discovering", "lastResourceCollectionTimestamp": "2022-10-19T17:37:43Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaceMapping": [], "clusterName": "prod-cluster", "clusterID": "690deba1-bc57-4771-ab72-88758cab2afd", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-10-19T17:37:43Z", "modificationTimestamp": "2022-10-19T17:37:43Z", "createdBy": "022c5578-44b6-4f2a-8f25-862c7352205a"}}
```

```text
$ actoolkit manage app wordpress wordpress \
    690deba1-bc57-4771-ab72-88758cab2afd \
    -a default app.kubernetes.io/instance=wordpress,app.kubernetes.io/managed-by=Helm \
    -a wordpress-frontend
{"type": "application/astra-app", "version": "2.1", "id": "6a8f7c47-4caa-4ace-acce-eac1c4fdd23c", "name": "wordpress", "namespaceScopedResources": [{"namespace": "wordpress"}, {"namespace": "default", "labelSelectors": ["app.kubernetes.io/instance=wordpress,app.kubernetes.io/managed-by=Helm"]}, {"namespace": "kube-system"}], "clusterScopedResources": [], "state": "discovering", "lastResourceCollectionTimestamp": "2022-10-19T17:40:42Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaceMapping": [], "clusterName": "prod-cluster", "clusterID": "690deba1-bc57-4771-ab72-88758cab2afd", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-10-19T17:40:42Z", "modificationTimestamp": "2022-10-19T17:40:42Z", "createdBy": "022c5578-44b6-4f2a-8f25-862c7352205a"}}
```

Cluster scoped resources can be provided via the `--clusterScopedResource`/`-c` argument, which must match one of the available [API resource kinds](../list/README.md#apiresources) for the given cluster.  A single cluster scoped resource should be provided per `--clusterScopedResource`/`-c` flag, with an optional additional label selector.

```text
$ actoolkit manage app cloudbees-core cloudbees-core 690deba1-bc57-4771-ab72-88758cab2afd \
    -c ValidatingWebhookConfiguration \
    -c ClusterRole app.kubernetes.io/instance=cloudbees-core \
    -c ClusterRoleBinding app.kubernetes.io/instance=cloudbees-core
{"type": "application/astra-app", "version": "2.1", "id": "53575377-7086-4922-9fb9-790a09e31479", "name": "application-4903123e-3", "namespaceScopedResources": [{"namespace": "cloudbees-core"}], "clusterScopedResources": [{"GVK": {"group": "rbac.authorization.k8s.io", "kind": "ClusterRole", "version": "v1"}, "labelSelectors": ["app.kubernetes.io/instance=cloudbees-core"]}, {"GVK": {"group": "rbac.authorization.k8s.io", "kind": "ClusterRoleBinding", "version": "v1"}, "labelSelectors": ["app.kubernetes.io/instance=cloudbees-core"]}, {"GVK": {"group": "admissionregistration.k8s.io", "kind": "ValidatingWebhookConfiguration", "version": "v1"}}], "state": "discovering", "lastResourceCollectionTimestamp": "2022-10-20T14:51:13Z", "stateTransitions": [{"to": ["pending"]}, {"to": ["provisioning"]}, {"from": "pending", "to": ["discovering", "failed"]}, {"from": "discovering", "to": ["ready", "failed"]}, {"from": "ready", "to": ["discovering", "restoring", "unavailable", "failed"]}, {"from": "unavailable", "to": ["ready", "restoring"]}, {"from": "provisioning", "to": ["discovering", "failed"]}, {"from": "restoring", "to": ["discovering", "failed"]}], "stateDetails": [], "protectionState": "none", "protectionStateDetails": [], "namespaceMapping": [], "clusterName": "prod-cluster", "clusterID": "690deba1-bc57-4771-ab72-88758cab2afd", "clusterType": "gke", "metadata": {"labels": [], "creationTimestamp": "2022-10-20T14:51:13Z", "modificationTimestamp": "2022-10-20T14:51:13Z", "createdBy": "022c5578-44b6-4f2a-8f25-862c7352205a"}}
```

## Bucket

To manage a bucket, you can either reference an existing [credentialID](../list/README.md#credentials), or a credential will be automatically created for you when using the `--accessKey` and `--accessSecret` arguments.  Command usage:

```text
actoolkit manage bucket <provider> <bucketName> \
    <credentialGroupArgs> <optionalProviderDependentArgs>
```

The arguments have the following requirements:

* `provider`: one of `aws`, `azure`, `gcp`, `generic-s3`, `ontap-s3`, or `storagegrid-s3`
* `bucketName`: the name of the bucket (which must already exist)
* Credential group arguments:
  * `-c`/`--credentialID`: the existing [credentialID](../list/README.md#credentials) (if specified, the following two `access` arguments **must not** be specified)
  * `--accessKey`: the access key of the bucket (if specified, `credentialID` **must not** be specified, and `accessSecret` **must** be specified)
  * `--accessSecret`: the access secret of the bucket (if specified, `credentialID` **must not** be specified, and `accessKey` **must** be specified)
* Provider dependent arguments:
  * `-u`/`--serverURL`: The URL to the base path of the bucket (only needed for `aws`, `generic-s3`, `ontap-s3` and `storagegrid-s3` providers)
  * `-a`/`--storageAccount`: The Azure storage account name (only needed for `azure` provider)

To manage a bucket based on an existing credentialID:

```text
$ actoolkit manage bucket gcp astra-gcp-examplebucket -c 987ab72d-3e48-4b9f-879f-1d14059efa8e
{"type": "application/astra-bucket", "version": "1.1", "id": "ffa96e57-4fb5-46b9-9899-b1fc7e089cb4", "name": "astra-gcp-examplebucket", "state": "pending", "credentialID": "987ab72d-3e48-4b9f-879f-1d14059efa8e", "provider": "gcp", "bucketParameters": {"gcp": {"bucketName": "astra-gcp-examplebucket"}}, "metadata": {"creationTimestamp": "2022-09-13T21:17:59Z", "modificationTimestamp": "2022-09-13T21:17:59Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

To manage a bucket based on an access key and secret (take note of the duplicate json response, as the credential is first created, then the bucket is managed):

```text
$ actoolkit manage bucket generic-s3 astra-generic-examplebucket -u s3.astrademo.net \
    --accessKey accessKey1234567890 --accessSecret accessSecret1234567890
{"type": "application/astra-credential", "version": "1.1", "id": "bd89e7e7-41b1-4356-bf19-d708906fad59", "name": "astra-generic-examplebucket", "keyType": "s3", "metadata": {"creationTimestamp": "2022-09-13T21:25:43Z", "modificationTimestamp": "2022-09-13T21:25:43Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "s3"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "s3"}]}}
{"type": "application/astra-bucket", "version": "1.1", "id": "d6c59f83-fcb2-4475-87de-cd5dc7277ac6", "name": "astra-generic-examplebucket", "state": "pending", "credentialID": "bd89e7e7-41b1-4356-bf19-d708906fad59", "provider": "generic-s3", "bucketParameters": {"s3": {"serverURL": "s3.astrademo.net", "bucketName": "astra-generic-examplebucket"}}, "metadata": {"creationTimestamp": "2022-09-13T21:25:43Z", "modificationTimestamp": "2022-09-13T21:25:43Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```

## Cloud

Managing a public cloud allows Astra Control to automatically discover deployed managed Kubernetes clusters.  Alternatively, managing a private cloud is a pre-requisite for cluster kubeconfig ingest.  Command usage:

```text
actoolkit manage cloud <cloudType> <cloudName> <--credentialPath credentialPath> \
    <--defaultBucketID optionalDefaultBucketID>
```

The arguments have the following requirements:

* `cloudType`: must be one of `AWS`, `Azure`, `GCP`, or `private`
* `cloudName`: a friendly, descriptive name of the cloud
* `credentialPath`: the local filesystem path of the credential JSON (required for all non-`private` cloudTypes)
* `defaultBucketID`: an optional [bucketID](../list/README.md#buckets) for app backup storage

Sample output:

```text
$ actoolkit manage cloud Azure azure-tme -p ~/.azure/azure-sp-tme-demo2-astra.json \
    -b e626e015-bc0b-4cac-9ccf-c55ed5eeb18a
{"type": "application/astra-credential", "version": "1.1", "id": "09f8b4ca-975f-4084-b123-53423af6924b", "name": "astra-sa@azure-tme", "keyType": "generic", "valid": "true", "metadata": {"creationTimestamp": "2022-11-11T14:17:38Z", "modificationTimestamp": "2022-11-11T14:17:38Z", "createdBy": "23ecfb3a-c581-473b-9f44-9495c280fb8b", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "service-account"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "Azure"}]}}
{"type": "application/astra-cloud", "version": "1.0", "id": "f7d8204a-1ff8-4ae7-983f-2c4352b01dc8", "name": "azure-tme", "state": "pending", "stateUnready": [], "cloudType": "Azure", "credentialID": "09f8b4ca-975f-4084-b123-53423af6924b", "defaultBucketID": "e626e015-bc0b-4cac-9ccf-c55ed5eeb18a", "metadata": {"labels": [], "creationTimestamp": "2022-11-11T14:17:40Z", "modificationTimestamp": "2022-11-11T14:17:40Z", "createdBy": "23ecfb3a-c581-473b-9f44-9495c280fb8b"}}
```

```text
$ actoolkit manage cloud AWS aws-tme-demo -p ~/.aws/aws-astra-control.json
{"type": "application/astra-credential", "version": "1.1", "id": "8bc83523-8406-4d21-ae03-3b931ad79a67", "name": "astra-sa@aws-tme-demo", "keyType": "generic", "valid": "true", "metadata": {"creationTimestamp": "2022-11-11T14:44:23Z", "modificationTimestamp": "2022-11-11T14:44:23Z", "createdBy": "23ecfb3a-c581-473b-9f44-9495c280fb8b", "labels": [{"name": "astra.netapp.io/labels/read-only/credType", "value": "service-account"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "AWS"}]}}
{"type": "application/astra-cloud", "version": "1.0", "id": "bd63bd2e-c6d5-4435-a5b2-71163d5c5dc1", "name": "aws-tme-demo", "state": "pending", "stateUnready": [], "cloudType": "AWS", "credentialID": "8bc83523-8406-4d21-ae03-3b931ad79a67", "metadata": {"labels": [], "creationTimestamp": "2022-11-11T14:44:23Z", "modificationTimestamp": "2022-11-11T14:44:23Z", "createdBy": "23ecfb3a-c581-473b-9f44-9495c280fb8b"}}
```

For `private` clouds, the `credentialPath` field is not necessary:

```text
$ actoolkit manage cloud private private
{"type": "application/astra-cloud", "version": "1.0", "id": "7c760fec-47dc-4a2b-a625-de5abab6487e", "name": "private", "state": "running", "stateUnready": [], "cloudType": "private", "metadata": {"labels": [], "creationTimestamp": "2022-11-11T14:43:22Z", "modificationTimestamp": "2022-11-11T14:43:22Z", "createdBy": "23ecfb3a-c581-473b-9f44-9495c280fb8b"}}
```

## Cluster

To manage a cluster, you must gather the [cluster ID](../list/README.md#clusters), and if changing the default storage class, the corresponding [storageclass ID](../list/README.md#storageclasses).  Command usage:

```text
actoolkit manage cluster <clusterID> <--defaultStorageClassID optionalDefaultStorageClassID>
```

Sample output:

```text
$ actoolkit manage cluster 062728da-ef0c-4dc2-83f9-bedb07c30511
{"type": "application/astra-managedCluster", "version": "1.1", "id": "062728da-ef0c-4dc2-83f9-bedb07c30511", "name": "prod-cluster", "state": "pending", "stateUnready": [], "managedState": "managed", "protectionState": "full", "restoreTargetSupported": "true", "snapshotSupported": "true", "managedStateUnready": [], "managedTimestamp": "2022-11-02T14:41:14Z", "inUse": "false", "clusterType": "gke", "clusterVersion": "1.22", "clusterVersionString": "v1.22.12-gke.2300", "clusterCreationTimestamp": "2022-11-01T14:08:28Z", "namespaces": [], "cloudID": "ec0c2760-5bd7-45a6-9c15-44287299cd7a", "credentialID": "073c587a-55a4-418a-9c4f-f9aef1d56a2f", "location": "us-east4-a", "isMultizonal": "true", "tridentManagedStateAllowed": ["unmanaged"], "tridentVersion": "22.7.0", "apiServiceID": "20e7a050-ef7d-428c-af47-16207ea7b2f3", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/gcp/HostVpcProjectID", "value": "xxxxxxx01169"}, {"name": "astra.netapp.io/labels/read-only/gcp/projectNumber", "value": "239048101169"}, {"name": "astra.netapp.io/labels/read-only/hasNonTridentCSIDriverSupport", "value": "true"}, {"name": "astra.netapp.io/labels/read-only/hasTridentDriverSupport", "value": "true"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "GCP"}], "creationTimestamp": "2022-11-02T14:41:14Z", "modificationTimestamp": "2022-11-02T14:41:15Z", "createdBy": "0fa0c5e9-5a2a-48e2-adb5-d0f12bd14115"}}
```

```text
$ actoolkit manage cluster 80d6bef8-300c-44bd-9e36-04ef874bdc29 \
    -s ba6d5a64-a321-4fd7-9842-9adce829229a
{"type": "application/astra-managedCluster", "version": "1.1", "id": "80d6bef8-300c-44bd-9e36-04ef874bdc29", "name": "aks-eastus-cluster", "state": "pending", "stateUnready": [], "managedState": "managed", "managedStateUnready": [], "managedTimestamp": "2022-05-19T20:33:59Z", "inUse": "false", "clusterType": "aks", "clusterVersion": "1.22", "clusterVersionString": "v1.22.6", "clusterCreationTimestamp": "0001-01-01T00:00:00Z", "namespaces": [], "defaultStorageClass": "ba6d5a64-a321-4fd7-9842-9adce829229a", "cloudID": "7b8d4252-293c-4c70-b101-7fd6b7d08e15", "credentialID": "04c067b2-df55-4d9c-8a3a-c869a779c276", "location": "eastus", "isMultizonal": "false", "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/hasNonTridentCSIDriverSupport", "value": "true"}, {"name": "astra.netapp.io/labels/read-only/hasTridentDriverSupport", "value": "true"}, {"name": "astra.netapp.io/labels/read-only/azure/subscriptionID", "value": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxa2935"}, {"name": "astra.netapp.io/labels/read-only/cloudName", "value": "Azure"}], "creationTimestamp": "2022-05-19T20:33:59Z", "modificationTimestamp": "2022-05-19T20:34:03Z", "createdBy": "system"`
```
