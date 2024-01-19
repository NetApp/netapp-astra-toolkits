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


def get_cluster_namespaces(ignore_namespaces):
    """Return a list of non-system namespaces on the cluster"""
    namespaces = astraSDK.k8s.getNamespaces().main(systemNS=ignore_namespaces)
    return [x["metadata"]["name"] for x in namespaces["items"]]


def get_astra_namespaces():
    """Return a list of namespaces already protected by Astra"""
    return_list = []
    for app in astraSDK.k8s.getResources().main(
        "applications", version="v1alpha1", group="management.astra.netapp.io"
    )["items"]:
        return_list += [ns["namespace"] for ns in app["spec"]["includedNamespaces"]]
    return return_list


def protect_namespace(namespace):
    """Manage an app named {namespace} in namespace {namespace} via a toolkit command
    which generates and creates the necessary custom resource"""
    print(f"--> managing namespace {namespace}")
    toolkit.main(argv=f"-n -f manage app {namespace} {namespace}".split())


def main():
    """Find all namespaces which aren't part of the IGNORE_NAMESPACES env variable,
    and which are not currently managed, and then manage them."""
    ignore_namespaces = os.environ.get("IGNORE_NAMESPACES").split(",")
    cluster_namespaces = get_cluster_namespaces(ignore_namespaces)
    astra_namespaces = get_astra_namespaces()

    for namespace in set(cluster_namespaces) - set(astra_namespaces):
        protect_namespace(namespace)


if __name__ == "__main__":
    main()
