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

import os

import astraSDK
from tkSrc import helpers


def downloadAsup(quiet, verbose, config, asupID):
    """Download/copy an auto-support bundle via the API to your local workstation"""
    if rc := astraSDK.asups.downloadAsup(quiet=quiet, verbose=verbose, config=config).main(asupID):
        return rc
    raise SystemExit("astraSDK.asups.downloadAsup() failed")


def downloadV3Asup(v3, dry_run, skip_tls_verify, verbose, asupDict):
    """Download/copy an auto-support bundle via kubectl to your local workstation"""
    context, config_file = tuple(v3.split("@"))
    cpCmd = " ".join(asupDict["status"]["bundleKubectlCpCommand"].split()[1:-1])
    if dry_run:
        raise SystemExit(
            "error: --dry-run not supported with kubectl cp. See 'kubectl cp --help' for usage."
        )
    helpers.run(
        f"kubectl --insecure-skip-tls-verify={skip_tls_verify} --context={context} "
        f"-v={6 if verbose else 0} {cpCmd} {asupDict['metadata']['name']}.7z",
        env={"KUBECONFIG": os.path.expanduser(config_file)} if config_file != "None" else None,
    )


def main(args, ard, config=None):
    if args.objectType == "asup":
        if args.v3:
            if ard.needsattr("asups"):
                ard.asups = astraSDK.k8s.getResources(
                    config_context=args.v3, skip_tls_verify=args.skip_tls_verify
                ).main("autosupportbundles")
            downloadV3Asup(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.verbose,
                ard.getSingleDict("asups", "metadata.name", args.asup),
            )
        else:
            downloadAsup(args.quiet, args.verbose, config, args.asup)
    elif args.objectType == "hooks":
        for hook in astraSDK.hooks.getHooks(config=config).main(appFilter=args.sourceApp)["items"]:
            rc = astraSDK.hooks.createHook(
                quiet=args.quiet, verbose=args.verbose, config=config
            ).main(
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
        for protection in astraSDK.protections.getProtectionpolicies(config=config).main(
            appFilter=args.sourceApp
        )["items"]:
            rc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose, config=config
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
