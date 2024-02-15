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
import json
import sys
import time
import yaml

import astraSDK
import tkSrc


def monitorProtectionTask(protectionID, protectionType, appID, background, pollTimer, parser):
    """Ensure backup/snapshot task was created successfully, then monitor"""
    if protectionID is False:
        return False
    if protectionType == "backup":
        protection_class = astraSDK.backups.getBackups()
    elif protectionType == "snapshot":
        protection_class = astraSDK.snapshots.getSnaps()
    else:
        parser.error(f"unknown protection type: {protectionType}")

    print(f"Starting {protectionType} of {appID}")
    if background:
        print(
            f"Background {protectionType} flag selected, run 'list {protectionType}s' to get status"
        )
        return True

    print(f"Waiting for {protectionType} to complete.", end="")
    sys.stdout.flush()
    err_counter = []
    while len(err_counter) < 3:
        try:
            objects = protection_class.main(appFilter=appID)
            if not objects:
                raise Exception(f"astraSDK.{protectionType}s.get{protectionType}s().main() failed")
            protection_found = False
            for obj in objects["items"]:
                if obj["id"] == protectionID:
                    protection_found = True
                    if obj["state"] == "completed":
                        print("complete!")
                        sys.stdout.flush()
                        return protectionID
                    elif obj["state"] == "failed":
                        print(f"{protectionType} job failed")
                        return False
            if not protection_found:
                raise Exception(f"Protection ID {protectionID} not found")
            time.sleep(pollTimer)
            print(".", end="")
            sys.stdout.flush()
        except Exception as err:
            err_counter.append(err)
    for err in set([str(e) for e in err_counter]):
        protection_class.printError(err + "\n")
    return False


def createV3Backup(
    v3, dry_run, quiet, name, app, appVault, snapshot=None, reclaimPolicy=None, generateName=None
):
    template = tkSrc.helpers.setupJinja("backup")
    v3_dict = yaml.safe_load(
        template.render(
            name=(tkSrc.helpers.isRFC1123(name) if name else name),
            appName=app,
            appVaultName=appVault,
            snapshotName=snapshot,
            reclaimPolicy=reclaimPolicy,
            generateName=generateName,
        )
    )
    if dry_run == "client":
        print(yaml.dump(v3_dict).rstrip("\n"))
        return v3_dict
    else:
        return astraSDK.k8s.createResource(quiet=quiet, dry_run=dry_run, config_context=v3).main(
            f"{v3_dict['kind'].lower()}s",
            v3_dict["metadata"]["namespace"],
            v3_dict,
            version="v1",
            group="astra.netapp.io",
        )


