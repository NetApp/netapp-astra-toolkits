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

import json
import kubernetes
import sys
import time
from datetime import datetime, timedelta


import astraSDK
import tkSrc


def doDeploy(chart, appName, namespace, setValues, fileValues, verbose, quiet):
    """Deploy a helm chart <chart>, naming the app <appName> into <namespace>"""

    setStr = tkSrc.helpers.createHelmStr("set", setValues)
    valueStr = tkSrc.helpers.createHelmStr("values", fileValues)

    nsObj = astraSDK.namespaces.getNamespaces(verbose=verbose)
    retval = tkSrc.helpers.run("kubectl get ns -o json", captureOutput=True)
    retvalJSON = json.loads(retval)
    for item in retvalJSON["items"]:
        if item["metadata"]["name"] == namespace:
            raise SystemExit(f"Namespace {namespace} already exists!")
    tkSrc.helpers.run(f"kubectl create namespace {namespace}")
    tkSrc.helpers.run(f"kubectl config set-context --current --namespace={namespace}")

    # If we're deploying gitlab, we need to ensure at least a premium storageclass
    # for postgresql and gitaly
    if chart.split("/")[1] == "gitlab":
        pgStorageClass = None
        scMapping = [
            ["standard-rwo", "premium-rwo"],
            ["netapp-cvs-perf-standard", "netapp-cvs-perf-premium"],
            ["azurefile", "azurefile-premium"],
            ["azurefile-csi", "azurefile-csi-premium"],
            ["managed", "managed-premium"],
            ["managed-csi", "managed-csi-premium"],
        ]
        configuration = kubernetes.config.load_kube_config()
        with kubernetes.client.ApiClient(configuration) as api_client:
            api_instance = kubernetes.client.StorageV1Api(api_client)
            api_response = api_instance.list_storage_class()
            for i in api_response.items:
                if (
                    i.metadata.annotations.get("storageclass.kubernetes.io/is-default-class")
                    == "true"
                ):
                    for sc in scMapping:
                        if i.metadata.name == sc[0]:
                            pgStorageClass = sc[1]
        if pgStorageClass:
            setStr += f" --set postgresql.global.storageClass={pgStorageClass}"
            setStr += f" --set gitlab.gitaly.persistence.storageClass={pgStorageClass}"

    tkSrc.helpers.run(f"helm install {appName} {chart}{setStr}{valueStr}")
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
                    - datetime.strptime(ns["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ")
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
    cpp = astraSDK.protections.createProtectionpolicy(quiet=True)
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


def main(args):
    doDeploy(
        args.chart,
        tkSrc.helpers.isRFC1123(args.app),
        args.namespace,
        args.set,
        args.values,
        args.verbose,
        args.quiet,
    )
