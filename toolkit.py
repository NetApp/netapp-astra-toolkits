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

import sys

import astraSDK
import tkSrc


def main(argv=sys.argv):
    # The various functions to populate the lists used for choices() in the options are
    # expensive. argparse provides no way to know what subcommand was selected prior to
    # parsing the options. By then it's too late to decide which functions to run to
    # populate the various choices the differing options for each subcommand needs. So
    # we just go around argparse's back and inspect sys.argv directly.
    acl = tkSrc.classes.ArgparseChoicesLists()
    ard = tkSrc.classes.AstraResourceDicts()
    plaidMode = False

    if len(argv) > 1:
        # verbs must manually be kept in sync with top_level_commands() in tkSrc/parser.py
        verbs = {
            "deploy": False,
            "clone": False,
            "restore": False,
            "list": False,
            "get": False,
            "create": False,
            "manage": False,
            "define": False,
            "destroy": False,
            "unmanage": False,
            "update": False,
        }

        firstverbfoundPosition = None
        verbPosition = None
        cookedlistofVerbs = [x for x in verbs]
        for verb in verbs:
            if verb not in argv:
                # no need to iterate over the arg list for a verb that isn't in there
                continue
            if verbPosition:
                # once we've found the first verb we can stop looking
                break
            for counter, item in enumerate(argv):
                if item == verb:
                    if firstverbfoundPosition is None:
                        # firstverbfoundPosition exists to prevent
                        # "toolkit.py create deploy create deploy" from deciding the second create
                        # is the first verb found
                        firstverbfoundPosition = counter
                    else:
                        if counter > firstverbfoundPosition:
                            continue
                        else:
                            firstverbfoundPosition = counter
                    # Why are we jumping through hoops here to remove the verb we found
                    # from the list of verbs?  Consider the input "toolkit.py deploy deploy"
                    # When we loop over the args we find the first "deploy"
                    # verb["deploy"] gets set to True, we loop over the slice of sys.argv
                    # previous to "deploy" and find no other verbs so verb["deploy"] remains True
                    # Then we find the second deploy.  We loop over the slice of sys.argv previous
                    # to *that* and sure enough, the first "deploy" is in verbs so
                    # verb["deploy"] gets set to False
                    try:
                        cookedlistofVerbs.remove(item)
                    except ValueError:
                        pass
                    verbs[verb] = True
                    verbPosition = counter
                    for item2 in argv[:(counter)]:
                        # argv[:(counter)] is a slice of sys.argv of all the items
                        # before the one we found
                        if item2 in cookedlistofVerbs:
                            # deploy wasn't the verb, it was a symbolic name of an object
                            verbs[verb] = False
                            verbPosition = None

        # Enabling comma separated listing of objects, like:
        # 'toolkit.py list apps,backups,snapshots'
        if (
            (verbs["list"] or verbs["get"])
            and len(argv) > (verbPosition + 1)
            and "," in argv[verbPosition + 1]
        ):
            listTypeArray = argv[verbPosition + 1].split(",")
            for lt in listTypeArray:
                argv[verbPosition + 1] = lt
                main(argv=argv)
            sys.exit(0)

        # Turn off verification to speed things up if true
        for counter, item in enumerate(argv):
            if verbPosition and counter < verbPosition and (item == "-f" or item == "--fast"):
                plaidMode = True

        if not plaidMode:
            # It isn't intuitive, however only one key in verbs can be True
            if verbs["deploy"]:
                ard.charts = tkSrc.helpers.updateHelm()
                acl.charts = ard.buildList("charts", "name")

            elif verbs["clone"]:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
                ard.destClusters = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
                acl.destClusters = ard.buildList("destClusters", "id")
                ard.backups = astraSDK.backups.getBackups().main()
                acl.backups = ard.buildList("backups", "id")
                ard.snapshots = astraSDK.snapshots.getSnaps().main()
                acl.snapshots = ard.buildList("snapshots", "id")
                # if the destination cluster has been specified, only show those storage classes
                if (clusterID := list(set(argv) & set(acl.destClusters))) and len(clusterID) == 1:
                    ard.storageClasses = astraSDK.storageclasses.getStorageClasses().main(
                        clusterStr=clusterID[0], hideUnmanaged=True
                    )
                else:
                    ard.storageClasses = astraSDK.storageclasses.getStorageClasses().main(
                        hideUnmanaged=True
                    )
                acl.storageClasses = ard.buildList("storageClasses", "name")
                acl.storageClasses = list(set(acl.storageClasses))

            elif verbs["restore"]:
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")

                # This expression translates to "Is there an arg after the verb we found?"
                if len(argv) - verbPosition >= 2:
                    # If that arg after the verb "restore" matches an appID then
                    # populate the lists of backups and snapshots for that appID
                    ard.backups = astraSDK.backups.getBackups().main()
                    ard.snapshots = astraSDK.snapshots.getSnaps().main()
                    for a in argv[verbPosition + 1 :]:
                        acl.backups += ard.buildList("backups", "id", "appID", a)
                        acl.snapshots += ard.buildList("snapshots", "id", "appID", a)
            elif (
                verbs["create"]
                and len(argv) - verbPosition >= 2
                and (
                    argv[verbPosition + 1] == "backup"
                    or argv[verbPosition + 1] == "hook"
                    or argv[verbPosition + 1] == "protectionpolicy"
                    or argv[verbPosition + 1] == "protection"
                    or argv[verbPosition + 1] == "replication"
                    or argv[verbPosition + 1] == "snapshot"
                )
            ):
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")
                if argv[verbPosition + 1] == "backup":
                    ard.buckets = astraSDK.buckets.getBuckets(quiet=True).main()
                    acl.buckets = ard.buildList("buckets", "id")
                    # Generate acl.snapshots if an appID was provided
                    for a in argv[verbPosition + 1 :]:
                        if a in acl.apps:
                            ard.snapshots = astraSDK.snapshots.getSnaps().main(appFilter=a)
                            acl.snapshots = ard.buildList("snapshots", "id")
                if argv[verbPosition + 1] == "hook":
                    ard.scripts = astraSDK.scripts.getScripts().main()
                    acl.scripts = ard.buildList("scripts", "id")
                if argv[verbPosition + 1] == "replication":
                    ard.destClusters = astraSDK.clusters.getClusters().main(hideUnmanaged=True)
                    acl.destClusters = ard.buildList("destClusters", "id")
                    ard.storageClasses = astraSDK.storageclasses.getStorageClasses(
                        quiet=True
                    ).main()
                    acl.storageClasses = ard.buildList("storageClasses", "name")
                    acl.storageClasses = list(set(acl.storageClasses))
            elif (
                verbs["create"]
                and len(argv) - verbPosition >= 2
                and argv[verbPosition + 1] == "cluster"
            ):
                ard.clouds = astraSDK.clouds.getClouds().main()
                for cloud in ard.clouds["items"]:
                    if cloud["cloudType"] not in ["GCP", "Azure", "AWS"]:
                        acl.clouds.append(cloud["id"])
                # Add a private cloud if it doesn't already exist
                if len(acl.clouds) == 0:
                    rc = astraSDK.clouds.manageCloud(quiet=True).main("private", "private")
                    if rc:
                        acl.clouds.append(rc["id"])
            elif (
                verbs["create"]
                and len(argv) - verbPosition >= 2
                and argv[verbPosition + 1] == "user"
            ):
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

            elif (
                verbs["list"]
                and len(argv) - verbPosition >= 2
                and argv[verbPosition + 1] == "assets"
            ):
                ard.apps = astraSDK.apps.getApps().main()
                acl.apps = ard.buildList("apps", "id")

            elif (verbs["manage"] or verbs["define"]) and len(argv) - verbPosition >= 2:
                if argv[verbPosition + 1] == "app":
                    ard.namespaces = astraSDK.namespaces.getNamespaces().main()
                    acl.namespaces = ard.buildList("namespaces", "name")
                    acl.clusters = ard.buildList("namespaces", "clusterID")
                    acl.clusters = list(set(acl.clusters))
                elif argv[verbPosition + 1] == "bucket":
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
                    ard.apps = astraSDK.apps.getApps().main()
                    acl.apps = ard.buildList("apps", "id")
                    ard.backups = astraSDK.backups.getBackups().main()
                    acl.backups = ard.buildList(
                        "backups", "id", fKey="appID", fVal=argv[verbPosition + 2]
                    )
                elif argv[verbPosition + 1] == "credential" and len(argv) - verbPosition >= 3:
                    ard.credentials = astraSDK.credentials.getCredentials().main()
                    acl.credentials = ard.buildList("credentials", "id")
                elif argv[verbPosition + 1] == "hook" and len(argv) - verbPosition >= 3:
                    ard.apps = astraSDK.apps.getApps().main()
                    acl.apps = ard.buildList("apps", "id")
                    ard.hooks = astraSDK.hooks.getHooks().main()
                    acl.hooks = ard.buildList(
                        "hooks", "id", fKey="appID", fVal=argv[verbPosition + 2]
                    )
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
                    acl.clusters = ard.buildList(
                        "clusters", "id", fKey="managedState", fVal="managed"
                    )
                elif argv[verbPosition + 1] == "cloud":
                    ard.clouds = astraSDK.clouds.getClouds().main()
                    acl.clouds = ard.buildList("clouds", "id")

            elif (verbs["update"]) and len(argv) - verbPosition >= 2:
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
                    ard.clusters = astraSDK.clusters.getClusters().main()
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

    else:
        raise SystemExit(
            f"{argv[0]}: error: please specify a subcommand. Run '{argv[0]} -h' for "
            "parser information."
        )

    # Manually passing args into argparse via parse_args() shouldn't include the function name
    argv = argv[1:] if "toolkit" in argv[0] else argv
    tkParser = tkSrc.parser.ToolkitParser(acl, plaidMode=plaidMode)
    parser = tkParser.main()
    args = parser.parse_args(args=argv)

    if args.subcommand == "deploy":
        tkSrc.deploy.main(args)
    elif args.subcommand == "clone":
        tkSrc.clone.main(args, parser, ard)
    elif args.subcommand == "restore":
        tkSrc.restore.main(args, parser)
    elif args.subcommand == "list" or args.subcommand == "get":
        tkSrc.list.main(args)
    elif args.subcommand == "create":
        tkSrc.create.main(args, parser, ard)
    elif args.subcommand == "manage" or args.subcommand == "define":
        tkSrc.manage.main(args, parser)
    elif args.subcommand == "destroy":
        tkSrc.destroy.main(args, parser, ard)
    elif args.subcommand == "unmanage":
        tkSrc.unmanage.main(args, ard)
    elif args.subcommand == "update":
        tkSrc.update.main(args, parser, ard)


if __name__ == "__main__":
    main()
