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
import sys

import astraSDK

def exec(args):
    if args.objectType == "apiresources":
        rc = astraSDK.apiresources.getApiResources(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cluster=args.cluster)
        if rc is False:
            print("astraSDK.apiresources.getApiResources() failed")
            sys.exit(1)
    elif args.objectType == "apps":
        rc = astraSDK.apps.getApps(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(
            namespace=args.namespace,
            nameFilter=args.nameFilter,
            cluster=args.cluster,
        )
        if rc is False:
            print("astraSDK.apps.getApps() failed")
            sys.exit(1)
    elif args.objectType == "assets":
        rc = astraSDK.apps.getAppAssets(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(args.appID)
        if rc is False:
            print("astraSDK.apps.getAppAssets() failed")
    elif args.objectType == "backups":
        rc = astraSDK.backups.getBackups(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(appFilter=args.app)
        if rc is False:
            print("astraSDK.backups.getBackups() failed")
            sys.exit(1)
    elif args.objectType == "buckets":
        rc = astraSDK.buckets.getBuckets(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(nameFilter=args.nameFilter, provider=args.provider)
        if rc is False:
            print("astraSDK.buckets.getBuckets() failed")
            sys.exit(1)
    elif args.objectType == "clouds":
        rc = astraSDK.clouds.getClouds(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cloudType=args.cloudType)
        if rc is False:
            print("astraSDK.clouds.getClouds() failed")
            sys.exit(1)
    elif args.objectType == "clusters":
        rc = astraSDK.clusters.getClusters(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(
            hideManaged=args.hideManaged,
            hideUnmanaged=args.hideUnmanaged,
            nameFilter=args.nameFilter,
        )
        if rc is False:
            print("astraSDK.clusters.getClusters() failed")
            sys.exit(1)
    elif args.objectType == "credentials":
        rc = astraSDK.credentials.getCredentials(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(kubeconfigOnly=args.kubeconfigOnly)
        if rc is False:
            print("astraSDK.credentials.getCredentials() failed")
            sys.exit(1)
    elif args.objectType == "hooks":
        rc = astraSDK.hooks.getHooks(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(appFilter=args.app)
        if rc is False:
            print("astraSDK.hooks.getHooks() failed")
            sys.exit(1)
    elif args.objectType == "protections":
        rc = astraSDK.protections.getProtectionpolicies(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(appFilter=args.app)
        if rc is False:
            print("astraSDK.protections.getProtectionpolicies() failed")
            sys.exit(1)
    elif args.objectType == "replications":
        rc = astraSDK.replications.getReplicationpolicies(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(appFilter=args.app)
        if rc is False:
            print("astraSDK.replications.getReplicationpolicies() failed")
            sys.exit(1)
    elif args.objectType == "namespaces":
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
            print("astraSDK.namespaces.getNamespaces() failed")
            sys.exit(1)
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
            print("astraSDK.namespaces.getNotifications() failed")
            sys.exit(1)
    elif args.objectType == "rolebindings":
        rc = astraSDK.rolebindings.getRolebindings(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(idFilter=args.idFilter)
        if rc is False:
            print("astraSDK.rolebindings.getRolebindings() failed")
            sys.exit(1)
    elif args.objectType == "scripts":
        if args.getScriptSource:
            args.quiet = True
            args.output = "json"
        rc = astraSDK.scripts.getScripts(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(nameFilter=args.nameFilter)
        if rc is False:
            print("astraSDK.scripts.getScripts() failed")
            sys.exit(1)
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
        rc = astraSDK.snapshots.getSnaps(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(appFilter=args.app)
        if rc is False:
            print("astraSDK.snapshots.getSnaps() failed")
            sys.exit(1)
    elif args.objectType == "storageclasses":
        rc = astraSDK.storageclasses.getStorageClasses(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cloudType=args.cloudType)
        if rc is False:
            print("astraSDK.storageclasses.getStorageClasses() failed")
            sys.exit(1)
    elif args.objectType == "users":
        rc = astraSDK.users.getUsers(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(nameFilter=args.nameFilter)
        if rc is False:
            print("astraSDK.users.getUsers() failed")
            sys.exit(1)
