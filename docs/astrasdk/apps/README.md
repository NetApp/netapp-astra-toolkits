# Apps

The following `apps` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getApps

This class makes an API call to gather **all** apps managed by Astra, and then removes unneeded apps/data from the reponse object depending upon various filters:

* `namespace`: filter by the namespace the app is in
* `nameFilter`: partial match filter for the application name (`word` would match `wordpress-prod` and `wordpress-dev`)
* `cluster`: filter by a specific Kubernetes cluster

## manageApp

This class defines an application by taking in namespace and cluster information, and optionally any Kubernetes labels (for further granularity).  Once managed, the application is eligible for data protection operations.

## unmanageApp

This class undefines an existing application.  It is recommended to remove all existing snapshots and backups priort to unmanaging the app.

## cloneApp

This class creates a new application based on either an existing snapshot, backup, or running application (only a single one of these IDs should be provided).  A clone can be within the same cluster, or to a new cluster.

This class submits the clone operation, with monitoring the success (or failure) of the operation left to other classes.

## restoreApp

This class restores an existing application to a previous snapshot or backup.  It is a destructive action that overwrites the current application.

This class submits the restore operation, with monitoring the success (or failure) of the operation left to other classes.

## getAppAssets

This class takes in a single app ID, and returns all of the assets (also known as resources) managed under the application by Astra Control.
