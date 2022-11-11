# Clouds

The following `clouds` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getClouds

This class gets all clouds currently managed via Astra Control.

The response can be filtered by a single cloudType (`aws`, `azure`, `gcp`, or `private`).

## manageCloud

This class manages a new cloud.  The `cloudType` input must be one of `AWS`, `Azure`, `GCP`, or `private`.

All non-`private` cloudTypes must also have a `credentialID` passed as an input.

## unmanageCloud

This class unmanages a cloud based on a given `cloudID`.  The associated `credentialID` should be [destroyed](../credentials/README.md#destroyCredential) after the cloud is unmanaged.
