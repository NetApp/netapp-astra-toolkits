# Scripts

The following `scripts` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getScripts

This class gets all of the scripts (also known as "hookSources") managed by Astra Control.  These scripts can then be used to create [execution hooks](../appClasses/README.md#createHook) for any number of applications.

## createScript

This class takes in a base64 encoded script to be used as an [execution hook source](../appClasses/README.md#createHook).  There is no validation performed to ensure the encoded script is in the correct format, that is instead left to the calling function.

## destroyScript

This class takes in a scriptID and destroys the script.  It is recommended to destroy all [execution hooks](../appClasses/README.md#destroyHook) utilizing the script prior to script destruction.
