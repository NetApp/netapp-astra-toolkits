# Storageclasses

The following `storageclasses` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getStorageClasses

This class utilizes both [getClouds](#getClouds) and [getClusters](#getClusters) to gather all storage classes known to Astra Control.  It makes an API call per valid cloud+cluster combination (whether a managed or unmanaged cluster), and combines all responses into a single data structure.

In large environments, a `cloudType` filter (exact match) can be provided to only display storageClasses from clusters belonging to a single cloud type to speed up operations.
