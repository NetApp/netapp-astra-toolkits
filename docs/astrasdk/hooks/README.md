# Hooks

The following `hooks` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getHooks

This class utilizes [getApps](../appClasses/README.md#getApps) to iterate over every managed application, and gathers all execution hooks for each application.  It then combines execution hooks for all applications into a single data structure.

In large environments, an `appFilter` (exact match based on either the application name or ID) can be provided which only makes a single `/executionHooks` API call to speed up operations.

## createHook

This class takes in an appID and scriptID (among other arguments) to create an execution hook for a single app based on a single [script](../accountClasses/README.md#getScripts).  It is likely this class needs to be called multiple times per managed application based on the [types of execution hook](https://docs.netapp.com/us-en/astra-control-service/use/manage-app-execution-hooks.html) required.

## destroyHook

This class takes in an appID and hookID and destroys the execution hook.
