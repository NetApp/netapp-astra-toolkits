#!/usr/bin/env python3
"""
   Copyright 2022 NetApp, Inc

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

import argparse


class toolkit_parser:
    """Creates and returns an argparse parser for use in toolkit.py"""

    def __init__(self, plaidMode=False):
        """Creates the parser object and global arguments"""
        self.parser = argparse.ArgumentParser(allow_abbrev=True)
        self.parser.add_argument(
            "-v",
            "--verbose",
            default=False,
            action="store_true",
            help="print verbose/verbose output",
        )
        self.parser.add_argument(
            "-o",
            "--output",
            default="table",
            choices=["json", "yaml", "table"],
            help="command output format",
        )
        self.parser.add_argument(
            "-q", "--quiet", default=False, action="store_true", help="supress output"
        )
        self.parser.add_argument(
            "-f",
            "--fast",
            default=False,
            action="store_true",
            help="prioritize speed over validation (using this will not validate arguments, which "
            + "may have unintended consequences)",
        )
        self.plaidMode = plaidMode

    def top_level_commands(self):
        """Creates the top level arguments, such as list, create, destroy, etc.
        Be sure to keep these in sync with verbs{} in the calling function."""
        self.subparsers = self.parser.add_subparsers(
            dest="subcommand", required=True, help="subcommand help"
        )
        self.parserDeploy = self.subparsers.add_parser(
            "deploy",
            help="Deploy a helm chart",
        )
        self.parserClone = self.subparsers.add_parser(
            "clone",
            help="Clone an app",
        )
        self.parserRestore = self.subparsers.add_parser(
            "restore",
            help="Restore an app from a backup or snapshot",
        )
        self.parserList = self.subparsers.add_parser(
            "list",
            aliases=["get"],
            help="List all items in a class",
        )
        self.parserCreate = self.subparsers.add_parser(
            "create",
            help="Create an object",
        )
        self.parserManage = self.subparsers.add_parser(
            "manage",
            aliases=["define"],
            help="Manage an object",
        )
        self.parserDestroy = self.subparsers.add_parser(
            "destroy",
            help="Destroy an object",
        )
        self.parserUnmanage = self.subparsers.add_parser(
            "unmanage",
            help="Unmanage an object",
        )
        self.parserUpdate = self.subparsers.add_parser(
            "update",
            help="Update an object",
        )

    def sub_commands(self):
        """'list', 'create', 'manage', 'destroy', 'unmanage', and 'update' all have
        subcommands, for example, 'list apps' or 'manage cluster'."""
        self.subparserList = self.parserList.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserCreate = self.parserCreate.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserManage = self.parserManage.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserDestroy = self.parserDestroy.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserUnmanage = self.parserUnmanage.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserUpdate = self.parserUpdate.add_subparsers(
            title="objectType", dest="objectType", required=True
        )

    def sub_list_commands(self):
        """list 'X'"""
        self.subparserListApiResources = self.subparserList.add_parser(
            "apiresources",
            help="list api resources",
        )
        self.subparserListApps = self.subparserList.add_parser(
            "apps",
            help="list apps",
        )
        self.subparserListAssets = self.subparserList.add_parser(
            "assets",
            help="list app assets",
        )
        self.subparserListBackups = self.subparserList.add_parser(
            "backups",
            help="list backups",
        )
        self.subparserListBuckets = self.subparserList.add_parser(
            "buckets",
            help="list buckets",
        )
        self.subparserListClouds = self.subparserList.add_parser(
            "clouds",
            help="list clouds",
        )
        self.subparserListClusters = self.subparserList.add_parser(
            "clusters",
            help="list clusters",
        )
        self.subparserListCredentials = self.subparserList.add_parser(
            "credentials",
            help="list credentials",
        )
        self.subparserListHooks = self.subparserList.add_parser(
            "hooks", help="list hooks (executionHooks)"
        )
        self.subparserListNamespaces = self.subparserList.add_parser(
            "namespaces",
            help="list namespaces",
        )
        self.subparserListNotifications = self.subparserList.add_parser(
            "notifications",
            help="list notifications",
        )
        self.subparserListProtections = self.subparserList.add_parser(
            "protections",
            help="list protection policies",
        )
        self.subparserListReplications = self.subparserList.add_parser(
            "replications",
            help="list replication policies",
        )
        self.subparserListRolebindings = self.subparserList.add_parser(
            "rolebindings",
            help="list role bindings",
        )
        self.subparserListScripts = self.subparserList.add_parser(
            "scripts",
            help="list scripts (hookSources)",
        )
        self.subparserListSnapshots = self.subparserList.add_parser(
            "snapshots",
            help="list snapshots",
        )
        self.subparserListStorageClasses = self.subparserList.add_parser(
            "storageclasses",
            help="list storageclasses",
        )
        self.subparserListUsers = self.subparserList.add_parser(
            "users",
            help="list users",
        )

    def sub_create_commands(self):
        """create 'X'"""
        self.subparserCreateBackup = self.subparserCreate.add_parser(
            "backup",
            help="create backup",
        )
        self.subparserCreateCluster = self.subparserCreate.add_parser(
            "cluster", help="create cluster (upload a K8s cluster kubeconfig to then manage)"
        )
        self.subparserCreateHook = self.subparserCreate.add_parser(
            "hook",
            help="create hook (executionHook)",
        )
        self.subparserCreateProtection = self.subparserCreate.add_parser(
            "protection",
            aliases=["protectionpolicy"],
            help="create protection policy",
        )
        self.subparserCreateReplication = self.subparserCreate.add_parser(
            "replication",
            help="create replication policy",
        )
        self.subparserCreateScript = self.subparserCreate.add_parser(
            "script",
            help="create script (hookSource)",
        )
        self.subparserCreateSnapshot = self.subparserCreate.add_parser(
            "snapshot",
            help="create snapshot",
        )
        self.subparserCreateUser = self.subparserCreate.add_parser(
            "user",
            help="create a user",
        )

    def sub_manage_commands(self):
        """manage 'X'"""
        self.subparserManageApp = self.subparserManage.add_parser(
            "app",
            help="manage app",
        )
        self.subparserManageBucket = self.subparserManage.add_parser(
            "bucket",
            help="manage bucket",
        )
        self.subparserManageCluster = self.subparserManage.add_parser(
            "cluster",
            help="manage cluster",
        )
        self.subparserManageCloud = self.subparserManage.add_parser(
            "cloud",
            help="manage cloud",
        )

    def sub_destroy_commands(self):
        """destroy 'X'"""
        self.subparserDestroyBackup = self.subparserDestroy.add_parser(
            "backup",
            help="destroy backup",
        )
        self.subparserDestroyCredential = self.subparserDestroy.add_parser(
            "credential",
            help="destroy credential",
        )
        self.subparserDestroyHook = self.subparserDestroy.add_parser(
            "hook",
            help="destroy hook (executionHook)",
        )
        self.subparserDestroyProtection = self.subparserDestroy.add_parser(
            "protection",
            help="destroy protection policy",
        )
        self.subparserDestroyReplication = self.subparserDestroy.add_parser(
            "replication",
            help="destroy replication policy",
        )
        self.subparserDestroyScript = self.subparserDestroy.add_parser(
            "script",
            help="destroy script (hookSource)",
        )
        self.subparserDestroySnapshot = self.subparserDestroy.add_parser(
            "snapshot",
            help="destroy snapshot",
        )
        self.subparserDestroyUser = self.subparserDestroy.add_parser(
            "user",
            help="destroy user",
        )

    def sub_unmanage_commands(self):
        """unmanage 'X'"""
        self.subparserUnmanageApp = self.subparserUnmanage.add_parser(
            "app",
            help="unmanage app",
        )
        self.subparserUnmanageBucket = self.subparserUnmanage.add_parser(
            "bucket",
            help="unmanage bucket",
        )
        self.subparserUnmanageCluster = self.subparserUnmanage.add_parser(
            "cluster",
            help="unmanage cluster",
        )
        self.subparserUnmanageCloud = self.subparserUnmanage.add_parser(
            "cloud",
            help="unmanage cloud",
        )

    def sub_update_commands(self):
        """update 'X'"""
        self.subparserUpdateReplication = self.subparserUpdate.add_parser(
            "replication",
            help="update replication",
        )

    def deploy_args(self, chartsList):
        """deploy args and flags"""
        self.parserDeploy.add_argument(
            "app",
            help="name of app",
        )
        self.parserDeploy.add_argument(
            "chart",
            choices=(None if self.plaidMode else chartsList),
            help="chart to deploy",
        )
        self.parserDeploy.add_argument(
            "-n",
            "--namespace",
            required=True,
            help="Namespace to deploy into (must not already exist)",
        )
        self.parserDeploy.add_argument(
            "-f",
            "--values",
            required=False,
            action="append",
            nargs="*",
            help="Specify Helm values in a YAML file",
        )
        self.parserDeploy.add_argument(
            "--set",
            required=False,
            action="append",
            nargs="*",
            help="Individual helm chart parameters",
        )

    def clone_args(self, appList, backupList, destclusterList, snapshotList):
        """clone args and flags"""
        self.parserClone.add_argument(
            "-b",
            "--background",
            default=False,
            action="store_true",
            help="Run clone operation in the background",
        )
        self.parserClone.add_argument(
            "--cloneAppName",
            required=False,
            default=None,
            help="Clone app name",
        )
        self.parserClone.add_argument(
            "--clusterID",
            choices=(None if self.plaidMode else destclusterList),
            required=False,
            default=None,
            help="Cluster to clone into (can be same as source)",
        )
        nsGroup = self.parserClone.add_mutually_exclusive_group()
        nsGroup.add_argument(
            "--cloneNamespace",
            required=False,
            default=None,
            help="For single-namespace apps, specify the clone namespace name (if not"
            + " specified cloneAppName is used)",
        )
        nsGroup.add_argument(
            "--multiNsMapping",
            required=False,
            default=None,
            action="append",
            nargs="*",
            help="For multi-namespace apps, specify matching number of sourcens1=destns1 mappings",
        )
        sourceGroup = self.parserClone.add_mutually_exclusive_group(required=True)
        sourceGroup.add_argument(
            "--backupID",
            choices=(None if self.plaidMode else backupList),
            required=False,
            default=None,
            help="Source backup to clone from",
        )
        sourceGroup.add_argument(
            "--snapshotID",
            choices=(None if self.plaidMode else snapshotList),
            required=False,
            default=None,
            help="Source snapshot to clone from",
        )
        sourceGroup.add_argument(
            "--sourceAppID",
            choices=(None if self.plaidMode else appList),
            required=False,
            default=None,
            help="Source app to clone",
        )
        self.parserClone.add_argument(
            "-t",
            "--pollTimer",
            type=int,
            default=5,
            help="The frequency (seconds) to poll the operation status (default: %(default)s)",
        )

    def restore_args(self, appList, backupList, snapshotList):
        """restore args and flags"""
        self.parserRestore.add_argument(
            "-b",
            "--background",
            default=False,
            action="store_true",
            help="Run restore operation in the background",
        )
        self.parserRestore.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID to restore",
        )
        group = self.parserRestore.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--backupID",
            choices=(None if self.plaidMode else backupList),
            required=False,
            default=None,
            help="Source backup to restore from",
        )
        group.add_argument(
            "--snapshotID",
            choices=(None if self.plaidMode else snapshotList),
            required=False,
            default=None,
            help="Source snapshot to restore from",
        )
        self.parserRestore.add_argument(
            "-t",
            "--pollTimer",
            type=int,
            default=5,
            help="The frequency (seconds) to poll the operation status (default: %(default)s)",
        )

    def list_apiresources_args(self):
        """list api resources args and flags"""
        self.subparserListApiResources.add_argument(
            "-c", "--cluster", default=None, help="Only show api resources from this cluster"
        )

    def list_apps_args(self):
        """list apps args and flags"""
        self.subparserListApps.add_argument(
            "-n", "--namespace", default=None, help="Only show apps from this namespace"
        )
        self.subparserListApps.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter app names by this value to minimize output (partial match)",
        )
        self.subparserListApps.add_argument(
            "-c", "--cluster", default=None, help="Only show apps from this cluster"
        )

    def list_assets_args(self, appList):
        """list assets args and flags"""
        self.subparserListAssets.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="The appID from which to display the assets",
        )

    def list_backups_args(self):
        """list backups args and flags"""
        self.subparserListBackups.add_argument(
            "-a", "--app", default=None, help="Only show backups from this app"
        )

    def list_buckets_args(self):
        """list buckets args and flags"""
        self.subparserListBuckets.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter app names by this value to minimize output (partial match)",
        )
        self.subparserListBuckets.add_argument(
            "-p",
            "--provider",
            default=None,
            help="Only show buckets of a single provider",
        )

    def list_clouds_args(self):
        """list clouds args and flags"""
        self.subparserListClouds.add_argument(
            "-t",
            "--cloudType",
            default=None,
            choices=["GCP", "Azure", "AWS", "Private"],
            help="Only show clouds of a single type",
        )

    def list_clusters_args(self):
        """list clusters args and flags"""
        self.subparserListClusters.add_argument(
            "-m",
            "--hideManaged",
            default=False,
            action="store_true",
            help="Hide managed clusters",
        )
        self.subparserListClusters.add_argument(
            "-u",
            "--hideUnmanaged",
            default=False,
            action="store_true",
            help="Hide unmanaged clusters",
        )
        self.subparserListClusters.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter cluster names by this value to minimize output (partial match)",
        )

    def list_credentials_args(self):
        """list credentials args and flags"""
        self.subparserListCredentials.add_argument(
            "-k",
            "--kubeconfigOnly",
            default=False,
            action="store_true",
            help="Only show kubeconfig credentials",
        )

    def list_hooks_args(self):
        """list hooks args and flags"""
        self.subparserListHooks.add_argument(
            "-a", "--app", default=None, help="Only show execution hooks from this app"
        )

    def list_namespaces_args(self):
        """list namespaces args and flags"""
        self.subparserListNamespaces.add_argument(
            "-c", "--clusterID", default=None, help="Only show namespaces from this clusterID"
        )
        self.subparserListNamespaces.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter namespaces by this value to minimize output (partial match)",
        )
        self.subparserListNamespaces.add_argument(
            "-r",
            "--showRemoved",
            default=False,
            action="store_true",
            help="Show namespaces in a 'removed' state",
        )
        self.subparserListNamespaces.add_argument(
            "-u",
            "--unassociated",
            default=False,
            action="store_true",
            help="Only show namespaces which do not have any associatedApps",
        )
        self.subparserListNamespaces.add_argument(
            "-m",
            "--minutes",
            default=False,
            type=int,
            help="Only show namespaces created within the last X minutes",
        )

    def list_notifications_args(self):
        """list notifications args and flags"""
        self.subparserListNotifications.add_argument(
            "-l",
            "--limit",
            default=None,
            type=int,
            help="The number of notifications to display",
        )
        self.subparserListNotifications.add_argument(
            "-o",
            "--offset",
            default=None,
            type=int,
            help="The number of notifications to skip (used in conjunction with limit)",
        )
        self.subparserListNotifications.add_argument(
            "-m",
            "--minutes",
            default=False,
            type=int,
            help="Only show notifications created within the last X minutes",
        )
        self.subparserListNotifications.add_argument(
            "-s",
            "--severity",
            default=None,
            type=str.lower,
            choices=["informational", "warning", "critical"],
            help="Filter by the severity type",
        )

    def list_protections_args(self):
        """list protection policies args and flags"""
        self.subparserListProtections.add_argument(
            "-a", "--app", default=None, help="Only show protection policies from this app"
        )

    def list_replications_args(self):
        """list replication policies args and flags"""
        self.subparserListReplications.add_argument(
            "-a", "--app", default=None, help="Only show replication policies from this app"
        )

    def list_rolebindings_args(self):
        """list rolebindings args and flags"""
        self.subparserListRolebindings.add_argument(
            "-i",
            "--idFilter",
            default=None,
            help="Only show role bindings matching the provided user or group ID",
        )

    def list_scripts_args(self):
        """list scripts args and flags"""
        self.subparserListScripts.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter scripts by this value to minimize output (partial match)",
        )
        self.subparserListScripts.add_argument(
            "-s",
            "--getScriptSource",
            default=False,
            action="store_true",
            help="View the script source code",
        )

    def list_snapshots_args(self):
        """list snapshots args and flags"""
        self.subparserListSnapshots.add_argument(
            "-a", "--app", default=None, help="Only show snapshots from this app"
        )

    def list_storageclasses_args(self):
        """list storageclasses args and flags"""
        self.subparserListStorageClasses.add_argument(
            "-t",
            "--cloudType",
            default=None,
            choices=["GCP", "Azure", "AWS", "Private"],
            help="Only show storageclasses of a single cloud type",
        )

    def list_users_args(self):
        """list users args and flags"""
        self.subparserListUsers.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter users by this value to minimize output (partial match)",
        )

    def create_backup_args(self, appList, bucketList, snapshotList):
        """create backups args and flags"""
        self.subparserCreateBackup.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID to backup",
        )
        self.subparserCreateBackup.add_argument(
            "name",
            help="Name of backup to be taken",
        )
        self.subparserCreateBackup.add_argument(
            "-u",
            "--bucketID",
            default=None,
            choices=(None if self.plaidMode else bucketList),
            help="Optionally specify which bucket to store the backup",
        )
        self.subparserCreateBackup.add_argument(
            "-s",
            "--snapshotID",
            default=None,
            choices=(None if self.plaidMode else snapshotList),
            help="Optionally specify an existing snapshot as the source of the backup",
        )
        self.subparserCreateBackup.add_argument(
            "-b",
            "--background",
            default=False,
            action="store_true",
            help="Run backup operation in the background",
        )
        self.subparserCreateBackup.add_argument(
            "-t",
            "--pollTimer",
            type=int,
            default=5,
            help="The frequency (seconds) to poll the operation status (default: %(default)s)",
        )

    def create_cluster_args(self, cloudList):
        """create cluster args and flags"""
        self.subparserCreateCluster.add_argument(
            "filePath",
            help="the local filesystem path to the cluster kubeconfig",
        )
        self.subparserCreateCluster.add_argument(
            "-c",
            "--cloudID",
            choices=(None if self.plaidMode else cloudList),
            default=(cloudList[0] if len(cloudList) == 1 else None),
            required=(False if len(cloudList) == 1 else True),
            help="The cloudID to add the cluster to (only required if # of clouds > 1)",
        )

    def create_hook_args(self, appList, scriptList):
        """create hooks args and flags"""
        self.subparserCreateHook.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID to create an execution hook for",
        )
        self.subparserCreateHook.add_argument(
            "name",
            help="Name of the execution hook to be created",
        )
        self.subparserCreateHook.add_argument(
            "scriptID",
            choices=(None if self.plaidMode else scriptList),
            help="scriptID to use for the execution hook",
        )
        self.subparserCreateHook.add_argument(
            "-o",
            "--operation",
            choices=["pre-snapshot", "post-snapshot", "pre-backup", "post-backup", "post-restore"],
            required=True,
            type=str.lower,
            help="The operation type for the execution hook",
        )
        self.subparserCreateHook.add_argument(
            "-a",
            "--hookArguments",
            required=False,
            default=None,
            action="append",
            nargs="*",
            help="The (optional) arguments for the execution hook script",
        )
        filterGroup = self.subparserCreateHook.add_argument_group(
            "filterGroup",
            "optional logical AND regex filters to minimize containers where the hook will execute",
        )
        filterGroup.add_argument(
            "-i",
            "--containerImage",
            required=False,
            default=[],
            action="append",
            nargs="*",
            help="regex filter for container images",
        )
        filterGroup.add_argument(
            "-n",
            "--namespace",
            required=False,
            default=[],
            action="append",
            nargs="*",
            help="regex filter for namespaces (useful for multi-namespace apps)",
        )
        filterGroup.add_argument(
            "-p",
            "--podName",
            required=False,
            default=[],
            action="append",
            nargs="*",
            help="regex filter for pod names",
        )
        filterGroup.add_argument(
            "-l",
            "--label",
            required=False,
            default=[],
            action="append",
            nargs="*",
            help="regex filter for Kubernetes labels",
        )
        filterGroup.add_argument(
            "-c",
            "--containerName",
            required=False,
            default=[],
            action="append",
            nargs="*",
            help="regex filter for container names",
        )

    def create_protection_args(self, appList):
        """create protectionpolicy args and flags"""
        self.subparserCreateProtection.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of the application to create protection schedule for",
        )
        self.subparserCreateProtection.add_argument(
            "-g",
            "--granularity",
            required=True,
            choices=["hourly", "daily", "weekly", "monthly"],
            help="Must choose one of the four options for the schedule",
        )
        self.subparserCreateProtection.add_argument(
            "-b",
            "--backupRetention",
            type=int,
            required=True,
            choices=range(60),
            help="Number of backups to retain",
        )
        self.subparserCreateProtection.add_argument(
            "-s",
            "--snapshotRetention",
            type=int,
            required=True,
            choices=range(60),
            help="Number of snapshots to retain",
        )
        self.subparserCreateProtection.add_argument(
            "-M", "--dayOfMonth", type=int, choices=range(1, 32), help="Day of the month"
        )
        self.subparserCreateProtection.add_argument(
            "-W",
            "--dayOfWeek",
            type=int,
            choices=range(7),
            help="0 = Sunday ... 6 = Saturday",
        )
        self.subparserCreateProtection.add_argument(
            "-H", "--hour", type=int, choices=range(24), help="Hour in military time"
        )
        self.subparserCreateProtection.add_argument(
            "-m", "--minute", default=0, type=int, choices=range(60), help="Minute"
        )

    def create_replication_args(self, appList, destclusterList, storageClassList):
        """create replication policy args and flags"""
        self.subparserCreateReplication.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of the application to create the replication policy for",
        )
        self.subparserCreateReplication.add_argument(
            "-c",
            "--destClusterID",
            choices=(None if self.plaidMode else destclusterList),
            help="the destination cluster ID to replicate to",
            required=True,
        )
        self.subparserCreateReplication.add_argument(
            "-n",
            "--destNamespace",
            help="the namespace to create resources on the destination cluster",
            required=True,
        )
        self.subparserCreateReplication.add_argument(
            "-s",
            "--destStorageClass",
            choices=(None if self.plaidMode else storageClassList),
            default=None,
            help="the destination storage class to use for volume creation",
        )
        self.subparserCreateReplication.add_argument(
            "-f",
            "--replicationFrequency",
            choices=[
                "5m",
                "10m",
                "15m",
                "20m",
                "30m",
                "1h",
                "2h",
                "3h",
                "4h",
                "6h",
                "8h",
                "12h",
                "24h",
            ],
            help="the frequency that a snapshot is taken and replicated",
            required=True,
        )
        self.subparserCreateReplication.add_argument(
            "-o",
            "--offset",
            default="00:00",
            help="the amount of time to offset the replication snapshot as to not interfere with "
            + "other operations, in 'hh:mm' or 'mm' format",
        )

    def create_script_args(self):
        """create script args and flags"""
        self.subparserCreateScript.add_argument(
            "name",
            help="Name of the script",
        )
        self.subparserCreateScript.add_argument(
            "filePath",
            help="the local filesystem path to the script",
        )
        self.subparserCreateScript.add_argument(
            "-d",
            "--description",
            default=None,
            help="The optional description of the script",
        )

    def create_snapshot_args(self, appList):
        """create snapshot args and flags"""
        self.subparserCreateSnapshot.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID to snapshot",
        )
        self.subparserCreateSnapshot.add_argument(
            "name",
            help="Name of snapshot to be taken",
        )
        self.subparserCreateSnapshot.add_argument(
            "-b",
            "--background",
            default=False,
            action="store_true",
            help="Run snapshot operation in the background",
        )
        self.subparserCreateSnapshot.add_argument(
            "-t",
            "--pollTimer",
            type=int,
            default=5,
            help="The frequency (seconds) to poll the operation status (default: %(default)s)",
        )

    def create_user_args(self, labelList, namespaceList):
        """create user args and flags"""
        self.subparserCreateUser.add_argument("email", help="The email of the user to add")
        self.subparserCreateUser.add_argument(
            "role", choices=["viewer", "member", "admin", "owner"], help="The user's role"
        )
        self.subparserCreateUser.add_argument(
            "-p",
            "--tempPassword",
            default=None,
            help="The temporary password for the user (ACC-only)",
        )
        self.subparserCreateUser.add_argument(
            "-f",
            "--firstName",
            default=None,
            help="The user's first name",
        )
        self.subparserCreateUser.add_argument(
            "-l", "--lastName", default=None, help="The user's last name"
        )
        self.subparserCreateUser.add_argument(
            "-a",
            "--labelConstraint",
            default=None,
            choices=(None if self.plaidMode else labelList),
            nargs="*",
            action="append",
            help="Restrict user role to label constraints",
        )
        self.subparserCreateUser.add_argument(
            "-n",
            "--namespaceConstraint",
            default=None,
            choices=(None if self.plaidMode else namespaceList),
            nargs="*",
            action="append",
            help="Restrict user role to namespace constraints",
        )

    def manage_app_args(self, clusterList, namespaceList):
        """manage app args and flags"""
        self.subparserManageApp.add_argument(
            "appName", help="The logical name of the newly defined app"
        )
        self.subparserManageApp.add_argument(
            "namespace",
            choices=(None if self.plaidMode else namespaceList),
            help="The namespace to move from undefined (aka unmanaged) to defined (aka managed)",
        )
        self.subparserManageApp.add_argument(
            "clusterID",
            choices=(None if self.plaidMode else clusterList),
            help="The clusterID hosting the newly defined app",
        )
        self.subparserManageApp.add_argument(
            "-l",
            "--labelSelectors",
            required=False,
            default=None,
            help="Optional label selectors to filter resources to be included or excluded from "
            + "the application definition (within the primary 'namespace' argument)",
        )
        self.subparserManageApp.add_argument(
            "-a",
            "--additionalNamespace",
            required=False,
            default=None,
            nargs="*",
            action="append",
            help="Any number of additional namespaces (and optional labelSelectors), one set per"
            + " argument (-a namespace2 -a namespace3 app=appname)",
        )
        self.subparserManageApp.add_argument(
            "-c",
            "--clusterScopedResource",
            required=False,
            default=None,
            nargs="*",
            action="append",
            help="Any number of clusterScopedResources (and optional labelSelectors), one set per"
            + " argument (-a csr-kind1 -a csr-kind2 app=appname)",
        )

    def manage_bucket_args(self, credentialList):
        """manage bucket args and flags"""
        self.subparserManageBucket.add_argument(
            "provider",
            choices=["aws", "azure", "gcp", "generic-s3", "ontap-s3", "storagegrid-s3"],
            help="The infrastructure provider of the storage bucket",
        )
        self.subparserManageBucket.add_argument(
            "bucketName",
            help="The existing bucket name",
        )
        credGroup = self.subparserManageBucket.add_argument_group(
            "credentialGroup",
            "Either an (existing credentialID) OR (accessKey AND accessSecret)",
        )
        credGroup.add_argument(
            "-c",
            "--credentialID",
            choices=(None if self.plaidMode else credentialList),
            help="The ID of the credentials used to access the bucket",
            default=None,
        )
        credGroup.add_argument(
            "--accessKey",
            help="The access key of the bucket",
            default=None,
        )
        credGroup.add_argument(
            "--accessSecret",
            help="The access secret of the bucket",
            default=None,
        )
        self.subparserManageBucket.add_argument(
            "-u",
            "--serverURL",
            help="The URL to the base path of the bucket "
            + "(only needed for 'aws', 'generic-s3', 'ontap-s3' 'storagegrid-s3')",
            default=None,
        )
        self.subparserManageBucket.add_argument(
            "-a",
            "--storageAccount",
            help="The  Azure storage account name (only needed for 'Azure')",
            default=None,
        )

    def manage_cluster_args(self, clusterList, storageClassList):
        """manage cluster args and flags"""
        self.subparserManageCluster.add_argument(
            "clusterID",
            choices=(None if self.plaidMode else clusterList),
            help="clusterID of the cluster to manage",
        )
        self.subparserManageCluster.add_argument(
            "-s",
            "--defaultStorageClassID",
            choices=(None if self.plaidMode else storageClassList),
            default=None,
            help="Optionally modify the default storage class",
        )

    def manage_cloud_args(self, bucketList):
        """manage cloud args and flags"""
        self.subparserManageCloud.add_argument(
            "cloudType",
            choices=["AWS", "Azure", "GCP", "private"],
            help="the type of cloud to add",
        )
        self.subparserManageCloud.add_argument(
            "cloudName",
            help="a friendly name for the cloud",
        )
        self.subparserManageCloud.add_argument(
            "-c",
            "--credentialPath",
            default=None,
            help="the local filesystem path to the cloud credential (required for all but "
            + "'private' clouds)",
        )
        self.subparserManageCloud.add_argument(
            "-b",
            "--defaultBucketID",
            choices=(None if self.plaidMode else bucketList),
            default=None,
            help="optionally specify the default bucketID for backups",
        )

    def destroy_backup_args(self, appList, backupList):
        """destroy backup args and flags"""
        self.subparserDestroyBackup.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of app to destroy backups from",
        )
        self.subparserDestroyBackup.add_argument(
            "backupID",
            choices=(None if self.plaidMode else backupList),
            help="backupID to destroy",
        )

    def destroy_credential_args(self, credentialList):
        """destroy credential args and flags"""
        self.subparserDestroyCredential.add_argument(
            "credentialID",
            choices=(None if self.plaidMode else credentialList),
            help="credentialID to destroy",
        )

    def destroy_hook_args(self, appList, hookList):
        """destroy hook args and flags"""
        self.subparserDestroyHook.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of app to destroy hooks from",
        )
        self.subparserDestroyHook.add_argument(
            "hookID",
            choices=(None if self.plaidMode else hookList),
            help="hookID to destroy",
        )

    def destroy_protection_args(self, appList, protectionList):
        """destroy protection args and flags"""
        self.subparserDestroyProtection.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of app to destroy protection policy from",
        )
        self.subparserDestroyProtection.add_argument(
            "protectionID",
            choices=(None if self.plaidMode else protectionList),
            help="protectionID to destroy",
        )

    def destroy_replication_args(self, replicationList):
        """destroy replication args and flags"""
        self.subparserDestroyReplication.add_argument(
            "replicationID",
            choices=(None if self.plaidMode else replicationList),
            help="replicationID to destroy",
        )

    def destroy_script_args(self, scriptList):
        """destroy script args and flags"""
        self.subparserDestroyScript.add_argument(
            "scriptID",
            choices=(None if self.plaidMode else scriptList),
            help="scriptID of script to destroy",
        )

    def destroy_snapshot_args(self, appList, snapshotList):
        """destroy snapshot args and flags"""
        self.subparserDestroySnapshot.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of app to destroy snapshot from",
        )
        self.subparserDestroySnapshot.add_argument(
            "snapshotID",
            choices=(None if self.plaidMode else snapshotList),
            help="snapshotID to destroy",
        )

    def destroy_user_args(self, userList):
        """destroy user args and flags"""
        self.subparserDestroyUser.add_argument(
            "userID",
            choices=(None if self.plaidMode else userList),
            help="userID to destroy",
        )

    def unmanage_app_args(self, appList):
        """unmanage app args and flags"""
        self.subparserUnmanageApp.add_argument(
            "appID",
            choices=(None if self.plaidMode else appList),
            help="appID of app to move from managed to unmanaged",
        )

    def unmanage_bucket_args(self, bucketList):
        """unmanage bucket args and flags"""
        self.subparserUnmanageBucket.add_argument(
            "bucketID",
            choices=(None if self.plaidMode else bucketList),
            help="bucketID of bucket to unmanage",
        )

    def unmanage_cluster_args(self, clusterList):
        """unmanage cluster args and flags"""
        self.subparserUnmanageCluster.add_argument(
            "clusterID",
            choices=(None if self.plaidMode else clusterList),
            help="clusterID of the cluster to unmanage",
        )

    def unmanage_cloud_args(self, cloudList):
        """unmanage cloud args and flags"""
        self.subparserUnmanageCloud.add_argument(
            "cloudID",
            choices=(None if self.plaidMode else cloudList),
            help="cloudID of the cloud to unmanage",
        )

    def update_replication_args(self, replicationList):
        """update replication args and flags"""
        self.subparserUpdateReplication.add_argument(
            "replicationID",
            choices=(None if self.plaidMode else replicationList),
            help="replicationID to update",
        )
        self.subparserUpdateReplication.add_argument(
            "operation",
            choices=["failover", "reverse", "resync"],
            help="whether to failover, reverse, or resync the replication policy",
        )
        self.subparserUpdateReplication.add_argument(
            "--dataSource",
            "-s",
            default=None,
            help="resync operation: the new source replication data (either appID or clusterID)",
        )

    def main(
        self,
        appList,
        backupList,
        bucketList,
        chartsList,
        cloudList,
        clusterList,
        credentialList,
        destclusterList,
        hookList,
        labelList,
        namespaceList,
        protectionList,
        replicationList,
        scriptList,
        snapshotList,
        storageClassList,
        userList,
    ):

        # Create the top-level commands like: deploy, clone, list, manage, etc.
        self.top_level_commands()

        # *Some* top-level commands have sub-commands like: list apps vs list buckets
        self.sub_commands()

        # Of those top-level commands with sub-commands, create those sub-command parsers
        self.sub_list_commands()
        self.sub_create_commands()
        self.sub_manage_commands()
        self.sub_destroy_commands()
        self.sub_unmanage_commands()
        self.sub_update_commands()

        # Create arguments for all commands
        self.deploy_args(chartsList)
        self.clone_args(appList, backupList, destclusterList, snapshotList)
        self.restore_args(appList, backupList, snapshotList)

        self.list_apiresources_args()
        self.list_apps_args()
        self.list_assets_args(appList)
        self.list_backups_args()
        self.list_buckets_args()
        self.list_clouds_args()
        self.list_clusters_args()
        self.list_credentials_args()
        self.list_hooks_args()
        self.list_namespaces_args()
        self.list_notifications_args()
        self.list_protections_args()
        self.list_replications_args()
        self.list_rolebindings_args()
        self.list_scripts_args()
        self.list_snapshots_args()
        self.list_storageclasses_args()
        self.list_users_args()

        self.create_backup_args(appList, bucketList, snapshotList)
        self.create_cluster_args(cloudList)
        self.create_hook_args(appList, scriptList)
        self.create_protection_args(appList)
        self.create_replication_args(appList, destclusterList, storageClassList)
        self.create_script_args()
        self.create_snapshot_args(appList)
        self.create_user_args(labelList, namespaceList)

        self.manage_app_args(clusterList, namespaceList)
        self.manage_bucket_args(credentialList)
        self.manage_cluster_args(clusterList, storageClassList)
        self.manage_cloud_args(bucketList)

        self.destroy_backup_args(appList, backupList)
        self.destroy_credential_args(credentialList)
        self.destroy_hook_args(appList, hookList)
        self.destroy_protection_args(appList, protectionList)
        self.destroy_replication_args(replicationList)
        self.destroy_script_args(scriptList)
        self.destroy_snapshot_args(appList, snapshotList)
        self.destroy_user_args(userList)

        self.unmanage_app_args(appList)
        self.unmanage_bucket_args(bucketList)
        self.unmanage_cluster_args(clusterList)
        self.unmanage_cloud_args(cloudList)

        self.update_replication_args(replicationList)

        return self.parser
