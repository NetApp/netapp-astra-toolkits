# Cloud and Cluster Classes

These classes all relate to clouds and Kubernetes clusters, and all inherit the [SDKCommon](../baseClasses/README.md#SDKCommon) class.

## getClusters

This class utilizes [getClouds](#getClouds) to make an API call *per cloud* to get all clusters (both managed and unmanaged) known to Astra Control, with the following optional filters:

* `hideManaged`: boolean (default False) that when True, it does not return any of the currently managed clusters.
* `hideUnmanaged`: boolean (default False) that when True, it does not return any of the currently unmanaged clusters.
* `nameFilter`: partial match filter for the cluster name (`prod` would match `aks-prod1` and `gke-production`)

## getClouds

This class gets all clouds currently managed via Astra Control.  In 22.08 versions of Astra Control, Astra Control Center will only have a single `Private` cloud, and Astra Control Service will have at most three (`aws`, `azure`, and `gcp`).  In future software versions, this will be expanded.

The response can be filtered by a single cloudType (`aws`, `azure`, `gcp`, or `private`).

## getStorageClasses

This class utilizes both [getClouds](#getClouds) and [getClusters](#getClusters) to gather all storage classes known to Astra Control.  It makes an API call per valid cloud+cluster combination (whether a managed or unmanaged cluster), and combines all responses into a single data structure.

In large environments, a `cloudType` filter (exact match) can be provided to only display storageClasses from clusters belonging to a single cloud type to speed up operations.

## manageCluster

This class takes an unmanaged clusterID and a default storageClassID and has Astra Control manage the cluster (which in turn allows for application management).

In ACS environments, clusters are automatically discovered and listed as "unmanaged" clusters via the cloud credentials provided.  In ACC environments, a kubeconfig file must first be provided by [createCredential](../accountClasses/README.md#createCredential) and then [addCluster](#addCluster) must be called  prior to it appearing as unmanaged.

## deleteCluster

This class is meant for ACC environments only.  [unmanageCluster](#unmanageCluster) should be called first, then this class (deleteCluster), and finally [destroyCredential](../accountClasses/README.md#destroyCredential) to properly clean up Kubernetes cluster resources in ACC environments.

## unmanageCluster

This class takes a currently managed Kubernetes cluster and makes it an unmanaged cluster.  In ACS environments, only this class needs to be called to remove a cluster, but in ACC environments calling this class should be followed by [deleteCluster](#deleteCluster) and then [destroyCredential](../accountClasses/README.md#destroyCredential).

It is recommended to first [unmanage all apps](../appClasses/README.md#unmanageApp) from the cluster prior to cluster unmanagement.

## addCluster

This class is meant for ACC environments only, and  takes a kubeconfig [credentialID](../accountClasses/README.md#getCredentials) as input to add the cluster to the "unmanaged" cluster list.  The cluster must then be [managed](#manageCluster) to fully bring the cluster under ACC's control.
