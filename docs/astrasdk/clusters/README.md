# Clusters

The following `clusters` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getClusters

This class utilizes [getClouds](#getClouds) to make an API call *per cloud* to get all clusters (both managed and unmanaged) known to Astra Control, with the following optional filters:

* `hideManaged`: boolean (default False) that when True, it does not return any of the currently managed clusters.
* `hideUnmanaged`: boolean (default False) that when True, it does not return any of the currently unmanaged clusters.
* `nameFilter`: partial match filter for the cluster name (`prod` would match `aks-prod1` and `gke-production`)

## manageCluster

This class takes an unmanaged clusterID and a default storageClassID and has Astra Control manage the cluster (which in turn allows for application management).

In ACS environments, clusters are automatically discovered and listed as "unmanaged" clusters via the cloud credentials provided.  In ACC environments, a kubeconfig file must first be provided by [createCredential](../accountClasses/README.md#createCredential) and then [addCluster](#addCluster) must be called  prior to it appearing as unmanaged.

## unmanageCluster

This class takes a currently managed Kubernetes cluster and makes it an unmanaged cluster.  In ACS environments, only this class needs to be called to remove a cluster, but in ACC environments calling this class should be followed by [deleteCluster](#deleteCluster) and then [destroyCredential](../accountClasses/README.md#destroyCredential).

It is recommended to first [unmanage all apps](../appClasses/README.md#unmanageApp) from the cluster prior to cluster unmanagement.

## addCluster

This class takes a generic kubeconfig [credentialID](../accountClasses/README.md#getCredentials) as input to add the cluster to the "unmanaged" cluster list.  The cluster must then be [managed](#manageCluster) to fully bring the cluster under Astra's control.

## deleteCluster

This class is meant for clusters which have been added via [addCluster](#addCluster) only.  [unmanageCluster](#unmanageCluster) should be called first, then this class (deleteCluster), and finally [destroyCredential](../accountClasses/README.md#destroyCredential) to properly clean up Kubernetes cluster resources in ACC environments.
