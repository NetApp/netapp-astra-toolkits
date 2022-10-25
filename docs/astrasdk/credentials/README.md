# Credentials

The following `credentials` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getCredentials

This class gets all of the credentials managed by Astra Control.  It can optionally be filtered by setting `kubeconfigOnly=True` to only show kubeconfig credentials (useful for ACC cluster management).

## createCredential

This class is used to create an S3 (object storage bucket) or Kubeconfig credential.  This class does not perform any validation of the arguments provided, instead this is left to the calling function.

## destroyCredential

This class takes in a credentialID and destroys the credential.  Use with caution, as there is no going back.  In ACC environments, it is recommended to call this class after first calling [unmanageCluster](../cloudClusterClasses/README.md#unmanageCluster) and [deleteCluster](../cloudClusterClasses/README.md#deleteCluster) to properly clean up Kubernetes cluster resources.
