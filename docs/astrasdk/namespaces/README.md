# Namespaces

The following `namespaces` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getNamespaces

This class makes an API call to get all of the namespaces known to Astra.  It can be filtered by the following values:

* `clusterID`: only show namespaces from a particular cluster
* `nameFilter`: partial match filter for the namespace name (`word` would match `wordpress-prod` and `wordpress-dev`)
* `unassociated`: boolean (default False), when True only namespaces which do not have an application associated are shown
* `minuteFilter`: only show namespaces which were discovered in the last X number of minutes
