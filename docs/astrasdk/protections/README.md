# Protections

The following `protections` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getProtectionpolicies

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all proection policies for each application.  It then combines protection policies for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/schedules` API call to speed up operations.

## createProtectionpolicy

This class creates a protection policy for a single app ID and a single granularity (hourly/daily/weekly/monthly).  To fully protect an application, this class should be called four times, once for each granularity.

This class does not perform any validation of the arguments that are provided, that instead is left to the calling function.

## destroyProtectiontionpolicy

This class takes in an appID and protectionID, and destroys this protection policy for an application/granularity combination.  If removing all protection policies for a given application, this class should be called four times, once for each granularity.
