# Buckets

The following `buckets` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getBuckets

This class returns all object storage buckets associated with the Astra Control instance.  It can optionally be filtered by a `nameFilter` (partial match based on the bucket name) or a `provider` (exact match of either `aws`, `azure`, `gcp`, `generic-s3`, `ontap-s3`, or `storagegrid-s3`) arguments to reduce the data returned.

## manageBucket

This class manages an object storage resource for storing backups.  It requires an existing [credentialID](#createCredential) which contains the object storage bucket credentials (composed of an access key and a secret access key), a provider type (one of `aws`, `azure`, `gcp`, `generic-s3`, `ontap-s3`, or `storagegrid-s3`), and potentially additional parameters depending upon the provider type.  This class does not perform any validation of inputs, instead that is left to the calling function.

## unmanageBucket

This class takes in a bucketID and removes the bucket from Astra Control management.  In order to be removed, the bucket can not be storing any application backups.
