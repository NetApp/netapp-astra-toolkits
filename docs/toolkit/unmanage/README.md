# Unmanage

The `unmanage` argument allows you to unmanage a currently managed object:

* [App](#app)
* [Bucket](#bucket)
* [Cloud](#cloud)
* [Cluster](#cluster)

```text
$ actoolkit unmanage -h
usage: actoolkit unmanage [-h] {app,bucket,cloud,cluster} ...

options:
  -h, --help            show this help message and exit

objectType:
  {app,bucket,cloud,cluster}
    app                 unmanage app
    bucket              unmanage bucket
    cloud               unmanage cloud
    cluster             unmanage cluster
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
