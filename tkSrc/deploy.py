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
import os
from datetime import datetime, timedelta


import astraSDK
from tkSrc import create, helpers, manage


def deployHelm(
    chart,
    appName,
    namespace,
    setValues,
    fileValues,
    bucket,
    verbose,
    quiet,
    v3=False,
    dry_run=None,
    skip_tls_verify=False,
):
    """Deploy a helm chart <chart>, naming the app <appName> into <namespace>"""
    if v3:
        context, config_file = tuple(v3.split("@"))
        contextStr = f" --kube-context={context}"
        configFileStr = (
            "" if config_file == "None" else f" --kubeconfig={os.path.expanduser(config_file)}"
        )
        dryRunStr = f" --dry-run={dry_run}" if dry_run else ""
    else:
        v3 = None
        contextStr, configFileStr, dryRunStr = "", "", ""

    setStr = helpers.createHelmStr("set", setValues)
    valueStr = helpers.createHelmStr("values", fileValues)
    cluster_namespaces = astraSDK.k8s.getNamespaces(
        config_context=v3, skip_tls_verify=skip_tls_verify
    ).main(systemNS=[])
    if namespace in [n["metadata"]["name"] for n in cluster_namespaces["items"]]:
        raise SystemExit(f"Namespace {namespace} already exists!")

    helpers.run(
        f"helm install{configFileStr}{contextStr}{dryRunStr} {appName} "
        f"-n {namespace} --create-namespace {chart}{setStr}{valueStr}"
    )

    if v3:
        if dry_run == "client":
            print("---")
        manage.manageV3App(v3, dry_run, skip_tls_verify, quiet, verbose, appName, namespace)
        backupRetention = "1"
        snapshotRetention = "1"
        minute = "0"
        protectionData = {
            "hourly": {"dayOfWeek": "", "dayOfMonth": "", "hour": ""},
            "daily": {"dayOfWeek": "", "dayOfMonth": "", "hour": "2"},
            "weekly": {"dayOfWeek": "0", "dayOfMonth": "", "hour": "2"},
            "monthly": {"dayOfWeek": "", "dayOfMonth": "1", "hour": "2"},
        }
        for granularity in protectionData.keys():
            if dry_run == "client":
                print("---")
            create.createV3Protection(
                v3,
                dry_run,
                skip_tls_verify,
                quiet,
                verbose,
                appName,
                bucket,
                granularity,
                backupRetention,
                snapshotRetention,
                minute,
                protectionData[granularity]["hour"],
                protectionData[granularity]["dayOfWeek"],
                protectionData[granularity]["dayOfMonth"],
            )
    else:
        nsObj = astraSDK.namespaces.getNamespaces(verbose=verbose)
        print("Waiting for Astra to discover the namespace", end="")
        sys.stdout.flush()

        appID = ""
        while not appID:
            # It takes Astra some time to realize new apps have been installed
            time.sleep(3)
            print(".", end="")
            sys.stdout.flush()
            namespaces = nsObj.main()
            # Cycle through the apps and see if one matches our new namespace
            for ns in namespaces["items"]:
                # Check to make sure our namespace name matches, it's in a discovered state,
                # and that it's a recently created namespace (less than 10 minutes old)
                if (
                    ns["name"] == namespace
                    and ns["namespaceState"] == "discovered"
                    and (
                        datetime.utcnow()
                        - datetime.strptime(
                            ns["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ"
                        )
                    )
                    < timedelta(minutes=10)
                ):
                    print(" Namespace discovered!")
                    sys.stdout.flush()
                    time.sleep(3)
                    print(f"Managing app: {ns['name']}.", end="")
                    sys.stdout.flush()
                    rc = astraSDK.apps.manageApp(verbose=verbose).main(
                        ns["name"], ns["name"], ns["clusterID"]
                    )
                    if rc:
                        appID = rc["id"]
                        print(" Success!")
                        sys.stdout.flush()
                        break
                    else:
                        sys.stdout.flush()
                        print("\nERROR managing app, trying one more time:")
                        rc = astraSDK.apps.manageApp(quiet=quiet, verbose=verbose).main(
                            ns["name"], ns["name"], ns["clusterID"]
                        )
                        if rc:
                            appID = rc["id"]
                            print("Success!")
                            break
                        else:
                            raise SystemExit("Error managing app")

        # Create a protection policy on that namespace (using its appID)
        time.sleep(5)
        backupRetention = "1"
        snapshotRetention = "1"
        minute = "0"
        cpp = astraSDK.protections.createProtectionpolicy(quiet=quiet)
        cppData = {
            "hourly": {"dayOfWeek": "*", "dayOfMonth": "*", "hour": "*"},
            "daily": {"dayOfWeek": "*", "dayOfMonth": "*", "hour": "2"},
            "weekly": {"dayOfWeek": "0", "dayOfMonth": "*", "hour": "2"},
            "monthly": {"dayOfWeek": "*", "dayOfMonth": "1", "hour": "2"},
        }
        for period in cppData:
            print(f"Setting {period} protection policy on {appID}")
            dayOfWeek = cppData[period]["dayOfWeek"]
            dayOfMonth = cppData[period]["dayOfMonth"]
            hour = cppData[period]["hour"]
            cppRet = cpp.main(
                period,
                backupRetention,
                snapshotRetention,
                dayOfWeek,
                dayOfMonth,
                hour,
                minute,
                appID,
            )
            if cppRet is False:
                raise SystemExit(f"cpp.main({period}...) returned False")


def main(args, parser, ard):
    if args.objectType == "acp":
        if args.v3:
            # Ensure the trident orchestrator is already running
            torc = astraSDK.k8s.getClusterResources(
                quiet=args.quiet,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main("tridentorchestrators")
            if torc is None or len(torc["items"]) == 0:
                parser.error("trident operator not found on current Kubernetes context")
            elif len(torc["items"]) > 1:
                parser.error("multiple trident operators found on current Kubernetes context")
            # Handle the registry secret
            if not args.regCred:
                cred = astraSDK.k8s.createRegCred(
                    quiet=args.quiet,
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                    config_context=args.v3,
                    skip_tls_verify=args.skip_tls_verify,
                ).main(registry=args.registry)
                if not cred:
                    raise SystemExit("astraSDK.k8s.createRegCred() failed")
                args.regCred = cred["metadata"]["name"]
            else:
                if ard.needsattr("credentials"):
                    ard.credentials = astraSDK.k8s.getSecrets(
                        config_context=args.v3, skip_tls_verify=args.skip_tls_verify
                    ).main(namespace="trident")
                cred = ard.getSingleDict("credentials", "metadata.name", args.regCred, parser)
            # Handle default registry
            if not args.registry:
                try:
                    args.registry = next(
                        iter(
                            json.loads(
                                base64.b64decode(cred["data"][".dockerconfigjson"]).decode()
                            )["auths"].keys()
                        )
                    )
                except KeyError as err:
                    parser.error(
                        f"{args.regCred} does not appear to be a Docker secret: {err} key not found"
                    )
            # Create the patch spec
            torc_name = torc["items"][0]["metadata"]["name"]
            torc_version = torc["items"][0]["status"]["version"][1:]
            torc_spec = {"spec": torc["items"][0]["spec"]}
            torc_spec["spec"]["enableACP"] = True
            torc_spec["spec"]["acpImage"] = f"{args.registry}/astra/trident-acp:{torc_version}"
            torc_spec["spec"]["imagePullSecrets"] = [args.regCred]
            # Make the update
            torc_update = astraSDK.k8s.updateClusterResource(
                quiet=args.quiet,
                dry_run=args.dry_run,
                verbose=args.verbose,
                config_context=args.v3,
                skip_tls_verify=args.skip_tls_verify,
            ).main("tridentorchestrators", torc_name, torc_spec)
            if torc_update:
                print(f"tridentorchestrator.trident.netapp.io/{torc_name} edited")
            else:
                raise SystemExit("astraSDK.k8s.updateClusterResource() failed")
        else:
            parser.error(
                "'deploy acp' is currently only supported as a --v3 command, please re-run with "
                "--v3 and an optional context, kubeconfig_file, or context@kubeconfig_file mapping"
            )
    elif args.objectType == "chart":
        if not hasattr(args, "bucket"):
            args.bucket = None
        if args.v3:
            if ard.needsattr("buckets"):
                ard.buckets = astraSDK.k8s.getResources(
                    config_context=args.v3, skip_tls_verify=args.skip_tls_verify
                ).main("appvaults")
            if args.bucket is None:
                args.bucket = ard.getSingleDict("buckets", "status.state", "available", parser)[
                    "metadata"
                ]["name"]
        deployHelm(
            args.chart,
            helpers.isRFC1123(args.app, parser=parser),
            args.namespace,
            args.set,
            args.values,
            args.bucket,
            args.verbose,
            args.quiet,
            v3=args.v3,
            dry_run=args.dry_run,
            skip_tls_verify=args.skip_tls_verify,
        )
