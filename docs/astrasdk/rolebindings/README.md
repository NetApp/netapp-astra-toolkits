# Rolebindings

The following `rolebindings` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getRolebindings

This class returns all users associated with the Astra Control instance.  It also optionally takes in an `idFilter` argument (exact match on either user or group ID) to reduce the data returned.

## createRolebinding

This class creates a rolebinding based on a role (one of `viewer`, `member`, `admin`, or `owner`), and *either* a user ID or group ID.

## destroyRolebinding

This class destroys a rolebinding based on a `roleBindingID`.  If this rolebinding is also associated with a user, Astra Control automatically destroys that user as well.
