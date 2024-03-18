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


def createLdapCredential(quiet, verbose, username, password, parser):
    """Create a public cloud (AWS/Azure/GCP) credential via the API"""
    bindDn = base64.b64encode(username.encode("utf-8")).decode("utf-8")
    enpass = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    rc = astraSDK.credentials.createCredential(quiet=quiet, verbose=verbose).main(
        "ldapBindCredential-" + username.split("@")[0],
        "generic",
        {"bindDn": bindDn, "password": enpass},
    )
    if rc:
        return rc
    raise SystemExit("astraSDK.credentials.createCredential() failed")


def main(args, parser, ard):
    if args.objectType == "backup":
        protectionID = astraSDK.backups.takeBackup(quiet=args.quiet, verbose=args.verbose).main(
            args.appID,
            tkSrc.helpers.isRFC1123(args.name),
            bucketID=args.bucketID,
            snapshotID=args.snapshotID,
        )
        rc = monitorProtectionTask(
            protectionID,
            args.objectType,
            args.appID,
            args.background,
            args.pollTimer,
            parser,
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
    elif args.objectType == "group":
        ldapGroups = astraSDK.groups.getLdapGroups().main(dnFilter=args.dn, matchType="eq")
        if len(ldapGroups["items"]) == 0:
            parser.error(f"0 LDAP groups found with DN '{args.dn}'")
        elif len(ldapGroups["items"]) > 1:
            parser.error(f"multiple LDAP users found with DN '{args.dn}'")
        # First create the group
        grc = astraSDK.groups.createGroup(quiet=args.quiet, verbose=args.verbose).main(args.dn)
        if grc:
            # Next create the role binding
            if not astraSDK.rolebindings.createRolebinding(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.role,
                groupID=grc["id"],
                roleConstraints=tkSrc.helpers.createConstraintList(
                    args.namespaceConstraint, args.labelConstraint
                ),
            ):
                raise SystemExit("astraSDK.rolebindings.createRolebinding() failed")
        else:
            raise SystemExit("astraSDK.groups.createGroup() failed")
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
    elif args.objectType == "ldap":
        credential = createLdapCredential(
            args.quiet, args.verbose, args.username, args.password, parser
        )
        ard.settings = astraSDK.settings.getSettings().main()
        ldapSetting = ard.getSingleDict("settings", "name", "astra.account.ldap", parser)
        rc = astraSDK.settings.createLdap(quiet=args.quiet, verbose=args.verbose).main(
            ldapSetting["id"],
            args.url,
            args.port,
            credential["id"],
            args.userBaseDN,
            args.userSearchFilter,
            args.userLoginAttribute,
            args.groupBaseDN,
            groupSearchFilter=args.groupSearchFilter,
            secureMode=args.secure,
        )
        if rc is False:
            raise SystemExit("astraSDK.settings.createLdap() failed")
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
        protectionID = astraSDK.snapshots.takeSnap(quiet=args.quiet, verbose=args.verbose).main(
            args.appID,
            tkSrc.helpers.isRFC1123(args.name),
        )
        rc = monitorProtectionTask(
            protectionID,
            args.objectType,
            args.appID,
            args.background,
            args.pollTimer,
            parser,
        )
        if rc is False:
            raise SystemExit("doProtectionTask() failed")
    elif args.objectType == "user":
        # Handle LDAP use cases
        if args.ldap:
            ldapUsers = astraSDK.users.getLdapUsers().main(emailFilter=args.email, matchType="eq")
            if len(ldapUsers["items"]) == 0:
                parser.error(f"0 LDAP users found with email '{args.email}'")
            elif len(ldapUsers["items"]) > 1:
                parser.error(f"multiple LDAP users found with email '{args.email}'")
            args.firstName = ldapUsers["items"][0]["firstName"]
            args.lastName = ldapUsers["items"][0]["lastName"]
            args.ldap = "ldap"
        # First create the user
        urc = astraSDK.users.createUser(quiet=args.quiet, verbose=args.verbose).main(
            args.email, firstName=args.firstName, lastName=args.lastName, authProvider=args.ldap
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
