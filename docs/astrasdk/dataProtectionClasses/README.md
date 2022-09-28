# Data Protection Classes

These classes all relate to application data management, and all inherit the [SDKCommon](../baseClasses/README.md#SDKCommon) class.

## getBackups

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all backups for each application.  It then combines backups for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/appBackups` API call to speed up operations.

## takeBackup

This class takes in a single appID and a backup name, and initiates a backup.  It only submits the backup operation, with monitoring the success (or failure) of the operation left to other classes.

## destroyBackup

This class takes in a single appID and backupID, and initiates the destruction of the backup.  It only submits the backup destruction operation, with monitoring the success (or failure) of the operation left to other classes.

## getProtectionpolicies

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all proection policies for each application.  It then combines protection policies for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/schedules` API call to speed up operations.

## createProtectionpolicy

This class creates a protection policy for a single app ID and a single granularity (hourly/daily/weekly/monthly).  To fully protect an application, this class should be called four times, once for each granularity.

This class does not perform any validation of the arguments that are provided, that instead is left to the calling function.

## destroyProtectiontionpolicy

This class takes in an appID and protectionID, and destroys this protection policy for an application/granularity combination.  If removing all protection policies for a given application, this class should be called four times, once for each granularity.

## takeSnap

This class takes in a single appID and a snapshot name, and initiates a snapshot.  It only submits the snapshot operation, with monitoring the success (or failure) of the operation left to other classes.

## getSnaps

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all snapshots for each application.  It then combines snapshots for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/appSnaps` API call to speed up operations.

## destroySnapshot

This class takes in a single appID and snapshotID, and initiates the destruction of the snapshot.  It only submits the snapshot destruction operation, with monitoring the success (or failure) of the operation left to other classes.

## getReplicationpolicies

This class gets all "Snap Mirror" replication policies (aka appMirrors) known to Astra Control.  It optionally takes in an `appFilter` argument which when provided, only returns replication policies which have a matching source or destination appName or appID.

## createReplicationpolicy

This class is currently only meant for ACC environments, and creates a replication policy (aka snap mirror or appMirror) for a single application.  There is no validation of inputs in this class, that instead is left to the calling function.

To fully configure a proper replication, in addition to this class being called a [protection policy](#createProtectionpolicy) with a `custom` granularity must also be created which defines the frequency of data replication.

## updateReplicationpolicy

This class updates a replication policy, with the purpose of failing over, reversing, or resyncing the policy.  Each of these operations is handled uniquely based on the arguments provided.  This class does not perform any validation of the arguments provided, that instead is handled by the calling function.

## destroyReplicationpolicy

This class takes in a replicationID and destroys the replication policy.  The corresponding [protection policy](#getProtectionpolicies) should also be destroyed to properly clean up all resources associated with the replication.
