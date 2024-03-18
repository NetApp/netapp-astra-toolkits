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

import base64
import copy

import astraSDK
from tkSrc import helpers


def listV3Apps(v3, quiet, output, verbose, skip_tls_verify=False, nameFilter=None, namespace=None):
    """List applications Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main(
        "applications",
        filters=[
            {
                "keyFilter": "spec.includedNamespaces[].namespace",
                "valFilter": namespace,
                "inMatch": True,  # inMatch since app namespaces is a list, not a str
            },
            {"keyFilter": "metadata.name", "valFilter": nameFilter, "inMatch": True},
        ],
    )


def listV3Appvaults(
    v3, quiet, output, verbose, skip_tls_verify=False, provider=None, nameFilter=None
):
    """List appvaults Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main(
        "appvaults",
        filters=[
            {"keyFilter": "spec.providerType", "valFilter": provider},
            {"keyFilter": "metadata.name", "valFilter": nameFilter, "inMatch": True},
        ],
    )


def listV3Backups(v3, quiet, output, verbose, skip_tls_verify=False, app=None):
    """List backups Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main(
        "backups",
        filters=[{"keyFilter": "spec.applicationRef", "valFilter": app}],
    )


def listV3Connectors(v3, quiet, output, verbose, skip_tls_verify=False):
    """List astraconnectors Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main("astraconnectors")


def listV3Hooks(v3, quiet, output, verbose, skip_tls_verify=False, app=None):
    """List exechooks Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main("exechooks", filters=[{"keyFilter": "spec.applicationRef", "valFilter": app}])


def listV3Hooksruns(v3, quiet, output, verbose, skip_tls_verify=False, app=None):
    """List exechooksruns Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main("exechooksruns", filters=[{"keyFilter": "spec.applicationRef", "valFilter": app}])


def listV3Iprs(v3, quiet, output, verbose, skip_tls_verify=False, app=None):
    """List both backupinplacerestores and snapshotinplacerestores Kubernetes custom resources"""
    resources = astraSDK.k8s.getResources(
        verbose=verbose, config_context=v3, skip_tls_verify=skip_tls_verify
    )
    apps = resources.main("applications")
    iprs = helpers.combineResources(
        resources.main("backupinplacerestores"), resources.main("snapshotinplacerestores")
    )
    for a in apps["items"]:
        for ipr in iprs["items"]:
            if a["metadata"]["uid"] in ipr["spec"]["appArchivePath"]:
                ipr["metadata"]["app"] = a
    iprsCopy = copy.deepcopy(iprs)
    for counter, ipr in enumerate(iprsCopy.get("items")):
        if app and app != ipr["metadata"]["app"]["metadata"]["name"]:
            iprs["items"].remove(iprsCopy["items"][counter])
    resources.formatPrint(iprs, "inplacerestores", quiet=quiet, output=output, verbose=verbose)
    return iprs


