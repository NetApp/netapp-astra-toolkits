#!/usr/bin/env python
"""
   Copyright 2021 NetApp, Inc

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
import time


def destroyAllAppBackups(app):
    appBackups = astraSDK.getBackups().main(appFilter=app["id"])
    for appBackup in appBackups["items"]:
        print(f"\t\tDeleting backup:\t{appBackup['name']}")
        astraSDK.destroyBackup(quiet=False).main(app["id"], appBackup["id"])


def destroyAllAppSnapshots(app):
    appSnaps = astraSDK.getSnaps().main(appFilter=app["id"])
    for appSnap in appSnaps["items"]:
        print(f"\t\tDeleting snap:\t\t{appSnap['name']}")
        astraSDK.destroySnapshot(quiet=False).main(app["id"], appSnap["id"])


def destroyAllAppHooks(app):
    appHooks = astraSDK.getHooks().main(appFilter=app["id"])
    for appHook in appHooks["items"]:
        print(f"\t\tDeleting hook:\t\t{appHook['name']}")
        astraSDK.destroyHook(quiet=False).main(app["id"], appHook["id"])


def destroyAppResources(apps):
    for app in apps["items"]:
        print(f"Cleaning up snaps/backups for app:\t{app['name']}")
        destroyAllAppBackups(app)
        destroyAllAppSnapshots(app)
        destroyAllAppHooks(app)


def unmanageAllApps(apps):
    for app in apps["items"]:
        print(f"Unmanaging app:\t\t\t{app['name']}")
        astraSDK.unmanageApp(quiet=False).main(app["id"])


def unmanageAllClusters(clusters):
    for cluster in clusters["items"]:
        print(f"Unmanaging cluster:\t{cluster['name']}")
        astraSDK.unmanageCluster(quiet=False).main(cluster["id"])


if __name__ == "__main__":
    """This script deletes all snapshots, backups, apps, and then clusters from an astra
    environment.  There is no confirmation provided, so use with caution."""
    # self.headers["ForceDelete"] = "true"

    # Get the apps, and loop continuously until they're all unmanaged
    apps = astraSDK.getApps().main()
    while len(apps["items"]) > 0:
        destroyAppResources(apps)
        print("--> Sleeping for 30 seconds")
        time.sleep(30)
        unmanageAllApps(apps)
        print("--> Sleeping for 20 seconds")
        time.sleep(20)
        apps = astraSDK.getApps().main()

    # Get the clusters, and loop continuously until they're all unmanaged
    while True:
        clusters = astraSDK.getClusters().main()
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
            clusters = astraSDK.getClusters().main()

    print("ASTRA CLEANED SUCCESSFULLY")
