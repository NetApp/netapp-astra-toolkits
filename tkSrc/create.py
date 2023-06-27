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


def doProtectionTask(protectionType, appID, name, background, pollTimer, quiet, verbose):
    """Take a snapshot/backup of appID giving it name <name>
    Return the snapshotID/backupID of the backup taken or False if the protection task fails"""
    if protectionType == "backup":
        protectionID = astraSDK.backups.takeBackup(quiet=quiet, verbose=verbose).main(appID, name)
    elif protectionType == "snapshot":
        protectionID = astraSDK.snapshots.takeSnap(quiet=quiet, verbose=verbose).main(appID, name)
    if protectionID is False:
        return False

    print(f"Starting {protectionType} of {appID}")
    if background:
        print(
            f"Background {protectionType} flag selected, run 'list {protectionType}s' to get status"
        )
        return True

    print(f"Waiting for {protectionType} to complete.", end="")
    sys.stdout.flush()
    while True:
        if protectionType == "backup":
            objects = astraSDK.backups.getBackups().main()
        elif protectionType == "snapshot":
            objects = astraSDK.snapshots.getSnaps().main()
        if not objects:
            # This isn't technically true.  Trying to list the backups/snapshots after taking
            # the protection job failed.  The protection job itself may eventually succeed.
            print(f"Taking {protectionType} failed")
            return False
        for obj in objects["items"]:
            # Just because the API call to create a backup/snapshot succeeded, that doesn't
            # mean the actual backup will succeed. So loop to show completed or failed.
            if obj["id"] == protectionID:
                if obj["state"] == "completed":
                    print("complete!")
                    sys.stdout.flush()
                    return protectionID
                elif obj["state"] == "failed":
                    print(f"{protectionType} job failed")
                    return False
        time.sleep(pollTimer)
        print(".", end="")
        sys.stdout.flush()


def main(args, parser, ard):
    if args.objectType == "backup":
        rc = doProtectionTask(
            args.objectType,
            args.appID,
            tkSrc.helpers.isRFC1123(args.name),
            args.background,
            args.pollTimer,
            args.quiet,
            args.verbose,
        )
        if rc is False:
            raise SystemExit("doProtectionTask() failed")
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
    elif args.objectType == "hook":
        rc = astraSDK.hooks.createHook(quiet=args.quiet, verbose=args.verbose).main(
            args.appID,
            args.name,
            args.scriptID,
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
    elif args.objectType == "protection" or args.objectType == "protectionpolicy":
        if args.granularity == "hourly":
            if args.hour:
                parser.error("'hourly' granularity must not specify -H / --hour")
            args.hour = "*"
            args.dayOfWeek = "*"
            args.dayOfMonth = "*"
        elif args.granularity == "daily":
            if type(args.hour) != int and not args.hour:
                parser.error("'daily' granularity requires -H / --hour")
            args.dayOfWeek = "*"
            args.dayOfMonth = "*"
        elif args.granularity == "weekly":
            if type(args.hour) != int and not args.hour:
                parser.error("'weekly' granularity requires -H / --hour")
            if type(args.dayOfWeek) != int and not args.dayOfWeek:
                parser.error("'weekly' granularity requires -W / --dayOfWeek")
            args.dayOfMonth = "*"
        elif args.granularity == "monthly":
            if type(args.hour) != int and not args.hour:
                parser.error("'monthly' granularity requires -H / --hour")
            if args.dayOfWeek:
                parser.error("'monthly' granularity must not specify -W / --dayOfWeek")
            if not args.dayOfMonth:
                parser.error("'monthly' granularity requires -M / --dayOfMonth")
            args.dayOfWeek = "*"
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
            args.appID,
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
        rc = doProtectionTask(
            args.objectType,
            args.appID,
            tkSrc.helpers.isRFC1123(args.name),
            args.background,
            args.pollTimer,
            args.quiet,
            args.verbose,
        )
        if rc is False:
            raise SystemExit("doProtectionTask() failed")
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
