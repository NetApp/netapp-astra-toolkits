# Backups

The following `backups` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getBackups

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all backups for each application.  It then combines backups for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/appBackups` API call to speed up operations.

## takeBackup

This class takes in a single appID and a backup name, and initiates a backup.  It only submits the backup operation, with monitoring the success (or failure) of the operation left to other classes.

## destroyBackup

This class takes in a single appID and backupID, and initiates the destruction of the backup.  It only submits the backup destruction operation, with monitoring the success (or failure) of the operation left to other classes.
