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


def main(args):
    if args.objectType == "hooks":
        for hook in astraSDK.hooks.getHooks().main(appFilter=args.sourceApp)["items"]:
            rc = astraSDK.hooks.createHook(quiet=args.quiet, verbose=args.verbose).main(
                args.destinationApp,
                hook["name"],
                hook["hookSourceID"],
                hook["stage"],
                hook["action"],
                hook["arguments"],
                hook["matchingCriteria"],
            )
            if rc is False:
                raise SystemExit("astraSDK.hooks.createHook() failed")
    elif args.objectType == "protections":
        for protection in astraSDK.protections.getProtectionpolicies().main(
            appFilter=args.sourceApp
        )["items"]:
            rc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                protection["granularity"],
                protection["backupRetention"],
                protection["snapshotRetention"],
                protection.get("dayOfWeek"),
                protection.get("dayOfMonth"),
                protection.get("hour"),
                protection.get("minute"),
                args.destinationApp,
            )
            if rc is False:
                raise SystemExit("astraSDK.protections.createProtectionpolicy() failed")
