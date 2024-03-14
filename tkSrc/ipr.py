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
from tkSrc import helpers


def doV3Ipr(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    parser,
    ard,
    backup=None,
    snapshot=None,
    filterSelection=None,
    filterSet=None,
):
    if backup:
        if ard.needsattr("backups"):
            ard.backups = astraSDK.k8s.getResources(
                config_context=v3, skip_tls_verify=skip_tls_verify
            ).main("backups")
        iprSourceDict = ard.getSingleDict("backups", "metadata.name", backup, parser)
    elif snapshot:
        if ard.needsattr("snapshots"):
            ard.snapshots = astraSDK.k8s.getResources(
                config_context=v3, skip_tls_verify=skip_tls_verify
            ).main("snapshots")
        iprSourceDict = ard.getSingleDict("snapshots", "metadata.name", snapshot, parser)

    template = helpers.setupJinja("ipr")
    try:
        v3_dict = yaml.safe_load(
            template.render(
                kind=iprSourceDict["kind"],
                iprName=f"{iprSourceDict['kind'].lower()}ipr-{uuid.uuid4()}",
                appArchivePath=iprSourceDict["status"]["appArchivePath"],
                appVaultRef=iprSourceDict["spec"]["appVaultRef"],
                resourceFilter=helpers.prependDump(
                    helpers.createFilterSet(filterSelection, filterSet, None, parser, v3=True),
                    prepend=4,
                ),
            )
        )
        if dry_run == "client":
            print(yaml.dump(v3_dict).rstrip("\n"))
        else:
            astraSDK.k8s.createResource(
                quiet=quiet,
                dry_run=dry_run,
                verbose=verbose,
                config_context=v3,
                skip_tls_verify=skip_tls_verify,
            ).main(
                f"{v3_dict['kind'].lower()}s",
                v3_dict["metadata"]["namespace"],
                v3_dict,
                version="v1",
                group="astra.netapp.io",
            )
    except KeyError as err:
        iprSourceName = backup if backup else snapshot
        parser.error(
            f"{err} key not found in '{iprSourceName}' object, please ensure "
            f"'{iprSourceName}' is a valid backup/snapshot"
        )


def main(args, parser, ard):
    if (args.filterSelection and not args.filterSet) or (
        args.filterSet and not args.filterSelection
    ):
        parser.error("either both or none of --filterSelection and --filterSet should be specified")

    if args.v3:
        doV3Ipr(
            args.v3,
            args.dry_run,
            args.skip_tls_verify,
            args.quiet,
            args.verbose,
            parser,
            ard,
            backup=args.backup,
            snapshot=args.snapshot,
            filterSelection=args.filterSelection,
            filterSet=args.filterSet,
        )
    else:
        rc = astraSDK.apps.restoreApp(quiet=args.quiet, verbose=args.verbose).main(
            args.app,
            backupID=args.backup,
            snapshotID=args.snapshot,
            resourceFilter=helpers.createFilterSet(
                args.filterSelection,
                args.filterSet,
                astraSDK.apps.getAppAssets().main(args.app),
                parser,
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
