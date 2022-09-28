# Account level Classes

These classes all relate to broader Astra Control account level objects, and all inherit the [SDKCommon](../baseClasses/README.md#SDKCommon) class.

## getScripts

This class gets all of the scripts (also known as "hookSources") managed by Astra Control.  These scripts can then be used to create [execution hooks](../appClasses/README.md#createHook) for any number of applications.

## createScript

This class takes in a base64 encoded script to be used as an [execution hook source](../appClasses/README.md#createHook).  There is no validation performed to ensure the encoded script is in the correct format, that is instead left to the calling function.

## destroyScript

This class takes in a scriptID and destroys the script.  It is recommended to destroy all [execution hooks](../appClasses/README.md#destroyHook) utilizing the script prior to script destruction.

## getCredentials

This class gets all of the credentials managed by Astra Control.  It can optionally be filtered by setting `kubeconfigOnly=True` to only show kubeconfig credentials (useful for ACC cluster management).

## createCredential

This class is used to create an S3 (object storage bucket) or Kubeconfig credential.  This class does not perform any validation of the arguments provided, instead this is left to the calling function.

## destroyCredential

This class takes in a credentialID and destroys the credential.  Use with caution, as there is no going back.  In ACC environments, it is recommended to call this class after first calling [unmanageCluster](../cloudClusterClasses/README.md#unmanageCluster) and [deleteCluster](../cloudClusterClasses/README.md#deleteCluster) to properly clean up Kubernetes cluster resources.

## getEntitlements

This class does not take any inputs, and returns all entitlements (aka licenses) associated with the Astra Control instance.  This can also be used to programmatically determine whether it is an ACC or ACS environment.

## getUsers

This class returns all users associated with the Astra Control instance.  It also optionally takes in a `nameFilter` argument (partial match on either first or last name) to reduce the data returned.

## getBuckets

This class returns all object storage buckets associated with the Astra Control instance.  It can optionally be filtered by a `nameFilter` (partial match based on the bucket name) or a `provider` (exact match of either `aws`, `azure`, `gcp`, `generic-s3`, `ontap-s3`, or `storagegrid-s3`) arguments to reduce the data returned.

## manageBucket

This class manages an object storage resource for storing backups.  It requires an existing [credentialID](#createCredential) which contains the object storage bucket credentials (composed of an access key and a secret access key), a provider type (one of `aws`, `azure`, `gcp`, `generic-s3`, `ontap-s3`, or `storagegrid-s3`), and potentially additional parameters depending upon the provider type.  This class does not perform any validation of inputs, instead that is left to the calling function.

## unmanageBucket

This class takes in a bucketID and removes the bucket from Astra Control management.  In order to be removed, the bucket can not be storing any application backups.
