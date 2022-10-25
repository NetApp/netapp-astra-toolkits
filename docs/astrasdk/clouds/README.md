# Clouds

The following `clouds` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getClouds

This class gets all clouds currently managed via Astra Control.  In 22.08 versions of Astra Control, Astra Control Center will only have a single `Private` cloud, and Astra Control Service will have at most three (`aws`, `azure`, and `gcp`).  In future software versions, this will be expanded.

The response can be filtered by a single cloudType (`aws`, `azure`, `gcp`, or `private`).
