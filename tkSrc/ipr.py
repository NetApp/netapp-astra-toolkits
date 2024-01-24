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

import sys
import time
import uuid
import yaml

import astraSDK
import tkSrc


def main(args, parser, ard):
    if (args.filterSelection and not args.filterSet) or (
        args.filterSet and not args.filterSelection
    ):
        parser.error("either both or none of --filterSelection and --filterSet should be specified")

    if args.v3:
        if args.backup:
            if ard.needsattr("backups"):
                ard.backups = astraSDK.k8s.getResources(config_context=args.v3).main("backups")
            iprSourceDict = ard.getSingleDict("backups", "metadata.name", args.backup, parser)
        elif args.snapshot:
            if ard.needsattr("snapshots"):
                ard.snapshots = astraSDK.k8s.getResources(config_context=args.v3).main("snapshots")
            iprSourceDict = ard.getSingleDict("snapshots", "metadata.name", args.snapshot, parser)

        template = tkSrc.helpers.setupJinja(args.subcommand)
        try:
            v3_dict = yaml.safe_load(
                template.render(
                    kind=iprSourceDict["kind"],
                    iprName=f"{iprSourceDict['kind'].lower()}ipr-{uuid.uuid4()}",
                    appArchivePath=iprSourceDict["status"]["appArchivePath"],
                    appVaultRef=iprSourceDict["spec"]["appVaultRef"],
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
        except KeyError as err:
            iprSourceName = args.backup if args.backup else args.snapshot
            parser.error(
                f"{err} key not found in '{iprSourceName}' object, please ensure "
                f"'{iprSourceName}' is a valid backup/snapshot"
            )

    else:
        rc = astraSDK.apps.restoreApp(quiet=args.quiet, verbose=args.verbose).main(
            args.app,
            backupID=args.backup,
            snapshotID=args.snapshot,
            resourceFilter=tkSrc.helpers.createFilterSet(
                args.filterSelection, args.filterSet, astraSDK.apps.getAppAssets().main(args.app)
            ),
        )
        if rc:
            if args.background:
                print("In-Place-Restore job submitted successfully")
                print("Background flag selected, run 'list apps' to get status")
                return True
            print("In-Place-Restore job in progress", end="")
            sys.stdout.flush()
            while True:
                restoreApps = astraSDK.apps.getApps().main()
                state = None
                for restoreApp in restoreApps["items"]:
                    if restoreApp["id"] == args.app:
                        state = restoreApp["state"]
                if state == "restoring":
                    print(".", end="")
                    sys.stdout.flush()
                elif state == "ready":
                    print("Success!")
                    break
                elif state == "failed":
                    raise SystemExit(f"Restore of app {args.app} failed!")
                time.sleep(args.pollTimer)
        else:
            raise SystemExit("Submitting restore job failed.")
