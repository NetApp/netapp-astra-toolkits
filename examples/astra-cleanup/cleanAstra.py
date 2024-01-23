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

import sys
import time

# A bit of a hack to support both git repo and actoolkit python package use cases
try:
    # If this import succeeds, it's due to the actoolkit package being installed
    import astraSDK
    import toolkit
except ModuleNotFoundError:
    # If actoolkit isn't installed, then we're working within the git repo
    # Add the repo root dir to sys.path and set it as __package__
    # For more info on __package__, see https://peps.python.org/pep-0366/
    sys.path.append(sys.path[0].split("/examples")[0])
    __package__ = "netapp-astra-toolkits"
    import astraSDK
    import toolkit


def runToolkitCmd(cmd, plaid_mode=True):
    if plaid_mode:
        cmd = f"-f {cmd}"
    toolkit.main(argv=cmd.split())


def destroyAllAppBackups(app):
    appBackups = astraSDK.backups.getBackups().main(appFilter=app["id"])
    for appBackup in appBackups["items"]:
        print(f"\t\tDeleting backup:\t{appBackup['name']}")
        astraSDK.backups.destroyBackup(quiet=False).main(app["id"], appBackup["id"])


def destroyAllAppSnapshots(app):
    appSnaps = astraSDK.snapshots.getSnaps().main(appFilter=app["id"])
    for appSnap in appSnaps["items"]:
        print(f"\t\tDeleting snap:\t\t{appSnap['name']}")
        astraSDK.snapshots.destroySnapshot(quiet=False).main(app["id"], appSnap["id"])


def destroyAllAppHooks(app):
    appHooks = astraSDK.hooks.getHooks().main(appFilter=app["id"])
    for appHook in appHooks["items"]:
        print(f"\t\tDeleting hook:\t\t{appHook['name']}")
        astraSDK.hooks.destroyHook(quiet=False).main(app["id"], appHook["id"])


def destroyAppResources(apps):
    for app in apps["items"]:
        print(f"Cleaning up snaps/backups for app:\t{app['name']}")
        destroyAllAppBackups(app)
        destroyAllAppSnapshots(app)
        destroyAllAppHooks(app)


def unmanageAllApps(apps):
    for app in apps["items"]:
        print(f"Unmanaging app:\t\t\t{app['name']}")
        astraSDK.apps.unmanageApp(quiet=False).main(app["id"])


def unmanageAllClusters(clusters):
    for cluster in clusters["items"]:
        print(f"Unmanaging cluster:\t{cluster['name']}")
        runToolkitCmd(f"unmanage cluster {cluster['id']}")


if __name__ == "__main__":
    """This script deletes all snapshots, backups, apps, and then clusters from an astra
    environment.  There is no confirmation provided, so use with caution."""

    # Get the apps, and loop continuously until they're all unmanaged
    apps = astraSDK.apps.getApps().main()
    while len(apps["items"]) > 0:
        destroyAppResources(apps)
        print("--> Sleeping for 30 seconds")
        time.sleep(30)
        unmanageAllApps(apps)
        print("--> Sleeping for 20 seconds")
        time.sleep(20)
        apps = astraSDK.apps.getApps().main()

    # Get the clusters, and loop continuously until they're all unmanaged
    while True:
        clusters = astraSDK.clusters.getClusters().main()
        allUnmanaged = True
        for cluster in clusters["items"]:
            if cluster["managedState"] == "managed":
                allUnmanaged = False
        if allUnmanaged:
            break
        else:
            print("--> Sleeping for 20 seconds")
            time.sleep(20)
            unmanageAllClusters(clusters)
            clusters = astraSDK.clusters.getClusters().main()

    print("ASTRA CLEANED SUCCESSFULLY")