def listV3Namespaces(
    v3,
    quiet,
    output,
    verbose,
    skip_tls_verify=False,
    nameFilter=None,
    unassociated=None,
    minuteFilter=None,
):
    """List Kubernetes namespaces"""
    return astraSDK.k8s.getNamespaces(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main(nameFilter=nameFilter, unassociated=unassociated, minuteFilter=minuteFilter)


def listV3Restores(
    v3, quiet, output, verbose, skip_tls_verify=False, sourceNamespace=None, destNamespace=None
):
    """List both backuprestores and snapshotrestores Kubernetes custom resources"""
    resources = astraSDK.k8s.getResources(
        verbose=verbose, config_context=v3, skip_tls_verify=skip_tls_verify
    )
    restores = helpers.combineResources(
        resources.main(
            "backuprestores",
            filters=[
                {
                    "keyFilter": "spec.namespaceMapping[].source",
                    "valFilter": sourceNamespace,
                    "inMatch": True,
                },
                {
                    "keyFilter": "spec.namespaceMapping[].destination",
                    "valFilter": destNamespace,
                    "inMatch": True,
                },
            ],
        ),
        resources.main(
            "snapshotrestores",
            filters=[
                {
                    "keyFilter": "spec.namespaceMapping[].source",
                    "valFilter": sourceNamespace,
                    "inMatch": True,
                },
                {
                    "keyFilter": "spec.namespaceMapping[].destination",
                    "valFilter": destNamespace,
                    "inMatch": True,
                },
            ],
        ),
    )
    resources.formatPrint(restores, "restores", quiet=quiet, output=output, verbose=verbose)
    return restores


def listV3Schedules(v3, quiet, output, verbose, skip_tls_verify=False, app=None):
    """List schedules Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main("schedules", filters=[{"keyFilter": "spec.applicationRef", "valFilter": app}])


def listV3Secrets(v3, quiet, output, verbose, skip_tls_verify=False):
    """List Kubernetes secrets"""
    return astraSDK.k8s.getSecrets(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main()


def listV3Snapshots(v3, quiet, output, verbose, skip_tls_verify=False, app=None):
    """List snapshots Kubernetes custom resources"""
    return astraSDK.k8s.getResources(
        quiet=quiet,
        output=output,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main("snapshots", filters=[{"keyFilter": "spec.applicationRef", "valFilter": app}])


def main(args):
    if args.objectType == "apiresources":
        rc = astraSDK.apiresources.getApiResources(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(cluster=args.cluster)
        if rc is False:
            raise SystemExit("astraSDK.apiresources.getApiResources() failed")
    elif args.objectType == "apps" or args.objectType == "applications":
        if args.v3:
            listV3Apps(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
                nameFilter=args.nameFilter,
                namespace=args.namespace,
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
            listV3Backups(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
                app=args.app,
            )
        else:
            rc = astraSDK.backups.getBackups(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                raise SystemExit("astraSDK.backups.getBackups() failed")
    elif args.objectType == "buckets" or args.objectType == "appVaults":
        if args.v3:
            listV3Appvaults(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
                provider=args.provider,
                nameFilter=args.nameFilter,
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
        listV3Connectors(
            args.v3, args.quiet, args.output, args.verbose, skip_tls_verify=args.skip_tls_verify
        )
    elif args.objectType == "credentials" or args.objectType == "secrets":
        if args.v3:
            listV3Secrets(
                args.v3, args.quiet, args.output, args.verbose, skip_tls_verify=args.skip_tls_verify
            )
        else:
            rc = astraSDK.credentials.getCredentials(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(kubeconfigOnly=args.kubeconfigOnly)
            if rc is False:
                raise SystemExit("astraSDK.credentials.getCredentials() failed")
    elif args.objectType == "groups":
        rc = astraSDK.groups.getGroups(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main()
        if rc is False:
            raise SystemExit("astraSDK.groups.getGroups() failed")
    elif args.objectType == "hooks" or args.objectType == "exechooks":
        if args.v3:
            listV3Hooks(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
                app=args.app,
            )
        else:
            rc = astraSDK.hooks.getHooks(
                quiet=args.quiet, verbose=args.verbose, output=args.output
            ).main(appFilter=args.app)
            if rc is False:
                raise SystemExit("astraSDK.hooks.getHooks() failed")
    elif args.objectType == "hooksruns" or args.objectType == "exechooksruns":
        """This is a --v3 only command, per tkSrc/parser.py"""
        listV3Hooksruns(
            args.v3,
            args.quiet,
            args.output,
            args.verbose,
            skip_tls_verify=args.skip_tls_verify,
            app=args.app,
        )
    elif args.objectType == "iprs" or args.objectType == "inplacerestores":
        """This is a --v3 only command, per tkSrc/parser.py"""
        listV3Iprs(
            args.v3,
            args.quiet,
            args.output,
            args.verbose,
            skip_tls_verify=args.skip_tls_verify,
            app=args.app,
        )
    elif args.objectType == "ldapgroups":
        rc = astraSDK.groups.getLdapGroups(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(
            cnFilter=args.cnFilter,
            dnFilter=args.dnFilter,
            limit=args.limit,
            cont=args.cont,
            matchType=("in" if args.matchType == "partial" else "eq"),
        )
    elif args.objectType == "ldapusers":
        rc = astraSDK.users.getLdapUsers(
            quiet=args.quiet, verbose=args.verbose, output=args.output
        ).main(
            emailFilter=args.emailFilter,
            firstNameFilter=args.firstNameFilter,
            lastNameFilter=args.lastNameFilter,
            cnFilter=args.cnFilter,
            limit=args.limit,
            cont=args.cont,
            matchType=("in" if args.matchType == "partial" else "eq"),
        )
    elif args.objectType == "protections" or args.objectType == "schedules":
        if args.v3:
            listV3Schedules(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
                app=args.app,
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
            listV3Namespaces(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
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
        """This is a --v3 only command, per tkSrc/parser.py"""
        listV3Restores(
            args.v3,
            args.quiet,
            args.output,
            args.verbose,
            skip_tls_verify=args.skip_tls_verify,
            sourceNamespace=args.sourceNamespace,
            destNamespace=args.destNamespace,
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
            listV3Snapshots(
                args.v3,
                args.quiet,
                args.output,
                args.verbose,
                skip_tls_verify=args.skip_tls_verify,
                app=args.app,
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
