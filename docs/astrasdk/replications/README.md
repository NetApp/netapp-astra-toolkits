# Replications

The following `replications` classes all inherit the [SDKCommon](../common/README.md#SDKCommon) class.

## getReplicationpolicies

This class gets all "Snap Mirror" replication policies (aka appMirrors) known to Astra Control.  It optionally takes in an `appFilter` argument which when provided, only returns replication policies which have a matching source or destination appName or appID.

## createReplicationpolicy

This class is currently only meant for ACC environments, and creates a replication policy (aka snap mirror or appMirror) for a single application.  There is no validation of inputs in this class, that instead is left to the calling function.

To fully configure a proper replication, in addition to this class being called a [protection policy](#createProtectionpolicy) with a `custom` granularity must also be created which defines the frequency of data replication.

## updateReplicationpolicy

This class updates a replication policy, with the purpose of failing over, reversing, or resyncing the policy.  Each of these operations is handled uniquely based on the arguments provided.  This class does not perform any validation of the arguments provided, that instead is handled by the calling function.

## destroyReplicationpolicy

This class takes in a replicationID and destroys the replication policy.  The corresponding [protection policy](#getProtectionpolicies) should also be destroyed to properly clean up all resources associated with the replication.
