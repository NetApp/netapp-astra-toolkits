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

import base64

import astraSDK
from tkSrc import helpers


def main(args):
    if args.objectType == "apiresources":
        rc = astraSDK.apiresources.getApiResources(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cluster=args.cluster)
        if rc is False:
            raise SystemExit("astraSDK.apiresources.getApiResources() failed")
    elif args.objectType == "apps" or args.objectType == "applications":
        if args.v3:
            rc = astraSDK.k8s.getResources(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                "applications",
                filters=[
                    {
                        "keyFilter": "spec.includedNamespaces[].namespace",
                        "valFilter": args.namespace,
                        "inMatch": True,  # inMatch since app namespaces is a list, not a str
                    },
                    {"keyFilter": "metadata.name", "valFilter": args.nameFilter, "inMatch": True},
                ],
            )
        else:
            rc = astraSDK.apps.getApps(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                namespace=args.namespace,
                nameFilter=args.nameFilter,
                cluster=args.cluster,
            )
            if rc is False:
                raise SystemExit("astraSDK.apps.getApps() failed")
    elif args.objectType == "assets":
        rc = astraSDK.apps.getAppAssets(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(args.appID)
        if rc is False:
            raise SystemExit("astraSDK.apps.getAppAssets() failed")
    elif args.objectType == "backups":
        if args.v3:
            rc = astraSDK.k8s.getResources(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                "backups",
                filters=[{"keyFilter": "spec.applicationRef", "valFilter": args.app}],
            )
        else:
            rc = astraSDK.backups.getBackups(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                raise SystemExit("astraSDK.backups.getBackups() failed")
    elif args.objectType == "buckets" or args.objectType == "appVaults":
        if args.v3:
            rc = astraSDK.k8s.getResources(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                "appvaults",
                filters=[
                    {"keyFilter": "spec.providerType", "valFilter": args.provider},
                    {"keyFilter": "metadata.name", "valFilter": args.nameFilter, "inMatch": True},
                ],
            )
        else:
            rc = astraSDK.buckets.getBuckets(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(nameFilter=args.nameFilter, provider=args.provider)
            if rc is False:
                raise SystemExit("astraSDK.buckets.getBuckets() failed")
    elif args.objectType == "clouds":
        rc = astraSDK.clouds.getClouds(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cloudType=args.cloudType)
        if rc is False:
            raise SystemExit("astraSDK.clouds.getClouds() failed")
    elif args.objectType == "clusters":
        rc = astraSDK.clusters.getClusters(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(
            hideManaged=args.hideManaged,
            hideUnmanaged=args.hideUnmanaged,
            nameFilter=args.nameFilter,
        )
        if rc is False:
            raise SystemExit("astraSDK.clusters.getClusters() failed")
    elif args.objectType == "connectors" or args.objectType == "astraconnectors":
        rc = astraSDK.k8s.getResources(
            quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
        ).main("astraconnectors")
    elif args.objectType == "credentials" or args.objectType == "secrets":
        if args.v3:
            rc = astraSDK.k8s.getSecrets(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main()
        else:
            rc = astraSDK.credentials.getCredentials(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(kubeconfigOnly=args.kubeconfigOnly)
            if rc is False:
                raise SystemExit("astraSDK.credentials.getCredentials() failed")
    elif args.objectType == "hooks" or args.objectType == "exechooks":
        if args.v3:
            rc = astraSDK.k8s.getResources(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                "exechooks", filters=[{"keyFilter": "spec.applicationRef", "valFilter": args.app}]
            )
        else:
            rc = astraSDK.hooks.getHooks(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                raise SystemExit("astraSDK.hooks.getHooks() failed")
    elif args.objectType == "hooksruns" or args.objectType == "exechooksruns":
        rc = astraSDK.k8s.getResources(
            quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
        ).main(
            "exechooksruns", filters=[{"keyFilter": "spec.applicationRef", "valFilter": args.app}]
        )
    elif args.objectType == "iprs" or args.objectType == "inplacerestores":
        resources = astraSDK.k8s.getResources(verbose=args.verbose, config_context=args.v3)
        iprs = helpers.combineResources(
            resources.main("backupinplacerestores"), resources.main("snapshotinplacerestores")
        )
        resources.formatPrint(
            iprs, "inplacerestores", quiet=args.quiet, output=args.output, verbose=args.verbose
        )
    elif args.objectType == "protections" or args.objectType == "schedules":
        if args.v3:
            rc = astraSDK.k8s.getResources(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                "schedules",
                filters=[{"keyFilter": "spec.applicationRef", "valFilter": args.app}],
            )
        else:
            rc = astraSDK.protections.getProtectionpolicies(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                raise SystemExit("astraSDK.protections.getProtectionpolicies() failed")
    elif args.objectType == "replications":
        rc = astraSDK.replications.getReplicationpolicies(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(appFilter=args.app)
        if rc is False:
            raise SystemExit("astraSDK.replications.getReplicationpolicies() failed")
    elif args.objectType == "namespaces":
        if args.v3:
            rc = astraSDK.k8s.getNamespaces(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                nameFilter=args.nameFilter,
                unassociated=args.unassociated,
                minuteFilter=args.minutes,
            )
        else:
            rc = astraSDK.namespaces.getNamespaces(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(
                clusterID=args.clusterID,
                nameFilter=args.nameFilter,
                showRemoved=args.showRemoved,
                unassociated=args.unassociated,
                minuteFilter=args.minutes,
            )
            if rc is False:
                raise SystemExit("astraSDK.namespaces.getNamespaces() failed")
    elif args.objectType == "notifications":
        rc = astraSDK.notifications.getNotifications(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(
            limit=args.limit,
            skip=args.offset,
            minuteFilter=args.minutes,
            severityFilter=args.severity,
        )
        if rc is False:
            raise SystemExit("astraSDK.namespaces.getNotifications() failed")
    elif args.objectType == "restores":
        resources = astraSDK.k8s.getResources(verbose=args.verbose, config_context=args.v3)
        restores = helpers.combineResources(
            resources.main(
                "backuprestores",
                filters=[
                    {
                        "keyFilter": "spec.namespaceMapping[].source",
                        "valFilter": args.sourceNamespace,
                        "inMatch": True,
                    },
                    {
                        "keyFilter": "spec.namespaceMapping[].destination",
                        "valFilter": args.destNamespace,
                        "inMatch": True,
                    },
                ],
            ),
            resources.main(
                "snapshotrestores",
                filters=[
                    {
                        "keyFilter": "spec.namespaceMapping[].source",
                        "valFilter": args.sourceNamespace,
                        "inMatch": True,
                    },
                    {
                        "keyFilter": "spec.namespaceMapping[].destination",
                        "valFilter": args.destNamespace,
                        "inMatch": True,
                    },
                ],
            ),
        )
        resources.formatPrint(
            restores, "restores", quiet=args.quiet, output=args.output, verbose=args.verbose
        )
    elif args.objectType == "rolebindings":
        rc = astraSDK.rolebindings.getRolebindings(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(idFilter=args.idFilter)
        if rc is False:
            raise SystemExit("astraSDK.rolebindings.getRolebindings() failed")
    elif args.objectType == "scripts":
        if args.getScriptSource:
            args.quiet = True
            args.output = "json"
        rc = astraSDK.scripts.getScripts(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(nameFilter=args.nameFilter)
        if rc is False:
            raise SystemExit("astraSDK.scripts.getScripts() failed")
        else:
            if args.getScriptSource:
                if len(rc["items"]) == 0:
                    print(f"Script of name '{args.nameFilter}' not found.")
                for script in rc["items"]:
                    print("#" * len(f"### {script['name']} ###"))
                    print(f"### {script['name']} ###")
                    print("#" * len(f"### {script['name']} ###"))
                    print(base64.b64decode(script["source"]).decode("utf-8"))
    elif args.objectType == "snapshots":
        if args.v3:
            rc = astraSDK.k8s.getResources(
                quiet=args.quiet, output=args.output, verbose=args.verbose, config_context=args.v3
            ).main(
                "snapshots",
                filters=[{"keyFilter": "spec.applicationRef", "valFilter": args.app}],
            )
        else:
            rc = astraSDK.snapshots.getSnaps(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                raise SystemExit("astraSDK.snapshots.getSnaps() failed")
    elif args.objectType == "storagebackends":
        rc = astraSDK.storagebackends.getStorageBackends(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main()
        if rc is False:
            raise SystemExit("astraSDK.backups.getBackends() failed")
    elif args.objectType == "storageclasses":
        rc = astraSDK.storageclasses.getStorageClasses(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cloudType=args.cloudType, clusterStr=args.cluster)
        if rc is False:
            raise SystemExit("astraSDK.storageclasses.getStorageClasses() failed")
    elif args.objectType == "users":
        rc = astraSDK.users.getUsers(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(nameFilter=args.nameFilter)
        if rc is False:
            raise SystemExit("astraSDK.users.getUsers() failed")
