# Snapshots

The following `snapshots` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## takeSnap

This class takes in a single appID and a snapshot name, and initiates a snapshot.  It only submits the snapshot operation, with monitoring the success (or failure) of the operation left to other classes.

## getSnaps

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all snapshots for each application.  It then combines snapshots for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/appSnaps` API call to speed up operations.

## destroySnapshot

This class takes in a single appID and snapshotID, and initiates the destruction of the snapshot.  It only submits the snapshot destruction operation, with monitoring the success (or failure) of the operation left to other classes.
