#!/usr/bin/env python3
"""
   Copyright 2024 NetApp, Inc

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


import kubernetes
import sys

import astraSDK
from tkSrc import helpers

RED = "\033[31m"
ENDC = "\033[0m"


def main(argv, verbs, verbPosition, ard, acl, v3, v3_skip_tls_verify=False):
    """This function builds the argparse choices lists. To build these lists, a variety of external
    calls need to be made. The results of these calls are stored in ard (an instantiation of
    AstraResourceDicts) so the same call doesn't have to be made again later. The choices lists are
    stored in acl (an instantiation of ArgparseChoicesLists)"""

    if verbs["deploy"]:
        # This expression translates to "Is there an arg after the verb we found?"
        if len(argv) - verbPosition >= 2:
            if argv[verbPosition + 1] == "chart":
                ard.charts = helpers.updateHelm()
                acl.charts = ard.buildList("charts", "name")
                if v3:
                    ard.buckets = astraSDK.k8s.getResources(
                        config_context=v3, skip_tls_verify=v3_skip_tls_verify
                    ).main("appvaults")
                    acl.buckets = ard.buildList("buckets", "metadata.name")
            elif argv[verbPosition + 1] == "acp":
                ard.credentials = astraSDK.k8s.getSecrets(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main(namespace="trident")
                acl.credentials = ard.buildList("credentials", "metadata.name")

    elif verbs["clone"] or verbs["restore"]:
        if v3:
            ard.apps = astraSDK.k8s.getResources(
                config_context=v3, skip_tls_verify=v3_skip_tls_verify
            ).main("applications")
            acl.apps = ard.buildList("apps", "metadata.name")
            if verbs["restore"]:
                ard.backups = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("backups")
                ard.snapshots = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("snapshots")
                acl.dataProtections = ard.buildList("backups", "metadata.name") + ard.buildList(
                    "snapshots", "metadata.name"
                )
            if (
                len(argv) - verbPosition > 3
                and argv[verbPosition + 3] != "-h"
                and argv[verbPosition + 3] != "--help"
            ):
                for arg in argv[verbPosition + 1 :]:
                    if (
                        astraSDK.common.KubeCommon(
                            config_context=arg, silently_fail=True
                        ).api_client
                        is not None
                    ):
                        ard.storageClasses = astraSDK.k8s.getStorageClasses(
                            config_context=arg, skip_tls_verify=v3_skip_tls_verify
                        ).main()
                        acl.storageClasses = ard.buildList("storageClasses", "metadata.name")
                        break
            else:
                ard.storageClasses = astraSDK.k8s.getStorageClasses(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main()
                acl.storageClasses = ard.buildList("storageClasses", "metadata.name")
        else:
            ard.apps = astraSDK.apps.getApps().main()
            acl.apps = ard.buildList("apps", "id")
            ard.destClusters = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
            acl.destClusters = ard.buildList("destClusters", "id")
            if verbs["restore"]:
                ard.backups = astraSDK.backups.getBackups().main()
                ard.snapshots = astraSDK.snapshots.getSnaps().main()
                acl.dataProtections = ard.buildList("backups", "id") + ard.buildList(
                    "snapshots", "id"
                )
            # if the destination cluster has been specified, only show those storage classes
            if (clusterID := list(set(argv) & set(acl.destClusters))) and len(clusterID) == 1:
                ard.storageClasses = astraSDK.storageclasses.getStorageClasses().main(
                    clusterStr=clusterID[0], hideUnmanaged=True
                )
            else:
                ard.storageClasses = astraSDK.storageclasses.getStorageClasses().main(
                    hideUnmanaged=True
                )
            acl.storageClasses = list(set(ard.buildList("storageClasses", "name")))

    elif verbs["ipr"]:
        if v3:
            ard.apps = astraSDK.k8s.getResources(
                config_context=v3, skip_tls_verify=v3_skip_tls_verify
            ).main("applications")
            acl.apps = ard.buildList("apps", "metadata.name")
            if len(argv) - verbPosition >= 2:
                ard.backups = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("backups")
                ard.snapshots = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("snapshots")
                for a in argv[verbPosition + 1 :]:
                    acl.backups += ard.buildList(
                        "backups", "metadata.name", "spec.applicationRef", a
                    )
                    acl.snapshots += ard.buildList(
                        "snapshots", "metadata.name", "spec.applicationRef", a
                    )
        else:
            ard.apps = astraSDK.apps.getApps().main()
            acl.apps = ard.buildList("apps", "id")
            if len(argv) - verbPosition >= 2:
                ard.backups = astraSDK.backups.getBackups().main()
                ard.snapshots = astraSDK.snapshots.getSnaps().main()
                for a in argv[verbPosition + 1 :]:
                    acl.backups += ard.buildList("backups", "id", "appID", a)
                    acl.snapshots += ard.buildList("snapshots", "id", "appID", a)

    elif verbs["create"] and len(argv) - verbPosition >= 2:
        if (
            argv[verbPosition + 1] == "backup"
            or argv[verbPosition + 1] == "exechook"
            or argv[verbPosition + 1] == "hook"
            or argv[verbPosition + 1] == "protection"
            or argv[verbPosition + 1] == "replication"
            or argv[verbPosition + 1] == "schedule"
            or argv[verbPosition + 1] == "snapshot"
        ):
            if v3:
                ard.apps = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("applications")
                acl.apps = ard.buildList("apps", "metadata.name")
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
            if argv[verbPosition + 1] == "backup" or argv[verbPosition + 1] == "snapshot":
                if v3:
                    ard.buckets = astraSDK.k8s.getResources(
                        config_context=v3, skip_tls_verify=v3_skip_tls_verify
                    ).main("appvaults")
                    acl.buckets = ard.buildList("buckets", "metadata.name")
                else:
                    ard.buckets = astraSDK.buckets.getBuckets(quiet=True).main()
                    acl.buckets = ard.buildList("buckets", "id")
                # Generate acl.snapshots if an app was provided
                if argv[verbPosition + 1] == "backup":
                    for a in argv[verbPosition + 1 :]:
                        if a in acl.apps:
                            if v3:
                                ard.snapshots = astraSDK.k8s.getResources(
                                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                                ).main(
                                    "snapshots",
                                    filters=[{"keyFilter": "spec.applicationRef", "valFilter": a}],
                                )
                                acl.snapshots = ard.buildList("snapshots", "metadata.name")
                            else:
                                ard.snapshots = astraSDK.snapshots.getSnaps().main(appFilter=a)
                                acl.snapshots = ard.buildList("snapshots", "id")
            if argv[verbPosition + 1] == "hook" or argv[verbPosition + 1] == "exechook":
                if not v3:
                    ard.scripts = astraSDK.scripts.getScripts().main()
                    acl.scripts = ard.buildList("scripts", "id")
            if argv[verbPosition + 1] == "protection" or argv[verbPosition + 1] == "schedule":
                if v3:
                    ard.buckets = astraSDK.k8s.getResources(
                        config_context=v3, skip_tls_verify=v3_skip_tls_verify
                    ).main("appvaults")
                    acl.buckets = ard.buildList("buckets", "metadata.name")
                else:
                    ard.buckets = astraSDK.buckets.getBuckets().main()
                    acl.buckets = ard.buildList("buckets", "id")
            if argv[verbPosition + 1] == "replication":
                ard.destClusters = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
                acl.destClusters = ard.buildList("destClusters", "id")
                ard.storageClasses = astraSDK.storageclasses.getStorageClasses(quiet=True).main()
                acl.storageClasses = ard.buildList("storageClasses", "name")
                acl.storageClasses = list(set(acl.storageClasses))
        elif argv[verbPosition + 1] == "cluster":
            ard.clouds = astraSDK.clouds.getClouds().main()
            for cloud in ard.clouds["items"]:
                if cloud["cloudType"] not in ["GCP", "Azure", "AWS"]:
                    acl.clouds.append(cloud["id"])
            # Add a private cloud if it doesn't already exist
            if len(acl.clouds) == 0:
                rc = astraSDK.clouds.manageCloud(quiet=True).main("private", "private")
                if rc:
                    acl.clouds.append(rc["id"])
        elif argv[verbPosition + 1] == "user" or argv[verbPosition + 1] == "group":
            ard.namespaces = astraSDK.namespaces.getNamespaces().main()
            for namespace in ard.namespaces["items"]:
                acl.namespaces.append(namespace["id"])
                if namespace.get("kubernetesLabels"):
                    for label in namespace["kubernetesLabels"]:
                        labelString = label["name"]
                        if label.get("value"):
                            labelString += "=" + label["value"]
                        acl.labels.append(labelString)
            acl.labels = list(set(acl.labels))

    elif verbs["copy"]:
        ard.apps = astraSDK.apps.getApps().main()
        acl.apps = ard.buildList("apps", "id")
        if len(argv) - verbPosition > 2 and argv[verbPosition + 2] in acl.apps:
            acl.destApps = [x for x in acl.apps if x != argv[verbPosition + 2]]
        else:
            acl.destApps = [x for x in acl.apps]

    elif verbs["list"] and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "assets":
            ard.apps = astraSDK.apps.getApps().main()
            acl.apps = ard.buildList("apps", "id")

    elif (verbs["manage"] or verbs["define"]) and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "app" or argv[verbPosition + 1] == "application":
            if v3:
                ard.namespaces = astraSDK.k8s.getNamespaces(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main()
                acl.namespaces = ard.buildList("namespaces", "metadata.name")
            else:
                ard.namespaces = astraSDK.namespaces.getNamespaces().main()
                acl.namespaces = ard.buildList("namespaces", "name")
                acl.clusters = ard.buildList("namespaces", "clusterID")
                acl.clusters = list(set(acl.clusters))
        elif argv[verbPosition + 1] == "bucket" or argv[verbPosition + 1] == "appVault":
            if v3:
                ard.credentials = astraSDK.k8s.getSecrets(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main()
                acl.credentials = ard.buildList("credentials", "metadata.name")
                for c in argv[verbPosition + 1 :]:
                    if c in acl.credentials:
                        for d in ard.buildList("credentials", "data", fKey="metadata.name", fVal=c):
                            for i in d:
                                acl.keys.append(i)
                if not acl.keys:
                    acl.keys = [i for d in ard.buildList("credentials", "data") for i in d]
                acl.keys = list(set(acl.keys))
            else:
                ard.credentials = astraSDK.credentials.getCredentials().main()
                if ard.credentials:
                    for credential in ard.credentials["items"]:
                        if credential["metadata"].get("labels"):
                            credID = None
                            if credential.get("keyType") == "s3":
                                credID = credential["id"]
                            else:
                                for label in credential["metadata"]["labels"]:
                                    if (
                                        label.get("name")
                                        == "astra.netapp.io/labels/read-only/credType"
                                    ):
                                        if label.get("value") in [
                                            "AzureContainer",
                                            "service-account",
                                        ]:
                                            credID = credential["id"]
                            if credID:
                                acl.credentials.append(credential["id"])
        elif argv[verbPosition + 1] == "cluster":
            if v3:
                if "--headless" in argv:
                    acl.clouds.append("123")
                else:
                    try:
                        ard.clouds = astraSDK.clouds.getClouds().main()
                        if ard.clouds and ard.clouds.get("items"):
                            for cloud in ard.clouds["items"]:
                                if cloud["cloudType"] not in ["GCP", "Azure", "AWS"]:
                                    acl.clouds.append(cloud["id"])
                        # Add a private cloud if it doesn't already exist
                        if len(acl.clouds) == 0:
                            rc = astraSDK.clouds.manageCloud(quiet=True).main("private", "private")
                            if rc:
                                acl.clouds.append(rc["id"])
                    except SystemExit:
                        pass
                ard.credentials = astraSDK.k8s.getSecrets(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main()
                acl.credentials = ard.buildList("credentials", "metadata.name")
            else:
                ard.clusters = astraSDK.clusters.getClusters().main()
                acl.clusters = ard.buildList(
                    "clusters", "id", fKey="managedState", fVal="unmanaged"
                )
                ard.storageClasses = astraSDK.storageclasses.getStorageClasses().main()
                for a in argv[verbPosition + 2 :]:
                    acl.storageClasses += ard.buildList("storageClasses", "id", "clusterID", a)
        elif argv[verbPosition + 1] == "cloud":
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")

    elif verbs["destroy"] and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "backup" and len(argv) - verbPosition >= 3:
            if v3:
                ard.apps = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("applications")
                acl.apps = ard.buildList("apps", "metadata.name")
                ard.backups = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("backups")
                acl.backups = ard.buildList(
                    "backups",
                    "metadata.name",
                    fKey="spec.applicationRef",
                    fVal=argv[verbPosition + 2],
                )
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
                ard.backups = astraSDK.backups.getBackups().main()
                acl.backups = ard.buildList(
                    "backups", "id", fKey="appID", fVal=argv[verbPosition + 2]
                )
        elif argv[verbPosition + 1] == "cluster" and len(argv) - verbPosition >= 3:
            ard.clusters = astraSDK.clusters.getClusters().main()
            acl.clusters = ard.buildList("clusters", "id", fKey="managedState", fVal="unmanaged")
        elif (argv[verbPosition + 1] == "credential" or argv[verbPosition + 1] == "secret") and len(
            argv
        ) - verbPosition >= 3:
            if v3:
                ard.credentials = astraSDK.k8s.getSecrets(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main()
                acl.credentials = ard.buildList("credentials", "metadata.name")
            else:
                ard.credentials = astraSDK.credentials.getCredentials().main()
                acl.credentials = ard.buildList("credentials", "id")
        elif argv[verbPosition + 1] == "group" and len(argv) - verbPosition >= 3:
            ard.groups = astraSDK.groups.getGroups().main()
            acl.groups = ard.buildList("groups", "id")
        elif (argv[verbPosition + 1] == "hook" or argv[verbPosition + 1] == "exechook") and len(
            argv
        ) - verbPosition >= 3:
            if v3:
                ard.apps = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("applications")
                acl.apps = ard.buildList("apps", "metadata.name")
                ard.hooks = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("exechooks")
                acl.hooks = ard.buildList(
                    "hooks",
                    "metadata.name",
                    fKey="spec.applicationRef",
                    fVal=argv[verbPosition + 2],
                )
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
                ard.hooks = astraSDK.hooks.getHooks().main()
                acl.hooks = ard.buildList("hooks", "id", fKey="appID", fVal=argv[verbPosition + 2])
        elif (
            argv[verbPosition + 1] == "protection" or argv[verbPosition + 1] == "schedule"
        ) and len(argv) - verbPosition >= 3:
            if v3:
                ard.apps = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("applications")
                acl.apps = ard.buildList("apps", "metadata.name")
                ard.protections = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("schedules")
                acl.protections = ard.buildList(
                    "protections",
                    "metadata.name",
                    fKey="spec.applicationRef",
                    fVal=argv[verbPosition + 2],
                )
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
                ard.protections = astraSDK.protections.getProtectionpolicies().main()
                acl.protections = ard.buildList(
                    "protections", "id", fKey="appID", fVal=argv[verbPosition + 2]
                )
        elif argv[verbPosition + 1] == "replication" and len(argv) - verbPosition >= 3:
            ard.replications = astraSDK.replications.getReplicationpolicies().main()
            if not ard.replications:  # Gracefully handle ACS env
                raise SystemExit(
                    "Error: 'replication' commands are currently only supported in ACC."
                )
            acl.replications = ard.buildList("replications", "id")
        elif argv[verbPosition + 1] == "snapshot" and len(argv) - verbPosition >= 3:
            if v3:
                ard.apps = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("applications")
                acl.apps = ard.buildList("apps", "metadata.name")
                ard.snapshots = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("snapshots")
                acl.snapshots = ard.buildList(
                    "snapshots",
                    "metadata.name",
                    fKey="spec.applicationRef",
                    fVal=argv[verbPosition + 2],
                )
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
                ard.snapshots = astraSDK.snapshots.getSnaps().main()
                acl.snapshots = ard.buildList(
                    "snapshots", "id", fKey="appID", fVal=argv[verbPosition + 2]
                )
        elif argv[verbPosition + 1] == "script" and len(argv) - verbPosition >= 3:
            ard.scripts = astraSDK.scripts.getScripts().main()
            acl.scripts = ard.buildList("scripts", "id")
        elif argv[verbPosition + 1] == "user" and len(argv) - verbPosition >= 3:
            ard.users = astraSDK.users.getUsers().main()
            acl.users = ard.buildList("users", "id")

    elif verbs["unmanage"] and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "app" or argv[verbPosition + 1] == "application":
            if v3:
                ard.apps = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("applications")
                acl.apps = ard.buildList("apps", "metadata.name")
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
        elif argv[verbPosition + 1] == "bucket" or argv[verbPosition + 1] == "appVault":
            if v3:
                ard.buckets = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("appvaults")
                acl.buckets = ard.buildList("buckets", "metadata.name")
            else:
                ard.buckets = astraSDK.buckets.getBuckets().main()
                acl.buckets = ard.buildList("buckets", "id")
        elif argv[verbPosition + 1] == "cluster":
            if v3:
                ard.connectors = astraSDK.k8s.getResources(
                    config_context=v3, skip_tls_verify=v3_skip_tls_verify
                ).main("astraconnectors", version="v1", group="astra.netapp.io")
                acl.clusters = ard.buildList("connectors", "spec.astra.clusterId") + ard.buildList(
                    "connectors", "spec.astra.clusterName"
                )
            else:
                ard.clusters = astraSDK.clusters.getClusters().main()
                acl.clusters = ard.buildList("clusters", "id", fKey="managedState", fVal="managed")
        elif argv[verbPosition + 1] == "cloud":
            ard.clouds = astraSDK.clouds.getClouds().main()
            acl.clouds = ard.buildList("clouds", "id")

    elif verbs["update"] and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "bucket" or argv[verbPosition + 1] == "appVault":
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")
            ard.credentials = astraSDK.credentials.getCredentials().main()
            for credential in ard.credentials["items"]:
                if credential["metadata"].get("labels"):
                    credID = None
                    if credential.get("keyType") == "s3":
                        credID = credential["id"]
                    else:
                        for label in credential["metadata"]["labels"]:
                            if label["name"] == "astra.netapp.io/labels/read-only/credType":
                                if label["value"] in ["AzureContainer", "service-account"]:
                                    credID = credential["id"]
                    if credID:
                        acl.credentials.append(credential["id"])
        elif argv[verbPosition + 1] == "cloud":
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")
            ard.clouds = astraSDK.clouds.getClouds().main()
            acl.clouds = ard.buildList("clouds", "id")
            ard.credentials = astraSDK.credentials.getCredentials().main()
            for credential in ard.credentials["items"]:
                if credential["metadata"].get("labels"):
                    credID = None
                    if credential.get("keyType") == "s3":
                        credID = credential["id"]
                    else:
                        for label in credential["metadata"]["labels"]:
                            if label["name"] == "astra.netapp.io/labels/read-only/credType":
                                if label["value"] in ["AzureContainer", "service-account"]:
                                    credID = credential["id"]
                    if credID:
                        acl.credentials.append(credential["id"])
        elif argv[verbPosition + 1] == "cluster":
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")
            ard.clusters = astraSDK.clusters.getClusters().main()
            # If we're updating a default bucket, only allow managed clusters
            if len(set(argv[verbPosition + 2 :]) & set(acl.buckets)) > 0:
                acl.clusters = ard.buildList("clusters", "id", fKey="managedState", fVal="managed")
            else:
                acl.clusters = ard.buildList("clusters", "id")
        elif argv[verbPosition + 1] == "protection":
            ard.protections = astraSDK.protections.getProtectionpolicies().main()
            acl.protections = ard.buildList("protections", "id")
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")
        elif argv[verbPosition + 1] == "replication":
            ard.replications = astraSDK.replications.getReplicationpolicies().main()
            if not ard.replications:  # Gracefully handle ACS env
                raise SystemExit(
                    "Error: 'replication' commands are currently only supported in ACC."
                )
            acl.replications = ard.buildList("replications", "id")
        elif argv[verbPosition + 1] == "script":
            ard.scripts = astraSDK.scripts.getScripts().main()
            acl.scripts = ard.buildList("scripts", "id")


def kube_config(argv, acl, verbPosition, v3Position, global_args):
    """This method completes two key actions:
    A) Generates the argparse choices list (acl) for the possible kubeconfig "contexts"
    B) Transparently modifies argv to enable very simple inputs for the user, but also allowing
       for any amount of customization (any config_file, any context)

    There are 5 possible use-cases which are covered:
    1) User enters plain "--v3"-> use system default config_file and context
    2) Specific context AND kubeconfig specified "--v3 context@kubeconfig_file"-> use specified val
    3) Only kubeconfig specified "-n kubeconfig_file"-> use default context of that config_file
    4) Only context specified "-n context"-> use specified context with default config_file
    5) Incluster config (from within a pod)

    Since we are potentially modifying the length of argv, this function also modifies and returns
    verbPosition.
    """
    desired_context = ""
    v3_arg = argv[v3Position + 1]
    # This is only needed to properly generate help text ("actoolkit --v3 --help")
    if verbPosition is None:
        verbPosition = v3Position + 1

    # First assume it's a regular, non-incluster config (1-4)
    # Handle plain input / no kubeconfig or context specified (1)
    if v3Position + 1 == verbPosition or v3_arg.split("=")[0] in global_args:
        config_file = None

    # Handle user input use cases (2-4)
    else:
        # Popping v3_arg from the list, as it gets re-added in proper format below
        argv.pop(v3Position + 1)
        verbPosition -= 1
        # Handle `context@kubeconfig` use case (2)
        if "@" in v3_arg:
            desired_context, config_file = tuple(v3_arg.split("@"))
            config_file = None if config_file == "None" else config_file
        # Handle use cases 3 and 4, config_file is set to the user's input, which may actually
        # be a kubeconfig (3), but could be a context (4), which will throw an error
        else:
            config_file = v3_arg

    # If this works without an error, then 1, 2, or 3 was entered
    try:
        contexts, current_context = kubernetes.config.kube_config.list_kube_config_contexts(
            config_file=config_file
        )
        if not desired_context:
            desired_context = current_context["name"]

    # If an exception, then either a `context` has been provided (4) or it's incluster (5)
    except kubernetes.config.config_exception.ConfigException:
        # Check to ensure `kubeconfig@context` wasn't accidentally entered
        if "@" in v3_arg:
            sys.stderr.write(
                f"{RED}Invalid kube-config file. No configuration found.\n"
                f"Please ensure {v3_arg} is a valid 'context@kubeconfig' mapping.{ENDC}\n"
            )
            raise SystemExit()
        config_file, desired_context = None, v3_arg
        try:
            contexts, _ = kubernetes.config.kube_config.list_kube_config_contexts(
                config_file=config_file
            )
        # If that fails as a last resort try an incluster config
        except kubernetes.config.config_exception.ConfigException:
            try:
                kubernetes.config.load_incluster_config()
                contexts, desired_context = [{"name": "incluster"}], "incluster"
                config_file = None
            # If this was hit, we do not have a valid kubeconfig file
            except kubernetes.config.config_exception.ConfigException as err:
                sys.stderr.write(f"{RED}{err}{ENDC}\n")
                raise SystemExit()

    # Build the choices list and modify argv
    acl.contexts = [f"{c['name']}@{config_file}" for c in contexts]
    config_context = f"{desired_context}@{config_file}"
    argv.insert(v3Position + 1, config_context)
    verbPosition += 1
    return config_context, verbPosition
