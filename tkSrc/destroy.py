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


def main(args, parser, ard):
    if args.objectType == "backup":
        rc = astraSDK.backups.destroyBackup(quiet=args.quiet, verbose=args.verbose).main(
            args.appID, args.backupID
        )
        if rc:
            print(f"Backup {args.backupID} destroyed")
        else:
            raise SystemExit(f"Failed destroying backup: {args.backupID}")
    elif args.objectType == "credential":
        rc = astraSDK.credentials.destroyCredential(quiet=args.quiet, verbose=args.verbose).main(
            args.credentialID
        )
        if rc:
            print(f"Credential {args.credentialID} destroyed")
        else:
            raise SystemExit(f"Failed destroying credential: {args.credentialID}")
    elif args.objectType == "hook":
        rc = astraSDK.hooks.destroyHook(quiet=args.quiet, verbose=args.verbose).main(
            args.appID, args.hookID
        )
        if rc:
            print(f"Hook {args.hookID} destroyed")
        else:
            raise SystemExit(f"Failed destroying hook: {args.hookID}")
    elif args.objectType == "protection":
        rc = astraSDK.protections.destroyProtectiontionpolicy(
            quiet=args.quiet, verbose=args.verbose
        ).main(args.appID, args.protectionID)
        if rc:
            print(f"Protection policy {args.protectionID} destroyed")
        else:
            raise SystemExit(f"Failed destroying protection policy: {args.protectionID}")
    elif args.objectType == "replication":
        if ard.needsattr("replications"):
            ard.replications = astraSDK.replications.getReplicationpolicies().main()
        rc = astraSDK.replications.destroyReplicationpolicy(
            quiet=args.quiet, verbose=args.verbose
        ).main(args.replicationID)
        if rc:
            print(f"Replication policy {args.replicationID} destroyed")
            # The underlying replication schedule(s) (protection policy) must also be deleted
            if ard.needsattr("protections"):
                ard.protections = astraSDK.protections.getProtectionpolicies().main()
            for replication in ard.replications["items"]:
                if replication["id"] == args.replicationID:
                    for protection in ard.protections["items"]:
                        if (
                            protection["appID"] == replication["sourceAppID"]
                            or protection["appID"] == replication["destinationAppID"]
                        ) and protection.get("replicate") == "true":
                            if astraSDK.protections.destroyProtectiontionpolicy(
                                quiet=args.quiet, verbose=args.verbose
                            ).main(protection["appID"], protection["id"]):
                                print(
                                    f"Underlying replication schedule {protection['id']} destroyed"
                                )
                            else:
                                raise SystemExit(
                                    "Failed destroying underlying replication "
                                    + f"schedule: {protection['id']}"
                                )
        else:
            raise SystemExit(f"Failed destroying replication policy: {args.replicationID}")
    elif args.objectType == "script":
        rc = astraSDK.scripts.destroyScript(quiet=args.quiet, verbose=args.verbose).main(
            args.scriptID
        )
        if rc:
            print(f"Script {args.scriptID} destroyed")
        else:
            raise SystemExit(f"Failed destroying script: {args.scriptID}")
    elif args.objectType == "snapshot":
        rc = astraSDK.snapshots.destroySnapshot(quiet=args.quiet, verbose=args.verbose).main(
            args.appID, args.snapshotID
        )
        if rc:
            print(f"Snapshot {args.snapshotID} destroyed")
        else:
            raise SystemExit(f"Failed destroying snapshot: {args.snapshotID}")
    elif args.objectType == "user":
        userDestroyed = False
        roleBindings = astraSDK.rolebindings.getRolebindings().main()
        for rb in roleBindings["items"]:
            if rb["userID"] == args.userID:
                rc = astraSDK.rolebindings.destroyRolebinding(
                    quiet=args.quiet, verbose=args.verbose
                ).main(rb["id"])
                if rc:
                    print(f"User {args.userID} / roleBinding {rb['id']} destroyed")
                    userDestroyed = True
                else:
                    raise SystemExit(
                        f"Failed destroying user {args.userID} with roleBinding {rb['id']}"
                    )
        if not userDestroyed:
            # If we reached this point, it's due to plaidMode == True and bad userID
            parser.error(f"userID {args.userID} not found")
