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


def get_cluster_namespaces(ignore_namespaces):
    """Return a list of non-system namespaces on the cluster"""
    namespaces = astraSDK.k8s.getNamespaces().main(systemNS=ignore_namespaces)
    return [x["metadata"]["name"] for x in namespaces["items"]]


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
    available_bucket_list = [
        x["metadata"]["name"]
        for x in buckets["items"]
        if x.get("status") and x["status"].get("state") and x["status"]["state"] == "available"
    ]
    # If there are no available buckets, raise an error
    if not available_bucket_list:
        raise SystemError(f"No bucket/appVault found in an available state, {buckets=}")
    # Return either the desired bucket, or the first available bucket
    if desired_bucket in available_bucket_list:
        return desired_bucket
    return available_bucket_list[0]


def build_protections_list():
    """Returns a list of protections by granularity"""
    hour = os.environ.get("HOUR")
    day_of_week = os.environ.get("DAY_OF_WEEK")
    day_of_month = os.environ.get("DAY_OF_MONTH")
    return [
        f"-g hourly  --minute {random.randint(0, 59)}",
        f"-g daily   --minute {random.randint(0, 59)} --hour {hour}",
        f"-g weekly  --minute {random.randint(0, 59)} --hour {hour} --dayOfWeek {day_of_week}",
        f"-g monthly --minute {random.randint(0, 59)} --hour {hour} --dayOfMonth {day_of_month}",
    ]


def protect_namespace(namespace):
    """Manage an app named {namespace} in namespace {namespace} via a toolkit command
    which generates and creates the necessary custom resource"""
    print(f"--> managing namespace {namespace}")
    toolkit.main(argv=f"--v3 -f manage app {namespace} {namespace}".split())


def create_protection_policy(namespace, protection, bucket):
    """Creates a protection policy for a given namespace and granularity"""
    num_backups = os.environ.get("BACKUPS_TO_KEEP")
    num_snapshots = os.environ.get("SNAPSHOTS_TO_KEEP")
    print(f"    --> creating {protection[3:10]} protection policy")
    cmd = (
        f"--v3 -f create protection {namespace} -u {bucket} -b {num_backups} -s {num_snapshots}"
        f" {protection}"
    )
    toolkit.main(argv=cmd.split())


def main():
    """Find all namespaces which aren't part of the IGNORE_NAMESPACES env variable,
    and which are not currently managed, and then manage them."""
    ignore_namespaces = os.environ.get("IGNORE_NAMESPACES").split(",")
    cluster_namespaces = get_cluster_namespaces(ignore_namespaces)
    astra_namespaces = get_astra_namespaces()
    bucket = get_bucket()
    protection_list = build_protections_list()

    for namespace in set(cluster_namespaces) - set(astra_namespaces):
        protect_namespace(namespace)
        for protection in protection_list:
            create_protection_policy(namespace, protection, bucket)


if __name__ == "__main__":
    main()
