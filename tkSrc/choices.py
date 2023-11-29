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

import astraSDK
import tkSrc


def main(argv, verbs, verbPosition, ard, acl, neptune):
    """This function builds the argparse choices lists. To build these lists, a variety of external
    calls need to be made. The results of these calls are stored in ard (an instantiation of
    AstraResourceDicts) so the same call doesn't have to be made again later. The choices lists are
    stored in acl (an instantiation of ArgparseChoicesLists)"""

    if verbs["deploy"]:
        # This expression translates to "Is there an arg after the verb we found?"
        if len(argv) - verbPosition >= 2:
            if argv[verbPosition + 1] == "chart":
                ard.charts = tkSrc.helpers.updateHelm()
                acl.charts = ard.buildList("charts", "name")
            elif argv[verbPosition + 1] == "acp":
                ard.credentials = astraSDK.k8s.getSecrets().main(namespace="trident")
                acl.credentials = ard.buildList("credentials", "metadata.name")

    elif verbs["clone"] or verbs["restore"]:
        if neptune:
            ard.apps = astraSDK.k8s.getResources().main(
                "applications", version="v1alpha1", group="management.astra.netapp.io"
            )
            acl.apps = ard.buildList("apps", "metadata.name")
            if verbs["restore"]:
                ard.backups = astraSDK.k8s.getResources().main(
                    "backups", version="v1alpha1", group="management.astra.netapp.io"
                )
                ard.snapshots = astraSDK.k8s.getResources().main(
                    "snapshots", version="v1alpha1", group="management.astra.netapp.io"
                )
                acl.dataProtections = ard.buildList("backups", "metadata.name") + ard.buildList(
                    "snapshots", "metadata.name"
                )
            ard.storageClasses = astraSDK.k8s.getStorageClasses().main()
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
        if neptune:
            ard.apps = astraSDK.k8s.getResources().main(
                "applications", version="v1alpha1", group="management.astra.netapp.io"
            )
            acl.apps = ard.buildList("apps", "metadata.name")
            if len(argv) - verbPosition >= 2:
                ard.backups = astraSDK.k8s.getResources().main(
                    "backups", version="v1alpha1", group="management.astra.netapp.io"
                )
                ard.snapshots = astraSDK.k8s.getResources().main(
                    "snapshots", version="v1alpha1", group="management.astra.netapp.io"
                )
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
            or argv[verbPosition + 1] == "hook"
            or argv[verbPosition + 1] == "protectionpolicy"
            or argv[verbPosition + 1] == "protection"
            or argv[verbPosition + 1] == "replication"
            or argv[verbPosition + 1] == "snapshot"
        ):
            if neptune:
                ard.apps = astraSDK.k8s.getResources().main(
                    "applications",
                    version="v1alpha1",
                    group="management.astra.netapp.io",
                )
                acl.apps = ard.buildList("apps", "metadata.name")
            else:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
            if argv[verbPosition + 1] == "backup" or argv[verbPosition + 1] == "snapshot":
                if neptune:
                    ard.buckets = astraSDK.k8s.getResources().main(
                        "appvaults",
                        version="v1alpha1",
                        group="management.astra.netapp.io",
                    )
                    acl.buckets = ard.buildList("buckets", "metadata.name")
                else:
                    ard.buckets = astraSDK.buckets.getBuckets(quiet=True).main()
                    acl.buckets = ard.buildList("buckets", "id")
                # Generate acl.snapshots if an app was provided
                if argv[verbPosition + 1] == "backup":
                    for a in argv[verbPosition + 1 :]:
                        if a in acl.apps:
                            if neptune:
                                ard.snapshots = astraSDK.k8s.getResources().main(
                                    "snapshots",
                                    version="v1alpha1",
                                    group="management.astra.netapp.io",
                                    keyFilter="spec.applicationRef",
                                    valFilter=a,
                                )
                                acl.snapshots = ard.buildList("snapshots", "metadata.name")
                            else:
                                ard.snapshots = astraSDK.snapshots.getSnaps().main(appFilter=a)
                                acl.snapshots = ard.buildList("snapshots", "id")
            if argv[verbPosition + 1] == "hook":
                ard.scripts = astraSDK.scripts.getScripts().main()
                acl.scripts = ard.buildList("scripts", "id")
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
        elif argv[verbPosition + 1] == "user":
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
        if argv[verbPosition + 1] == "app":
            if neptune:
                ard.namespaces = astraSDK.k8s.getNamespaces().main()
                acl.namespaces = ard.buildList("namespaces", "metadata.name")
            else:
                ard.namespaces = astraSDK.namespaces.getNamespaces().main()
                acl.namespaces = ard.buildList("namespaces", "name")
                acl.clusters = ard.buildList("namespaces", "clusterID")
                acl.clusters = list(set(acl.clusters))
        elif argv[verbPosition + 1] == "bucket" or argv[verbPosition + 1] == "appVault":
            if neptune:
                ard.credentials = astraSDK.k8s.getSecrets().main(namespace="neptune-system")
                acl.credentials = ard.buildList("credentials", "metadata.name")
                for c in argv[verbPosition + 1 :]:
                    if c in acl.credentials:
                        for l in ard.buildList("credentials", "data", fKey="metadata.name", fVal=c):
                            for i in l:
                                acl.keys.append(i)
                if not acl.keys:
                    acl.keys = [i for l in ard.buildList("credentials", "data") for i in l]
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
            ard.clusters = astraSDK.clusters.getClusters().main()
            acl.clusters = ard.buildList("clusters", "id", fKey="managedState", fVal="unmanaged")
            ard.storageClasses = astraSDK.storageclasses.getStorageClasses().main()
            for a in argv[verbPosition + 2 :]:
                acl.storageClasses += ard.buildList("storageClasses", "id", "clusterID", a)
        elif argv[verbPosition + 1] == "cloud":
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")

    elif verbs["destroy"] and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "backup" and len(argv) - verbPosition >= 3:
            ard.apps = astraSDK.apps.getApps().main()
            acl.apps = ard.buildList("apps", "id")
            ard.backups = astraSDK.backups.getBackups().main()
            acl.backups = ard.buildList("backups", "id", fKey="appID", fVal=argv[verbPosition + 2])
        elif argv[verbPosition + 1] == "credential" and len(argv) - verbPosition >= 3:
            ard.credentials = astraSDK.credentials.getCredentials().main()
            acl.credentials = ard.buildList("credentials", "id")
        elif argv[verbPosition + 1] == "hook" and len(argv) - verbPosition >= 3:
            ard.apps = astraSDK.apps.getApps().main()
            acl.apps = ard.buildList("apps", "id")
            ard.hooks = astraSDK.hooks.getHooks().main()
            acl.hooks = ard.buildList("hooks", "id", fKey="appID", fVal=argv[verbPosition + 2])
        elif argv[verbPosition + 1] == "protection" and len(argv) - verbPosition >= 3:
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
        if argv[verbPosition + 1] == "app":
            ard.apps = astraSDK.apps.getApps().main()
            acl.apps = ard.buildList("apps", "id")
        elif argv[verbPosition + 1] == "bucket":
            ard.buckets = astraSDK.buckets.getBuckets().main()
            acl.buckets = ard.buildList("buckets", "id")
        elif argv[verbPosition + 1] == "cluster":
            ard.clusters = astraSDK.clusters.getClusters().main()
            acl.clusters = ard.buildList("clusters", "id", fKey="managedState", fVal="managed")
        elif argv[verbPosition + 1] == "cloud":
            ard.clouds = astraSDK.clouds.getClouds().main()
            acl.clouds = ard.buildList("clouds", "id")

    elif verbs["update"] and len(argv) - verbPosition >= 2:
        if argv[verbPosition + 1] == "bucket":
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
