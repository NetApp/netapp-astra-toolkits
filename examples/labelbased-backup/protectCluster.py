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

import astraSDK
import toolkit


# Default protection levels, which are overridden by the CronJob labels
PROTECTION_LEVELS = {
    os.environ.get("GOLD_LABEL"): {
        "hourly": {"num_backups": 3, "num_snapshots": 3, "minute": 0},
        "daily": {"num_backups": 3, "num_snapshots": 3, "minute": 30, "hour": 1},
        "weekly": {"num_backups": 3, "num_snapshots": 3, "minute": 30, "hour": 2, "day_of_week": 1},
        "monthly": {
            "num_backups": 3,
            "num_snapshots": 3,
            "minute": 30,
            "hour": 3,
            "day_of_month": 1,
        },
    },
    os.environ.get("SILVER_LABEL"): {
        "hourly": {"num_backups": 1, "num_snapshots": 1, "minute": 0},
        "daily": {"num_backups": 1, "num_snapshots": 1, "minute": 30, "hour": 1},
        "weekly": {"num_backups": 1, "num_snapshots": 1, "minute": 30, "hour": 2, "day_of_week": 1},
        "monthly": {
            "num_backups": 1,
            "num_snapshots": 1,
            "minute": 30,
            "hour": 3,
            "day_of_month": 1,
        },
    },
    os.environ.get("BRONZE_LABEL"): {
        "hourly": {"num_backups": 0, "num_snapshots": 1, "minute": 0},
        "daily": {"num_backups": 0, "num_snapshots": 1, "minute": 30, "hour": 1},
        "weekly": {"num_backups": 0, "num_snapshots": 1, "minute": 30, "hour": 2, "day_of_week": 1},
        "monthly": {
            "num_backups": 0,
            "num_snapshots": 1,
            "minute": 30,
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
    """Returns a name of an available bucket/appVault"""
    desired_bucket = os.environ.get("BUCKET")
    buckets = astraSDK.k8s.getResources().main("appvaults")
    if desired_bucket in [
        x["metadata"]["name"]
        for x in buckets["items"]
        if x.get("status") and x["status"].get("state") and x["status"]["state"] == "available"
    ]:
        return desired_bucket
    for bucket in buckets["items"]:
        if (
            bucket.get("status")
            and bucket["status"].get("state")
            and bucket["status"]["state"] == "available"
        ):
            return bucket["metadata"]["name"]
    raise SystemError(f"No bucket/appVault found in an available state, {buckets=}")


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
    toolkit.main(argv=f"-n -f manage app {namespace} {namespace}".split())


def create_protection_policy(namespace, protection, bucket):
    """Creates a protection policy for a given namespace and granularity"""
    print(f"    --> creating {protection[3:10]} protection policy")
    toolkit.main(argv=f"-n -f create protection {namespace} -u {bucket} {protection}".split())


def main():
    cluster_namespaces = astraSDK.k8s.getNamespaces().main()
    protected_namespaces_list = get_astra_namespaces()
    protection_label_key = os.environ.get("PROTECTION_LABEL_KEY")
    bucket = get_bucket()

    # Loop through all cluster namespaces
    for cluster_namespace in cluster_namespaces["items"]:
        # We only care about unprotected namespaces
        if cluster_namespace["metadata"]["name"] not in protected_namespaces_list:
            # Ensure the protection label key is present in the namespace metadata
            if protection_label_key in cluster_namespace["metadata"]["labels"].keys():
                policy_name = cluster_namespace["metadata"]["labels"][protection_label_key]
                # Ensure the same key's value is present in the global protection levels dict
                if policy_name in PROTECTION_LEVELS.keys():
                    # Build the protection commands based on the corresponding policy
                    protection_list = build_protections_list(PROTECTION_LEVELS[policy_name])
                    # Create each protection granularity
                    for protection in protection_list:
                        create_protection_policy(
                            cluster_namespace["metadata"]["name"], protection, bucket
                        )


if __name__ == "__main__":
    main()
