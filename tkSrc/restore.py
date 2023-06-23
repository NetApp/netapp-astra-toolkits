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

import astraSDK
import tkSrc


def main(args, parser):
    if (args.filterSelection and not args.filterSet) or (
        args.filterSet and not args.filterSelection
    ):
        parser.error("either both or none of --filterSelection and --filterSet should be specified")
    rc = astraSDK.apps.restoreApp(quiet=args.quiet, verbose=args.verbose).main(
        args.appID,
        backupID=args.backupID,
        snapshotID=args.snapshotID,
        resourceFilter=tkSrc.helpers.createFilterSet(
            args.filterSelection, args.filterSet, astraSDK.apps.getAppAssets().main(args.appID)
        ),
    )
    if rc:
        if args.background:
            print("Restore job submitted successfully")
            print("Background restore flag selected, run 'list apps' to get status")
            return True
        print("Restore job in progress...", end="")
        sys.stdout.flush()
        while True:
            restoreApps = astraSDK.apps.getApps().main()
            state = None
            for restoreApp in restoreApps["items"]:
                if restoreApp["id"] == args.appID:
                    state = restoreApp["state"]
            if state == "restoring":
                print(".", end="")
                sys.stdout.flush()
            elif state == "ready":
                print("Success!")
                break
            elif state == "failed":
                raise SystemExit(f"Restore of app {args.appID} failed!")
            time.sleep(args.pollTimer)
    else:
        raise SystemExit("Submitting restore job failed.")
