# App Classes

These classes are all related to `apps`, and all inherit the [SDKCommon](../baseClasses/README.md#SDKCommon) class.

## getApps

This class makes an API call to gather **all** apps managed by Astra, and then removes unneeded apps/data from the reponse object depending upon various filters:

* `namespace`: filter by the namespace the app is in
* `nameFilter`: partial match filter for the application name (`word` would match `wordpress-prod` and `wordpress-dev`)
* `cluster`: filter by a specific Kubernetes cluster

## cloneApp

This class creates a new application based on either an existing snapshot, backup, or running application (only a single one of these IDs should be provided).  A clone can be within the same cluster, or to a new cluster.

This class submits the clone operation, with monitoring the success (or failure) of the operation left to other classes.

## restoreApp

This class restores an existing application to a previous snapshot or backup.  It is a destructive action that overwrites the current application.

This class submits the restore operation, with monitoring the success (or failure) of the operation left to other classes.

## manageApp

This class defines an application by taking in namespace and cluster information, and optionally any Kubernetes labels (for further granularity).  Once managed, the application is eligible for data protection operations.

## unmanageApp

This class undefines an existing application.  It is recommended to remove all existing snapshots and backups priort to unmanaging the app.

## getNamespaces

This class makes an API call to get all of the namespaces known to Astra.  It can be filtered by the following values:

* `clusterID`: only show namespaces from a particular cluster
* `nameFilter`: partial match filter for the namespace name (`word` would match `wordpress-prod` and `wordpress-dev`)
* `unassociated`: boolean (default False), when True only namespaces which do not have an application associated are shown
* `minuteFilter`: only show namespaces which were discovered in the last X number of minutes

## getAppAssets

This class takes in a single app ID, and returns all of the assets (also known as resources) managed under the application by Astra Control.

## getHooks

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all execution hooks for each application.  It then combines execution hooks for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/executionHooks` API call to speed up operations.

## createHook

This class takes in an appID and scriptID (among other arguments) to create an execution hook for a single app based on a single [script](../accountClasses/README.md#getScripts).  It is likely this class needs to be called multiple times per managed application based on the [types of execution hook](https://docs.netapp.com/us-en/astra-control-service/use/manage-app-execution-hooks.html) required.

## destroyHook

This class takes in an appID and hookID and destroys the execution hook.
