# Users

The following `users` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getUsers

This class returns all users associated with the Astra Control instance.  It also optionally takes in a `nameFilter` argument (partial match on either first or last name) to reduce the data returned.

## createUser

This class creates a user based on an email address.  This user must then be tied to a [rolebinding](../rolebindings/README.md#createRolebinding), and if a local user, an associated [credential](../credentials/README.md#createCredential).
