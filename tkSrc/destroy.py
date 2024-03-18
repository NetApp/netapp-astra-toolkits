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

import astraSDK


def main(args, parser, ard):
    if args.objectType == "backup":
        if args.v3:
            rc = astraSDK.k8s.destroyResource(
                quiet=args.quiet,
                dry_run=args.dry_run,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main("backups", args.backup)
        else:
            rc = astraSDK.backups.destroyBackup(quiet=args.quiet, verbose=args.verbose).main(
                args.app, args.backup
            )
            if rc:
                print(f"Backup {args.backup} destroyed")
            else:
                raise SystemExit(f"Failed destroying backup: {args.backup}")
    elif args.objectType == "cluster":
        if ard.needsattr("clusters"):
            ard.clusters = astraSDK.clusters.getClusters().main()
        cluster = ard.getSingleDict("clusters", "id", args.cluster, parser)
        rc = astraSDK.clusters.deleteCluster(quiet=args.quiet, verbose=args.verbose).main(
            cluster["id"], cluster["cloudID"]
        )
        if not rc:
            raise SystemExit(f"Failed destroying cluster: {args.cluster}")
    elif args.objectType == "credential" or args.objectType == "secret":
        if args.v3:
            astraSDK.k8s.destroySecret(
                quiet=args.quiet,
                dry_run=args.dry_run,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main(args.credential)
        else:
            rc = astraSDK.credentials.destroyCredential(
                quiet=args.quiet, verbose=args.verbose
            ).main(args.credential)
            if rc:
                print(f"Credential {args.credential} destroyed")
            else:
                raise SystemExit(f"Failed destroying credential: {args.credential}")
    elif args.objectType == "group":
        if ard.needsattr("rolebindings"):
            ard.rolebindings = astraSDK.rolebindings.getRolebindings().main()
        rb = ard.getSingleDict("rolebindings", "groupID", args.groupID, parser)
        if astraSDK.rolebindings.destroyRolebinding(quiet=args.quiet, verbose=args.verbose).main(
            rb["id"]
        ):
            print(f"RoleBinding {rb['id']} destroyed")
            if astraSDK.groups.destroyGroup(quiet=args.quiet, verbose=args.verbose).main(
                args.groupID
            ):
                print(f"Group {args.groupID} destroyed")
            else:
                raise SystemExit(f"Failed destroying group {args.groupID}")
        else:
            raise SystemExit(f"Failed destroying group {args.groupID} with roleBinding {rb['id']}")
    elif args.objectType == "hook" or args.objectType == "exechook":
        if args.v3:
            rc = astraSDK.k8s.destroyResource(
                quiet=args.quiet,
                dry_run=args.dry_run,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main("exechooks", args.hook)
        else:
            rc = astraSDK.hooks.destroyHook(quiet=args.quiet, verbose=args.verbose).main(
                args.app, args.hook
            )
            if rc:
                print(f"Hook {args.hook} destroyed")
            else:
                raise SystemExit(f"Failed destroying hook: {args.hook}")
    elif args.objectType == "ldap":
        ard.settings = astraSDK.settings.getSettings().main()
        ldapSetting = ard.getSingleDict("settings", "name", "astra.account.ldap", parser)
        if astraSDK.settings.destroyLdap(quiet=args.quiet, verbose=args.verbose).main(
            ldapSetting["id"]
        ):
            if ldapSetting["currentConfig"].get("credentialId"):
                rc = astraSDK.credentials.destroyCredential(
                    quiet=args.quiet, verbose=args.verbose
                ).main(ldapSetting["currentConfig"]["credentialId"])
                if rc:
                    print(f"Credential {ldapSetting['currentConfig']['credentialId']} destroyed")
                else:
                    raise SystemExit(
                        "Failed destroying credential: "
                        f"{ldapSetting['currentConfig']['credentialId']}"
                    )
        else:
            raise SystemExit(f"Failed destroying ldap: {ldapSetting['id']}")
    elif args.objectType == "protection" or args.objectType == "schedule":
        if args.v3:
            rc = astraSDK.k8s.destroyResource(
                quiet=args.quiet,
                dry_run=args.dry_run,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main("schedules", args.protection)
        else:
            rc = astraSDK.protections.destroyProtectiontionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(args.app, args.protection)
            if rc:
                print(f"Protection policy {args.protection} destroyed")
            else:
                raise SystemExit(f"Failed destroying protection policy: {args.protection}")
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
        if args.v3:
            rc = astraSDK.k8s.destroyResource(
                quiet=args.quiet,
                dry_run=args.dry_run,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main("snapshots", args.snapshot)
        else:
            rc = astraSDK.snapshots.destroySnapshot(quiet=args.quiet, verbose=args.verbose).main(
                args.app, args.snapshot
            )
            if rc:
                print(f"Snapshot {args.snapshot} destroyed")
            else:
                raise SystemExit(f"Failed destroying snapshot: {args.snapshot}")
    elif args.objectType == "user":
        if ard.needsattr("users"):
            ard.users = astraSDK.users.getUsers().main()
        if ard.needsattr("rolebindings"):
            ard.rolebindings = astraSDK.rolebindings.getRolebindings().main()
        user = ard.getSingleDict("users", "id", args.userID, parser)
        rb = ard.getSingleDict("rolebindings", "userID", args.userID, parser)
        if astraSDK.rolebindings.destroyRolebinding(quiet=args.quiet, verbose=args.verbose).main(
            rb["id"]
        ):
            print(f"RoleBinding {rb['id']} destroyed")
        else:
            raise SystemExit(f"Failed destroying user {args.userID} with roleBinding {rb['id']}")
        # Only LDAP users also need to be destroyed
        if user["authProvider"] == "ldap":
            if astraSDK.users.destroyUser(quiet=args.quiet, verbose=args.verbose).main(args.userID):
                print(f"User {args.userID} destroyed")
            else:
                raise SystemExit(f"Failed destroying user {args.userID}")
        else:
            print(f"User {args.userID} destroyed")