def main(args, parser, ard):
    if args.objectType == "backup":
        if args.v3:
            createV3Backup(
                args.v3,
                args.dry_run,
                args.quiet,
                args.name,
                args.app,
                args.bucket,
                args.snapshot,
                args.reclaimPolicy,
            )
        else:
            protectionID = astraSDK.backups.takeBackup(quiet=args.quiet, verbose=args.verbose).main(
                args.app,
                tkSrc.helpers.isRFC1123(args.name),
                bucketID=args.bucket,
                snapshotID=args.snapshot,
            )
            rc = monitorProtectionTask(
                protectionID,
                args.objectType,
                args.app,
                args.background,
                args.pollTimer,
                parser,
            )
            if rc is False:
                raise SystemExit("monitorProtectionTask() failed")
    elif args.objectType == "cluster":
        with open(args.filePath, encoding="utf8") as f:
            kubeconfigDict = yaml.load(f.read().rstrip(), Loader=yaml.SafeLoader)
            encodedStr = base64.b64encode(json.dumps(kubeconfigDict).encode("utf-8")).decode(
                "utf-8"
            )
        rc = astraSDK.credentials.createCredential(quiet=args.quiet, verbose=args.verbose).main(
            kubeconfigDict["clusters"][0]["name"],
            "kubeconfig",
            {"base64": encodedStr},
            cloudName="private",
        )
        if rc:
            rc = astraSDK.clusters.addCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.cloudID,
                rc["id"],
                privateRouteID=args.privateRouteID,
            )
            if rc is False:
                raise SystemExit("astraSDK.clusters.createCluster() failed")
        else:
            raise SystemExit("astraSDK.credentials.createCredential() failed")
    elif args.objectType == "hook" or args.objectType == "exechook":
        if args.v3:
            with open(args.filePath, encoding="utf8") as f:
                encodedStr = base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")
            template = tkSrc.helpers.setupJinja(args.objectType)
            v3_dict = yaml.safe_load(
                template.render(
                    name=tkSrc.helpers.isRFC1123(args.name),
                    action=args.operation.split("-")[1],
                    appName=args.app,
                    arguments=tkSrc.helpers.prependDump(
                        tkSrc.helpers.createHookList(args.hookArguments), prepend=4
                    ),
                    hookSource=encodedStr,
                    matchingCriteria=tkSrc.helpers.prependDump(
                        tkSrc.helpers.createCriteriaList(
                            args.containerImage,
                            args.namespace,
                            args.podName,
                            args.label,
                            args.containerName,
                        ),
                        prepend=4,
                    ),
                    stage=args.operation.split("-")[0],
                )
            )
            if args.dry_run == "client":
                print(yaml.dump(v3_dict).rstrip("\n"))
            else:
                astraSDK.k8s.createResource(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(
                    f"{v3_dict['kind'].lower()}s",
                    v3_dict["metadata"]["namespace"],
                    v3_dict,
                    version="v1",
                    group="astra.netapp.io",
                )
        else:
            rc = astraSDK.hooks.createHook(quiet=args.quiet, verbose=args.verbose).main(
                args.app,
                args.name,
                args.script,
                args.operation.split("-")[0],
                args.operation.split("-")[1],
                tkSrc.helpers.createHookList(args.hookArguments),
                matchingCriteria=tkSrc.helpers.createCriteriaList(
                    args.containerImage,
                    args.namespace,
                    args.podName,
                    args.label,
                    args.containerName,
                ),
            )
            if rc is False:
                raise SystemExit("astraSDK.hooks.createHook() failed")
    elif args.objectType == "protection" or args.objectType == "schedule":
        naStr = "" if args.v3 else "*"
        if args.granularity == "hourly":
            if args.hour:
                parser.error("'hourly' granularity must not specify -H / --hour")
            args.hour = naStr
            args.dayOfWeek = naStr
            args.dayOfMonth = naStr
        elif args.granularity == "daily":
            if not isinstance(args.hour, int) and not args.hour:
                parser.error("'daily' granularity requires -H / --hour")
            args.dayOfWeek = naStr
            args.dayOfMonth = naStr
        elif args.granularity == "weekly":
            if not isinstance(args.hour, int) and not args.hour:
                parser.error("'weekly' granularity requires -H / --hour")
            if not isinstance(args.dayOfWeek, int) and not args.dayOfWeek:
                parser.error("'weekly' granularity requires -W / --dayOfWeek")
            args.dayOfMonth = naStr
        elif args.granularity == "monthly":
            if not isinstance(args.hour, int) and not args.hour:
                parser.error("'monthly' granularity requires -H / --hour")
            if args.dayOfWeek:
                parser.error("'monthly' granularity must not specify -W / --dayOfWeek")
            if not args.dayOfMonth:
                parser.error("'monthly' granularity requires -M / --dayOfMonth")
            args.dayOfWeek = naStr
        if args.v3:
            template = tkSrc.helpers.setupJinja(args.objectType)
            v3_dict = yaml.safe_load(
                template.render(
                    name=tkSrc.helpers.isRFC1123(f"{args.app}-{args.granularity}") + "-",
                    appName=args.app,
                    appVaultName=args.bucket,
                    backupRetention=args.backupRetention,
                    dayOfMonth=args.dayOfMonth,
                    dayOfWeek=args.dayOfWeek,
                    granularity=args.granularity,
                    hour=args.hour,
                    minute=args.minute,
                    snapshotRetention=args.snapshotRetention,
                )
            )
            if args.dry_run == "client":
                print(yaml.dump(v3_dict).rstrip("\n"))
            else:
                astraSDK.k8s.createResource(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(
                    f"{v3_dict['kind'].lower()}s",
                    v3_dict["metadata"]["namespace"],
                    v3_dict,
                    version="v1",
                    group="astra.netapp.io",
                )
        else:
            rc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.granularity,
                str(args.backupRetention),
                str(args.snapshotRetention),
                str(args.dayOfWeek),
                str(args.dayOfMonth),
                str(args.hour),
                str(args.minute),
                args.app,
            )
            if rc is False:
                raise SystemExit("astraSDK.protections.createProtectionpolicy() failed")
    elif args.objectType == "replication":
        # Validate offset values and create DTSTART string
        if ":" in args.offset:
            hours = args.offset.split(":")[0].zfill(2)
            minutes = args.offset.split(":")[1].zfill(2)
        else:
            hours = "00"
            minutes = args.offset.zfill(2)
        if int(hours) < 0 or int(hours) > 23:
            parser.error(f"offset {args.offset} hours must be between 0 and 23, inclusive")
        elif int(minutes) < 0 or int(minutes) > 59:
            parser.error(f"offset '{args.offset}' minutes must be between 0 and 59, inclusive")
        dtstart = "DTSTART:20220101T" + hours + minutes + "00Z\n"
        # Create RRULE string
        rrule = "RRULE:FREQ=MINUTELY;INTERVAL="
        if "m" in args.replicationFrequency:
            rrule += args.replicationFrequency.strip("m")
        else:
            rrule += str(int(args.replicationFrequency.strip("h")) * 60)
        # Get Source ClusterID
        if ard.needsattr("apps"):
            ard.apps = astraSDK.apps.getApps().main()
        for app in ard.apps["items"]:
            if app["id"] == args.appID:
                sourceClusterID = app["clusterID"]
                sourceNamespaces = app["namespaces"]
        nsMapping = [
            {"clusterID": sourceClusterID, "namespaces": sourceNamespaces},
            {"clusterID": args.destClusterID, "namespaces": [args.destNamespace]},
        ]
        if args.destStorageClass:
            args.destStorageClass = [
                {"storageClassName": args.destStorageClass, "clusterID": args.destClusterID}
            ]
        rc = astraSDK.replications.createReplicationpolicy(
            quiet=args.quiet, verbose=args.verbose
        ).main(
            args.appID,
            args.destClusterID,
            nsMapping,
            destinationStorageClass=args.destStorageClass,
        )
        if rc:
            prc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                "custom",
                "0",
                "0",
                None,
                None,
                None,
                None,
                args.appID,
                dtstart + rrule,
            )
            if prc is False:
                raise SystemExit("astraSDK.protections.createProtectionpolicy() failed")
        else:
            raise SystemExit("astraSDK.replications.createReplicationpolicy() failed")
    elif args.objectType == "script":
        with open(args.filePath, encoding="utf8") as f:
            encodedStr = base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")
        rc = astraSDK.scripts.createScript(quiet=args.quiet, verbose=args.verbose).main(
            name=args.name, source=encodedStr, description=args.description
        )
        if rc is False:
            raise SystemExit("astraSDK.scripts.createScript() failed")
    elif args.objectType == "snapshot":
        if args.v3:
            template = tkSrc.helpers.setupJinja(args.objectType)
            v3_dict = yaml.safe_load(
                template.render(
                    name=tkSrc.helpers.isRFC1123(args.name),
                    appName=args.app,
                    appVaultName=args.bucket,
                    reclaimPolicy=args.reclaimPolicy,
                    createdTimeout=(None if not args.createdTimeout else str(args.createdTimeout)),
                    readyToUseTimeout=(
                        None if not args.readyToUseTimeout else str(args.readyToUseTimeout)
                    ),
                )
            )
            if args.dry_run == "client":
                print(yaml.dump(v3_dict).rstrip("\n"))
            else:
                astraSDK.k8s.createResource(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(
                    f"{v3_dict['kind'].lower()}s",
                    v3_dict["metadata"]["namespace"],
                    v3_dict,
                    version="v1",
                    group="astra.netapp.io",
                )
        else:
            protectionID = astraSDK.snapshots.takeSnap(quiet=args.quiet, verbose=args.verbose).main(
                args.app,
                tkSrc.helpers.isRFC1123(args.name),
            )
            rc = monitorProtectionTask(
                protectionID,
                args.objectType,
                args.app,
                args.background,
                args.pollTimer,
                parser,
            )
            if rc is False:
                raise SystemExit("monitorProtectionTask() failed")
    elif args.objectType == "user":
        # First create the user
        urc = astraSDK.users.createUser(quiet=args.quiet, verbose=args.verbose).main(
            args.email, firstName=args.firstName, lastName=args.lastName
        )
        if urc:
            # Next create the role binding
            rrc = astraSDK.rolebindings.createRolebinding(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.role,
                userID=urc["id"],
                roleConstraints=tkSrc.helpers.createConstraintList(
                    args.namespaceConstraint, args.labelConstraint
                ),
            )
            if rrc:
                # Delete+error "local" users where a tempPassword wasn't provided
                if urc["authProvider"] == "local" and not args.tempPassword:
                    drc = astraSDK.rolebindings.destroyRolebinding(quiet=True).main(rrc["id"])
                    if not drc:
                        raise SystemExit("astraSDK.rolebindings.destroyRolebinding() failed")
                    raise SystemExit("Error: --tempPassword is required for ACC+localAuth")
                # Finally, create the credential if local user
                if urc["authProvider"] == "local":
                    crc = astraSDK.credentials.createCredential(
                        quiet=args.quiet, verbose=args.verbose
                    ).main(
                        urc["id"],
                        "passwordHash",
                        {
                            "cleartext": base64.b64encode(args.tempPassword.encode("utf-8")).decode(
                                "utf-8"
                            ),
                            "change": base64.b64encode("true".encode("utf-8")).decode("utf-8"),
                        },
                    )
                    if not crc:
                        raise SystemExit("astraSDK.credentials.createCredential() failed")
            else:
                raise SystemExit("astraSDK.rolebindings.createRolebinding() failed")
        else:
            raise SystemExit("astraSDK.users.createUser() failed")
