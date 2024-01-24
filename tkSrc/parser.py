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

import argparse


class ToolkitParser:
    """Creates and returns an argparse parser for use in toolkit.py"""

    def __init__(self, acl, plaidMode=False, v3=False):
        """Creates the parser object and global arguments"""
        self.parser = argparse.ArgumentParser(allow_abbrev=True, prog="actoolkit")
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
        v3Group = self.parser.add_argument_group(
            title="v3 group",
            description="use CR-driven Kubernetes workflows rather than the Astra Control API",
        )
        if v3:
            v3Group.add_argument(
                "--v3",
                action="store",
                choices=(acl.contexts if v3 else None),
                help="create a v3 CR directly on the Kubernetes cluster (defaults to current "
                "context, but optionally specify a different context, kubeconfig_file, or "
                "kubeconfig_file:context mapping)",
            )
        else:
            v3Group.add_argument(
                "--v3",
                default=False,
                action="store_true",
                help="create a v3 CR directly on the Kubernetes cluster (defaults to current "
                "context, but optionally specify a different context, kubeconfig_file, or "
                "kubeconfig_file:context mapping)",
            )
        v3Group.add_argument(
            "--dry-run",
            default=False,
            choices=["client", "server"],
            help="client: output YAML to standard out; server: submit request without persisting "
            "the resource",
        )
        self.acl = acl
        self.plaidMode = plaidMode
        self.v3 = v3

    def top_level_commands(self):
        """Creates the top level arguments, such as list, create, destroy, etc.
        Be sure to keep these in sync with verbs{} in the calling function."""
        self.subparsers = self.parser.add_subparsers(
            dest="subcommand", required=True, help="subcommand help"
        )
        self.parserDeploy = self.subparsers.add_parser(
            "deploy",
            help="Deploy kubernetes resources into current context",
        )
        self.parserClone = self.subparsers.add_parser(
            "clone",
            help="Live clone a running app to a new namespace",
        )
        self.parserRestore = self.subparsers.add_parser(
            "restore",
            help="Restore an app from a backup or snapshot to a new namespace",
        )
        self.parserIPR = self.subparsers.add_parser(
            "ipr",
            help="In-Place Restore an app (destructive action for app) from a backup or snapshot",
        )
        self.parserList = self.subparsers.add_parser(
            "list",
            aliases=["get"],
            help="List all items in a class",
        )
        self.parserCopy = self.subparsers.add_parser(
            "copy",
            help="Copy resources from one app to another app",
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
        """'deploy', 'list', 'create', 'manage', 'destroy', 'unmanage', and 'update'
        all have subcommands, for example, 'list apps' or 'manage cluster'."""
        self.subparserDeploy = self.parserDeploy.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserList = self.parserList.add_subparsers(
            title="objectType", dest="objectType", required=True
        )
        self.subparserCopy = self.parserCopy.add_subparsers(
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

    def sub_deploy_commands(self):
        """deploy 'X'"""
        self.subparserDeployAcp = self.subparserDeploy.add_parser(
            "acp",
            help="deploy ACP (Astra Control Provisioner)",
        )
        self.subparserDeployChart = self.subparserDeploy.add_parser(
            "chart",
            help="deploy a Helm chart",
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
        self.subparserListStorageBackends = self.subparserList.add_parser(
            "storagebackends",
            help="list storagebackends",
        )
        self.subparserListStorageClasses = self.subparserList.add_parser(
            "storageclasses",
            help="list storageclasses",
        )
        self.subparserListUsers = self.subparserList.add_parser(
            "users",
            help="list users",
        )

    def sub_copy_commands(self):
        """copy 'X'"""
        self.subparserCopyHooks = self.subparserCopy.add_parser(
            "hooks", help="copy hooks (executionHooks) from one app to another"
        )
        self.subparserCopyProtections = self.subparserCopy.add_parser(
            "protections", help="copy protections from one app to another"
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
            aliases=["appVault"],
            help="manage bucket (appVault in v3 context)",
        )
        self.subparserManageCloud = self.subparserManage.add_parser(
            "cloud",
            help="manage cloud",
        )
        self.subparserManageCluster = self.subparserManage.add_parser(
            "cluster",
            help="manage cluster",
        )

    def sub_destroy_commands(self):
        """destroy 'X'"""
        self.subparserDestroyBackup = self.subparserDestroy.add_parser(
            "backup",
            help="destroy backup",
        )
        self.subparserDestroyCluster = self.subparserDestroy.add_parser(
            "cluster",
            help="destroy cluster",
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
        self.subparserUnmanageCloud = self.subparserUnmanage.add_parser(
            "cloud",
            help="unmanage cloud",
        )
        self.subparserUnmanageCluster = self.subparserUnmanage.add_parser(
            "cluster",
            help="unmanage cluster",
        )

    def sub_update_commands(self):
        """update 'X'"""
        self.subparserUpdateBucket = self.subparserUpdate.add_parser(
            "bucket",
            help="update bucket",
        )
        self.subparserUpdateCloud = self.subparserUpdate.add_parser(
            "cloud",
            help="update cloud",
        )
        self.subparserUpdateCluster = self.subparserUpdate.add_parser(
            "cluster",
            help="update cluster",
        )
        self.subparserUpdateReplication = self.subparserUpdate.add_parser(
            "replication",
            help="update replication",
        )
        self.subparserUpdateScript = self.subparserUpdate.add_parser(
            "script",
            help="update script",
        )

    def clone_args(self):
        """live clone args and flags"""
        self.parserClone.add_argument(
            "sourceApp",
            choices=(None if self.plaidMode else self.acl.apps),
            help="Source app to live clone",
        )
        self.parserClone.add_argument("appName", help="The logical name of the new app")
        if not self.v3:
            self.parserClone.add_argument(
                "cluster",
                choices=(None if self.plaidMode else self.acl.destClusters),
                help="Cluster to clone into (can be same as source)",
            )
        namespaceGroup = self.parserClone.add_argument_group(
            title="new namespace group",
            description="the namespace(s) to clone the app into (mutually exclusive)",
        )
        namespaceME = namespaceGroup.add_mutually_exclusive_group()
        namespaceME.add_argument(
            "--newNamespace",
            required=False,
            default=None,
            help="For single-namespace apps, specify the new namespace name (if not"
            + " specified the 'appName' field is used)",
        )
        namespaceME.add_argument(
            "--multiNsMapping",
            required=False,
            default=None,
            action="append",
            nargs="*",
            help="For multi-namespace apps, specify matching number of sourcens1=destns1 mappings",
        )
        self.parserClone.add_argument(
            "--newStorageClass",
            choices=(None if self.plaidMode else self.acl.storageClasses),
            required=False,
            default=None,
            help="Optionally specify a different storage class for the new app",
        )
        if not self.v3:
            pollingGroup = self.parserClone.add_argument_group(
                title="polling group", description="optionally modify default polling mechanism"
            )
            pollingGroup.add_argument(
                "-b",
                "--background",
                default=False,
                action="store_true",
                help="Run clone operation in the background instead of polling",
            )
            pollingGroup.add_argument(
                "-t",
                "--pollTimer",
                type=int,
                default=5,
                help="The frequency (seconds) to poll the operation status (default: %(default)s)",
            )

    def restore_args(self):
        """restore args and flags"""
        self.parserRestore.add_argument(
            "restoreSource",
            choices=(None if self.plaidMode else self.acl.dataProtections),
            help="Source backup or snapshot to restore the app from",
        )
        self.parserRestore.add_argument("appName", help="The logical name of the newly defined app")
        if not self.v3:
            self.parserRestore.add_argument(
                "cluster",
                choices=(None if self.plaidMode else self.acl.destClusters),
                help="Cluster to restore into (can be same as source)",
            )
        namespaceGroup = self.parserRestore.add_argument_group(
            title="new namespace group",
            description="the namespace(s) to restore the app into (mutually exclusive)",
        )
        namespaceME = namespaceGroup.add_mutually_exclusive_group()
        namespaceME.add_argument(
            "--newNamespace",
            required=False,
            default=None,
            help="For single-namespace apps, specify the new namespace name (if not"
            + " specified the 'appName' field is used)",
        )
        namespaceME.add_argument(
            "--multiNsMapping",
            required=False,
            default=None,
            action="append",
            nargs="*",
            help="For multi-namespace apps, specify matching number of sourcens1=destns1 mappings",
        )
        self.parserRestore.add_argument(
            "--newStorageClass",
            choices=(None if self.plaidMode else self.acl.storageClasses),
            required=False,
            default=None,
            help="Optionally specify a different storage class for the new app",
        )
        filterGroup = self.parserRestore.add_argument_group(
            title="filter group", description="optionally restore a subset of resources via filters"
        )
        filterGroup.add_argument(
            "--filterSelection",
            choices=["include", "exclude"],
            default=None,
            help="How the resource filter(s) select resources",
        )
        filterGroup.add_argument(
            "--filterSet",
            default=None,
            action="append",
            nargs="*",
            help=r"A comma separated set of key=value filter pairs, where 'key' is one of "
            "['namespace', 'name', 'label', 'group', 'version', 'kind']. This argument can be "
            "specified multiple times for multiple filter sets:\n--filterSet version=v1,kind="
            "PersistentVolumeClaim --filterSet label=app.kubernetes.io/tier=backend,name=mysql",
        )
        if not self.v3:
            pollingGroup = self.parserRestore.add_argument_group(
                title="polling group", description="optionally modify default polling mechanism"
            )
            pollingGroup.add_argument(
                "-b",
                "--background",
                default=False,
                action="store_true",
                help="Run restore operation in the background instead of polling",
            )
            pollingGroup.add_argument(
                "-t",
                "--pollTimer",
                type=int,
                default=5,
                help="The frequency (seconds) to poll the operation status (default: %(default)s)",
            )

    def IPR_args(self):
        """IPR args and flags"""
        self.parserIPR.add_argument(
            "app",
            choices=(None if self.plaidMode else self.acl.apps),
            help="app to in-place-restore",
        )
        group = self.parserIPR.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--backup",
            choices=(None if self.plaidMode else self.acl.backups),
            required=False,
            default=None,
            help="Source backup to in-place-restore from",
        )
        group.add_argument(
            "--snapshot",
            choices=(None if self.plaidMode else self.acl.snapshots),
            required=False,
            default=None,
            help="Source snapshot to in-place-restore from",
        )
        filterGroup = self.parserIPR.add_argument_group(
            title="filter group",
            description="optionally in-place-restore a subset of resources via filters",
        )
        filterGroup.add_argument(
            "--filterSelection",
            choices=["include", "exclude"],
            default=None,
            help="How the resource filter(s) select resources",
        )
        filterGroup.add_argument(
            "--filterSet",
            default=None,
            action="append",
            nargs="*",
            help=r"A comma separated set of key=value filter pairs, where 'key' is one of "
            "['namespace', 'name', 'label', 'group', 'version', 'kind']. This argument can be "
            "specified multiple times for multiple filter sets:\n--filterSet version=v1,kind="
            "PersistentVolumeClaim --filterSet label=app.kubernetes.io/tier=backend,name=mysql",
        )
        if not self.v3:
            pollingGroup = self.parserIPR.add_argument_group(
                title="polling group", description="optionally modify default polling mechanism"
            )
            pollingGroup.add_argument(
                "-b",
                "--background",
                default=False,
                action="store_true",
                help="Run restore operation in the background instead of polling",
            )
            pollingGroup.add_argument(
                "-t",
                "--pollTimer",
                type=int,
                default=5,
                help="The frequency (seconds) to poll the operation status (default: %(default)s)",
            )

    def deploy_acp_args(self):
        """deploy ACP args and flags"""
        self.subparserDeployAcp.add_argument(
            "--regCred",
            choices=(None if self.plaidMode else self.acl.credentials),
            default=None,
            help="optionally specify the name of the existing registry credential "
            "(rather than automatically creating a new secret)",
        )
        self.subparserDeployAcp.add_argument(
            "--registry",
            default=None,
            help="optionally specify the FQDN of the ACP image source registry "
            "(defaults to cr.<astra-control-fqdn>)",
        )

    def deploy_chart_args(self):
        """deploy helm chart args and flags"""
        self.subparserDeployChart.add_argument(
            "app",
            help="name of app",
        )
        self.subparserDeployChart.add_argument(
            "chart",
            choices=(None if self.plaidMode else self.acl.charts),
            help="chart to deploy",
        )
        self.subparserDeployChart.add_argument(
            "-n",
            "--namespace",
            required=True,
            help="Namespace to deploy into (must not already exist)",
        )
        self.subparserDeployChart.add_argument(
            "-f",
            "--values",
            required=False,
            action="append",
            nargs="*",
            help="Specify Helm values in a YAML file",
        )
        self.subparserDeployChart.add_argument(
            "--set",
            required=False,
            action="append",
            nargs="*",
            help="Individual helm chart parameters",
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

    def list_assets_args(self):
        """list assets args and flags"""
        self.subparserListAssets.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
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
            choices=["GCP", "Azure", "AWS", "private"],
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
            choices=["GCP", "Azure", "AWS", "private"],
            help="Only show storageclasses of a single cloud type",
        )
        self.subparserListStorageClasses.add_argument(
            "-c", "--cluster", default=None, help="Only show storageclasses from this cluster"
        )

    def list_users_args(self):
        """list users args and flags"""
        self.subparserListUsers.add_argument(
            "-f",
            "--nameFilter",
            default=None,
            help="Filter users by this value to minimize output (partial match)",
        )

    def copy_hooks_args(self):
        """copy hooks args and flags"""
        self.subparserCopyHooks.add_argument(
            "sourceApp",
            choices=(None if self.plaidMode else self.acl.apps),
            help="the app to source the hooks from",
        )
        self.subparserCopyHooks.add_argument(
            "destinationApp",
            choices=(None if self.plaidMode else self.acl.destApps),
            help="the app to copy the hooks into",
        )

    def copy_protections_args(self):
        """copy protections args and flags"""
        self.subparserCopyProtections.add_argument(
            "sourceApp",
            choices=(None if self.plaidMode else self.acl.apps),
            help="the app to source the protections from",
        )
        self.subparserCopyProtections.add_argument(
            "destinationApp",
            choices=(None if self.plaidMode else self.acl.destApps),
            help="the app to copy the protections into",
        )

    def create_backup_args(self):
        """create backups args and flags"""
        self.subparserCreateBackup.add_argument(
            "app",
            choices=(None if self.plaidMode else self.acl.apps),
            help="app to backup",
        )
        self.subparserCreateBackup.add_argument(
            "name",
            help="Name of backup to be taken",
        )
        self.subparserCreateBackup.add_argument(
            "-u",
            "--appVault" if self.v3 else "--bucketID",
            dest="bucket",
            default=None,
            required=(True if self.v3 else False),
            choices=(None if self.plaidMode else self.acl.buckets),
            help="Specify which bucket to store the backup",
        )
        self.subparserCreateBackup.add_argument(
            "-s",
            "--snapshot" if self.v3 else "--snapshotID",
            dest="snapshot",
            default=None,
            choices=(None if self.plaidMode else self.acl.snapshots),
            help="Optionally specify an existing snapshot as the source of the backup",
        )
        if self.v3:
            self.subparserCreateBackup.add_argument(
                "-r",
                "--reclaimPolicy",
                default=None,
                choices=["Delete", "Retain"],
                help="Define how to handle the snapshot data when the snapshot CR is deleted",
            )
        else:
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

    def create_cluster_args(self):
        """create cluster args and flags"""
        self.subparserCreateCluster.add_argument(
            "filePath",
            help="the local filesystem path to the cluster kubeconfig",
        )
        self.subparserCreateCluster.add_argument(
            "-c",
            "--cloudID",
            choices=(None if self.plaidMode else self.acl.clouds),
            default=(self.acl.clouds[0] if len(self.acl.clouds) == 1 else None),
            required=(False if len(self.acl.clouds) == 1 else True),
            help="The cloudID to add the cluster to (only required if # of clouds > 1)",
        )
        self.subparserCreateCluster.add_argument(
            "--privateRouteID",
            default=None,
            required=False,
            help="The private route identifier for private clusters "
            "(can obtained from the Astra Connector)",
        )

    def create_hook_args(self):
        """create hooks args and flags"""
        self.subparserCreateHook.add_argument(
            "app",
            choices=(None if self.plaidMode else self.acl.apps),
            help="app to create an execution hook for",
        )
        self.subparserCreateHook.add_argument(
            "name",
            help="Name of the execution hook to be created",
        )
        if self.v3:
            self.subparserCreateHook.add_argument(
                "filePath",
                help="the local filesystem path to the script",
            )
        else:
            self.subparserCreateHook.add_argument(
                "script",
                choices=(None if self.plaidMode else self.acl.scripts),
                help="script to use for the execution hook",
            )
        self.subparserCreateHook.add_argument(
            "-o",
            "--operation",
            choices=[
                "pre-snapshot",
                "post-snapshot",
                "pre-backup",
                "post-backup",
                "post-restore",
                "post-failover",
            ],
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

    def create_protection_args(self):
        """create protection args and flags"""
        self.subparserCreateProtection.add_argument(
            "app",
            choices=(None if self.plaidMode else self.acl.apps),
            help="the application to create protection schedule for",
        )
        if self.v3:
            self.subparserCreateProtection.add_argument(
                "-u",
                "--appVault",
                dest="bucket",
                default=None,
                required=True,
                choices=(None if self.plaidMode else self.acl.buckets),
                help="Name of the AppVault to use as the target of the backup/snapshot",
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

    def create_replication_args(self):
        """create replication policy args and flags"""
        self.subparserCreateReplication.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
            help="appID of the application to create the replication policy for",
        )
        self.subparserCreateReplication.add_argument(
            "-c",
            "--destClusterID",
            choices=(None if self.plaidMode else self.acl.destClusters),
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
            choices=(None if self.plaidMode else self.acl.storageClasses),
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

    def create_snapshot_args(self):
        """create snapshot args and flags"""
        self.subparserCreateSnapshot.add_argument(
            "app",
            choices=(None if self.plaidMode else self.acl.apps),
            help="app to snapshot",
        )
        self.subparserCreateSnapshot.add_argument(
            "name",
            help="Name of snapshot to be taken",
        )
        if self.v3:
            self.subparserCreateSnapshot.add_argument(
                "-u",
                "--appVault",
                dest="bucket",
                default=None,
                required=True,
                choices=(None if self.plaidMode else self.acl.buckets),
                help="Specify which appVault to store snapshot metadata",
            )
            self.subparserCreateSnapshot.add_argument(
                "-r",
                "--reclaimPolicy",
                default=None,
                choices=["Delete", "Retain"],
                help="Define how to handle the snapshot data when the snapshot CR is deleted",
            )
            self.subparserCreateSnapshot.add_argument(
                "-c",
                "--createdTimeout",
                type=int,
                default=None,
                help="The time (in minutes) to wait for the snapshot CreationTime to be set before "
                "returning timeout error (default: 5)",
            )
            self.subparserCreateSnapshot.add_argument(
                "-e",
                "--readyToUseTimeout",
                type=int,
                default=None,
                help="The time (in minutes) to wait for Snapshot CR to complete before returning "
                "timeout error (default: 30)",
            )
        else:
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

    def create_user_args(self):
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
            choices=(None if self.plaidMode else self.acl.labels),
            nargs="*",
            action="append",
            help="Restrict user role to label constraints",
        )
        self.subparserCreateUser.add_argument(
            "-n",
            "--namespaceConstraint",
            default=None,
            choices=(None if self.plaidMode else self.acl.namespaces),
            nargs="*",
            action="append",
            help="Restrict user role to namespace constraints",
        )

    def manage_app_args(self):
        """manage app args and flags"""
        self.subparserManageApp.add_argument(
            "appName", help="The logical name of the newly defined app"
        )
        self.subparserManageApp.add_argument(
            "namespace",
            choices=(None if self.plaidMode else self.acl.namespaces),
            help="The namespace to move from undefined (aka unmanaged) to defined (aka managed)",
        )
        if not self.v3:
            self.subparserManageApp.add_argument(
                "clusterID",
                choices=(None if self.plaidMode else self.acl.clusters),
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
            + " argument (-c csr-kind1 -c csr-kind2 app=appname)",
        )

    def manage_bucket_args(self):
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
        if self.v3:
            self.subparserManageBucket.add_argument(
                "-c",
                "--secret",
                dest="credential",
                required=True,
                nargs=2,
                action="append",
                choices=(None if self.plaidMode else self.acl.credentials + self.acl.keys),
                help=(
                    "The Kubernetes secret name and corresponding key name storing the credential"
                    " (-c gcp-credential credentials.json), if specifying S3 accessKey and "
                    "secretKey, accessKey *must* be specified first (-c s3-creds accessKeyID "
                    "-c s3-creds secretAccessKey)"
                ),
            )
            self.subparserManageBucket.add_argument(
                "--http",
                action="store_true",
                default=False,
                help="Optionally use http instead of https to connect to the bucket",
            )
            self.subparserManageBucket.add_argument(
                "--skipCertValidation",
                action="store_true",
                default=False,
                help="Optionally skip TLS certificate validation",
            )

        else:
            credGroup = self.subparserManageBucket.add_argument_group(
                "credentialGroup",
                "Either an (existing credential) OR (accessKey AND accessSecret)",
            )
            credGroup.add_argument(
                "-c",
                "--credentialID",
                dest="credential",
                required=False,
                default=None,
                choices=(None if self.plaidMode else self.acl.credentials),
                help="The ID of the credentials used to access the bucket",
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

    def manage_cluster_args(self):
        """manage cluster args and flags"""
        if self.v3:
            self.subparserManageCluster.add_argument(
                "clusterName",
                help="The friendly name of the cluster",
            )
            self.subparserManageCluster.add_argument(
                "-c",
                "--cloudID",
                choices=(None if self.plaidMode else self.acl.clouds),
                default=(self.acl.clouds[0] if len(self.acl.clouds) == 1 else None),
                required=(False if len(self.acl.clouds) == 1 else True),
                help="The cloudID to add the cluster to (only required if # of clouds > 1)",
            )
            self.subparserManageCluster.add_argument(
                "-v",
                "--operator-version",
                required=False,
                default="latest",
                help="Optionally specify the astra-connector-operator version "
                "(default: %(default)s)",
            )
            self.subparserManageCluster.add_argument(
                "--regCred",
                choices=(None if self.plaidMode else self.acl.credentials),
                default=None,
                help="optionally specify the name of the existing registry credential "
                "(rather than automatically creating a new secret)",
            )
            self.subparserManageCluster.add_argument(
                "--registry",
                default=None,
                help="optionally specify the FQDN of the ACP image source registry "
                "(defaults to cr.<astra-control-fqdn>)",
            )
        else:
            self.subparserManageCluster.add_argument(
                "cluster",
                choices=(None if self.plaidMode else self.acl.clusters),
                help="clusterID of the cluster to manage",
            )
            self.subparserManageCluster.add_argument(
                "-s",
                "--defaultStorageClassID",
                choices=(None if self.plaidMode else self.acl.storageClasses),
                default=None,
                help="Optionally modify the default storage class",
            )

    def manage_cloud_args(self):
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
            "-p",
            "--credentialPath",
            default=None,
            help="the local filesystem path to the cloud credential (required for all but "
            + "'private' clouds)",
        )
        self.subparserManageCloud.add_argument(
            "-b",
            "--defaultBucketID",
            choices=(None if self.plaidMode else self.acl.buckets),
            default=None,
            help="optionally specify the default bucketID for backups",
        )

    def destroy_backup_args(self):
        """destroy backup args and flags"""
        self.subparserDestroyBackup.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
            help="appID of app to destroy backups from",
        )
        self.subparserDestroyBackup.add_argument(
            "backupID",
            choices=(None if self.plaidMode else self.acl.backups),
            help="backupID to destroy",
        )

    def destroy_cluster_args(self):
        """destroy cluster args and flags"""
        self.subparserDestroyCluster.add_argument(
            "cluster",
            choices=(None if self.plaidMode else self.acl.clusters),
            help="cluster to destroy",
        )

    def destroy_credential_args(self):
        """destroy credential args and flags"""
        self.subparserDestroyCredential.add_argument(
            "credentialID",
            choices=(None if self.plaidMode else self.acl.credentials),
            help="credentialID to destroy",
        )

    def destroy_hook_args(self):
        """destroy hook args and flags"""
        self.subparserDestroyHook.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
            help="appID of app to destroy hooks from",
        )
        self.subparserDestroyHook.add_argument(
            "hookID",
            choices=(None if self.plaidMode else self.acl.hooks),
            help="hookID to destroy",
        )

    def destroy_protection_args(self):
        """destroy protection args and flags"""
        self.subparserDestroyProtection.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
            help="appID of app to destroy protection policy from",
        )
        self.subparserDestroyProtection.add_argument(
            "protectionID",
            choices=(None if self.plaidMode else self.acl.protections),
            help="protectionID to destroy",
        )

    def destroy_replication_args(self):
        """destroy replication args and flags"""
        self.subparserDestroyReplication.add_argument(
            "replicationID",
            choices=(None if self.plaidMode else self.acl.replications),
            help="replicationID to destroy",
        )

    def destroy_script_args(self):
        """destroy script args and flags"""
        self.subparserDestroyScript.add_argument(
            "scriptID",
            choices=(None if self.plaidMode else self.acl.scripts),
            help="scriptID of script to destroy",
        )

    def destroy_snapshot_args(self):
        """destroy snapshot args and flags"""
        self.subparserDestroySnapshot.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
            help="appID of app to destroy snapshot from",
        )
        self.subparserDestroySnapshot.add_argument(
            "snapshotID",
            choices=(None if self.plaidMode else self.acl.snapshots),
            help="snapshotID to destroy",
        )

    def destroy_user_args(self):
        """destroy user args and flags"""
        self.subparserDestroyUser.add_argument(
            "userID",
            choices=(None if self.plaidMode else self.acl.users),
            help="userID to destroy",
        )

    def unmanage_app_args(self):
        """unmanage app args and flags"""
        self.subparserUnmanageApp.add_argument(
            "appID",
            choices=(None if self.plaidMode else self.acl.apps),
            help="appID of app to move from managed to unmanaged",
        )

    def unmanage_bucket_args(self):
        """unmanage bucket args and flags"""
        self.subparserUnmanageBucket.add_argument(
            "bucketID",
            choices=(None if self.plaidMode else self.acl.buckets),
            help="bucketID of bucket to unmanage",
        )

    def unmanage_cluster_args(self):
        """unmanage cluster args and flags"""
        self.subparserUnmanageCluster.add_argument(
            "cluster",
            choices=(None if self.plaidMode else self.acl.clusters),
            help="the cluster to unmanage",
        )

    def unmanage_cloud_args(self):
        """unmanage cloud args and flags"""
        self.subparserUnmanageCloud.add_argument(
            "cloudID",
            choices=(None if self.plaidMode else self.acl.clouds),
            help="cloudID of the cloud to unmanage",
        )

    def update_bucket_args(self):
        """update bucket args and flags"""
        self.subparserUpdateBucket.add_argument(
            "bucketID",
            choices=(None if self.plaidMode else self.acl.buckets),
            help="bucketID to update",
        )
        credGroup = self.subparserUpdateBucket.add_argument_group(
            "credentialGroup",
            "Either an (existing credentialID) OR (accessKey AND accessSecret)",
        )
        credGroup.add_argument(
            "-c",
            "--credentialID",
            choices=(None if self.plaidMode else self.acl.credentials),
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

    def update_cloud_args(self):
        """update cloud args and flags"""
        self.subparserUpdateCloud.add_argument(
            "cloudID",
            choices=(None if self.plaidMode else self.acl.clouds),
            help="cloudID to update",
        )
        credGroup = self.subparserUpdateCloud.add_mutually_exclusive_group()
        credGroup.add_argument(
            "-c",
            "--credentialID",
            default=None,
            choices=(None if self.plaidMode else self.acl.credentials),
            help="The existing ID of the credentials used to access the cloud",
        )
        credGroup.add_argument(
            "-p",
            "--credentialPath",
            default=None,
            help="the local filesystem path to the new cloud credential",
        )
        self.subparserUpdateCloud.add_argument(
            "-b",
            "--defaultBucketID",
            choices=(None if self.plaidMode else self.acl.buckets),
            default=None,
            help="the new default bucketID for backups",
        )

    def update_cluster_args(self):
        """update cluster args and flags"""
        self.subparserUpdateCluster.add_argument(
            "clusterID",
            choices=(None if self.plaidMode else self.acl.clusters),
            help="clusterID to update",
        )
        self.subparserUpdateCluster.add_argument(
            "-p",
            "--credentialPath",
            default=None,
            help="the local filesystem path to the new cluster credential",
        )
        self.subparserUpdateCluster.add_argument(
            "-b",
            "--defaultBucketID",
            choices=(None if self.plaidMode else self.acl.buckets),
            default=None,
            help="the new default bucket / appVault for the cluster",
        )

    def update_replication_args(self):
        """update replication args and flags"""
        self.subparserUpdateReplication.add_argument(
            "replicationID",
            choices=(None if self.plaidMode else self.acl.replications),
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

    def update_script_args(self):
        """update script args and flags"""
        self.subparserUpdateScript.add_argument(
            "scriptID",
            choices=(None if self.plaidMode else self.acl.scripts),
            help="scriptID to update",
        )
        self.subparserUpdateScript.add_argument(
            "filePath",
            help="the local filesystem path to the updated script",
        )

    def main(self):
        # Create the top-level commands like: deploy, clone, list, manage, etc.
        self.top_level_commands()

        # *Some* top-level commands have sub-commands like: list apps vs list buckets
        self.sub_commands()

        # Of those top-level commands with sub-commands, create those sub-command parsers
        self.sub_deploy_commands()
        self.sub_list_commands()
        self.sub_copy_commands()
        self.sub_create_commands()
        self.sub_manage_commands()
        self.sub_destroy_commands()
        self.sub_unmanage_commands()
        self.sub_update_commands()

        # Create arguments for all commands
        self.clone_args()
        self.restore_args()
        self.IPR_args()

        self.deploy_acp_args()
        self.deploy_chart_args()

        self.list_apiresources_args()
        self.list_apps_args()
        self.list_assets_args()
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

        self.copy_hooks_args()
        self.copy_protections_args()

        self.create_backup_args()
        self.create_cluster_args()
        self.create_hook_args()
        self.create_protection_args()
        self.create_replication_args()
        self.create_script_args()
        self.create_snapshot_args()
        self.create_user_args()

        self.manage_app_args()
        self.manage_bucket_args()
        self.manage_cluster_args()
        self.manage_cloud_args()

        self.destroy_backup_args()
        self.destroy_cluster_args()
        self.destroy_credential_args()
        self.destroy_hook_args()
        self.destroy_protection_args()
        self.destroy_replication_args()
        self.destroy_script_args()
        self.destroy_snapshot_args()
        self.destroy_user_args()

        self.unmanage_app_args()
        self.unmanage_bucket_args()
        self.unmanage_cluster_args()
        self.unmanage_cloud_args()

        self.update_bucket_args()
        self.update_cloud_args()
        self.update_replication_args()
        self.update_script_args()
        self.update_cluster_args()

        return self.parser
