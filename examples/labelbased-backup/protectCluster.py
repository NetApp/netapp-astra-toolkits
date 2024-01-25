#!/usr/bin/env python3
"""
   Copyright 2023 NetApp, Inc

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import os
import random

import astraSDK
import toolkit


# Default protection levels, which are overridden by the CronJob labels
PROTECTION_LEVELS = {
    os.environ.get("GOLD_LABEL"): {
        "hourly": {"num_backups": 3, "num_snapshots": 3, "minute": random.randint(0, 59)},
        "daily": {"num_backups": 3, "num_snapshots": 3, "minute": random.randint(0, 59), "hour": 1},
        "weekly": {
            "num_backups": 3,
            "num_snapshots": 3,
            "minute": random.randint(0, 59),
            "hour": 2,
            "day_of_week": 1,
        },
        "monthly": {
            "num_backups": 3,
            "num_snapshots": 3,
            "minute": random.randint(0, 59),
            "hour": 3,
            "day_of_month": 1,
        },
    },
    os.environ.get("SILVER_LABEL"): {
        "hourly": {"num_backups": 1, "num_snapshots": 1, "minute": random.randint(0, 59)},
        "daily": {"num_backups": 1, "num_snapshots": 1, "minute": random.randint(0, 59), "hour": 1},
        "weekly": {
            "num_backups": 1,
            "num_snapshots": 1,
            "minute": random.randint(0, 59),
            "hour": 2,
            "day_of_week": 1,
        },
        "monthly": {
            "num_backups": 1,
            "num_snapshots": 1,
            "minute": random.randint(0, 59),
            "hour": 3,
            "day_of_month": 1,
        },
    },
    os.environ.get("BRONZE_LABEL"): {
        "hourly": {"num_backups": 0, "num_snapshots": 1, "minute": random.randint(0, 59)},
        "daily": {"num_backups": 0, "num_snapshots": 1, "minute": random.randint(0, 59), "hour": 1},
        "weekly": {
            "num_backups": 0,
            "num_snapshots": 1,
            "minute": random.randint(0, 59),
            "hour": 2,
            "day_of_week": 1,
        },
        "monthly": {
            "num_backups": 0,
            "num_snapshots": 1,
            "minute": random.randint(0, 59),
            "hour": 3,
            "day_of_month": 1,
        },
    },
}


def get_astra_namespaces():
    """Return a list of namespaces already protected by Astra"""
    return_list = []
    for app in astraSDK.k8s.getResources().main("applications")["items"]:
        return_list += [ns["namespace"] for ns in app["spec"]["includedNamespaces"]]
    return return_list


def get_bucket():
    """Returns the names of two available buckets/appVaults"""
    desired_bucket = os.environ.get("BUCKET")
    desired_gold_bucket = os.environ.get("GOLD_BUCKET")
    buckets = astraSDK.k8s.getResources().main("appvaults")
    available_bucket_list = [
        x["metadata"]["name"]
        for x in buckets["items"]
        if x.get("status") and x["status"].get("state") and x["status"]["state"] == "available"
    ]
    # If there are no available buckets, raise an error
    if not available_bucket_list:
        raise SystemError(f"No bucket/appVault found in an available state, {buckets=}")
    # If there's only one available bucket, it doesn't matter what was specified, warn and return
    elif len(available_bucket_list) == 1:
        print(
            "WARNING: only a single bucket in an available state, the default bucket and the "
            "secondary gold bucket will be the same, reducing resiliency, {buckets=}"
        )
        return available_bucket_list[0], available_bucket_list[0]
    # If both desired buckets are available, then we're all set, return desired buckets
    if desired_bucket in available_bucket_list and desired_gold_bucket in available_bucket_list:
        return desired_bucket, desired_gold_bucket
    # Otherwise, either one or both of the desired buckets are not available
    desired_bucket_available, desired_gold_bucket_available = False, False
    if desired_bucket in available_bucket_list:
        desired_bucket_available = True
    elif desired_gold_bucket in available_bucket_list:
        desired_gold_bucket_available = True
    # If neither are available, just return the first two
    if not desired_bucket_available and not desired_gold_bucket_available:
        return available_bucket_list[0], available_bucket_list[1]
    # If here, one of the two specified buckets is available, so return it and the next available
    if desired_bucket_available:
        return desired_bucket, [x for x in available_bucket_list if x != desired_bucket][0]
    return [x for x in available_bucket_list if x != desired_gold_bucket][0], desired_gold_bucket


def build_protections_list(policy):
    """Returns a list of protections by granularity"""
    return [
        f"-g hourly  -s {policy['hourly']['num_snapshots']} -b {policy['hourly']['num_backups']} "
        f"-m {policy['hourly']['minute']}",
        f"-g daily   -s {policy['daily']['num_snapshots']} -b {policy['daily']['num_backups']} "
        f"-m {policy['daily']['minute']} -H {policy['daily']['hour']}",
        f"-g weekly  -s {policy['weekly']['num_snapshots']} -b {policy['weekly']['num_backups']} "
        f"-m {policy['weekly']['minute']} -H {policy['weekly']['hour']} "
        f"-W {policy['weekly']['day_of_week']}",
        f"-g monthly -s {policy['monthly']['num_snapshots']} -b {policy['monthly']['num_backups']} "
        f"-m {policy['monthly']['minute']} -H {policy['monthly']['hour']} "
        f"-M {policy['monthly']['day_of_month']}",
    ]


def protect_namespace(namespace):
    """Manage an app named {namespace} in namespace {namespace} via a toolkit command
    which generates and creates the necessary custom resource"""
    print(f"--> managing namespace {namespace}")
    toolkit.main(argv=f"--v3 -f manage app {namespace} {namespace}".split())


def create_protection_policy(namespace, protection, bucket):
    """Creates a protection policy for a given namespace and granularity"""
    print(f"    --> creating {protection[3:10]} protection policy")
    toolkit.main(argv=f"--v3 -f create protection {namespace} -u {bucket} {protection}".split())


def main():
    cluster_namespaces = astraSDK.k8s.getNamespaces().main()
    protected_namespaces_list = get_astra_namespaces()
    protection_label_key = os.environ.get("PROTECTION_LABEL_KEY")
    bucket, gold_bucket = get_bucket()

    # Loop through all cluster namespaces
    for cluster_namespace in cluster_namespaces["items"]:
        # We only care about unprotected namespaces
        if cluster_namespace["metadata"]["name"] not in protected_namespaces_list:
            # Ensure the protection label key is present in the namespace metadata
            if protection_label_key in cluster_namespace["metadata"]["labels"].keys():
                policy_name = cluster_namespace["metadata"]["labels"][protection_label_key]
                # Ensure the same key's value is present in the global protection levels dict
                if policy_name in PROTECTION_LEVELS.keys():
                    # Protect the namespace and create each protection policy
                    protect_namespace(cluster_namespace["metadata"]["name"])
                    protection_list = build_protections_list(PROTECTION_LEVELS[policy_name])
                    for protection in protection_list:
                        create_protection_policy(
                            cluster_namespace["metadata"]["name"],
                            protection,
                            gold_bucket if policy_name == os.environ.get("GOLD_LABEL") else bucket,
                        )
        else:
            print(f"{cluster_namespace['metadata']['name']} already protected, skipping")


if __name__ == "__main__":
    main()
