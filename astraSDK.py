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

import inspect
import os
import sys
import yaml
from termcolor import colored
import requests


class getConfig:
    def __init__(self):

        path = sys.argv[0] or inspect.getfile(getConfig)
        for loc in (
            os.path.realpath(os.path.dirname(path)),
            os.path.join(os.path.expanduser("~"), ".config", "astra-toolkits"),
            "/etc/astra-toolkits",
            os.environ.get("ASTRATOOLKITS_CONF"),
        ):
            configPath = (os.path.join(loc, "config.yaml"))
            try:
                if loc:
                    if os.path.isfile(configPath):
                        with open(configPath, "r") as f:
                            self.conf = yaml.safe_load(f)
                            break
            except IOError:
                pass
            except yaml.YAMLError:
                print("%s not valid YAML" % configPath)
                continue

        for item in ["astra_project", "uid", "headers"]:
            try:
                assert self.conf.get(item) is not None
            except AssertionError:
                print("astra_project is a required field in %s" % configPath)
                sys.exit(3)

        self.base = "https://%s.astra.netapp.io/accounts/%s/" % (
            self.conf.get("astra_project"),
            self.conf.get("uid"),
        )
        self.headers = self.conf.get("headers")

    def main(self):
        return {"base": self.base, "headers": self.headers}


class getApps:
    def __init__(self, quiet=True, discovered=False, source=False, namespace=None):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.clusters = getClusters().main()
        self.discovered = discovered
        self.source = source
        self.namespace = namespace

    def main(self):
        if self.discovered:
            self.endpoint = "topology/v1/apps"
            self.params = {
                "include": "name,id,clusterName,clusterID,namespace,managedState,state"
            }
        else:
            self.endpoint = "k8s/v1/managedApps"
            self.params = {"include": "name,id,clusterName,clusterID,namespace,state"}

        if self.source:
            self.param_string = self.params.get("include")
            self.param_string = self.param_string + ",appDefnSource"
            self.params["include"] = self.param_string

        self.url = self.base + self.endpoint
        self.data = {}

        # This means we were run from the CLI without the -q flag
        # self.quiet = True if the CLI was run with -q or
        # we've been imported and called as a library
        if not self.quiet:
            print()
            print("Listing Apps...")
            print()
            print(colored("API URL: %s" % self.url, "green"))
        try:
            self.ret = requests.get(
                self.url, data=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if not self.quiet:
            print("API HTTP Status Code: %s" % self.ret.status_code)
            print()
        if self.ret.ok:
            self.results = self.ret.json()
            self.apps = {}
            for self.item in self.results["items"]:
                if self.item[1] not in self.apps:
                    self.apps[self.item[1]] = []
                    for self.entry in self.item:
                        if self.entry == self.item[1]:
                            continue
                        else:
                            self.apps[self.item[1]].append(self.entry)
            if self.discovered:
                # filter out system apps and managed apps to get a list of unmanaged user apps
                if self.source:
                    if self.namespace:
                        self.apps_cooked = {
                            k: v
                            for (k, v) in self.apps.items()
                            if v[0] != "trident"
                            and v[0] != "kube-system"
                            and v[3] == self.namespace
                            and v[4] == "unmanaged"
                            and v[6] == self.source
                        }
                    else:
                        self.apps_cooked = {
                            k: v
                            for (k, v) in self.apps.items()
                            if v[0] != "trident"
                            and v[0] != "kube-system"
                            and v[4] == "unmanaged"
                            and v[6] == self.source
                        }
                else:
                    if self.namespace:
                        self.apps_cooked = {
                            k: v
                            for (k, v) in self.apps.items()
                            if v[0] != "trident"
                            and v[0] != "kube-system"
                            and v[3] == self.namespace
                            and v[4] == "unmanaged"
                        }
                    else:
                        self.apps_cooked = {
                            k: v
                            for (k, v) in self.apps.items()
                            if v[0] != "trident"
                            and v[0] != "kube-system"
                            and v[4] == "unmanaged"
                        }
            else:
                if self.source:
                    if self.namespace:
                        self.apps_cooked = {
                            k: v
                            for (k, v) in self.apps.items()
                            if v[3] == self.namespace and v[5] == self.source
                        }
                    else:
                        self.apps_cooked = {
                            k: v for (k, v) in self.apps.items() if v[5] == self.source
                        }
                else:
                    if self.namespace:
                        self.apps_cooked = {
                            k: v
                            for (k, v) in self.apps.items()
                            if v[3] == self.namespace
                        }
                    else:
                        self.apps_cooked = self.apps

            if not self.quiet:
                print("apps:")
                for self.item in self.apps_cooked:
                    print(
                        "\tappName: %s\t appID: %s\t clusterName: %s\t namespace: %s\t state: %s"
                        % (
                            self.apps_cooked[self.item][0],
                            self.item,
                            self.apps_cooked[self.item][1],
                            self.apps_cooked[self.item][3],
                            self.apps_cooked[self.item][4],
                        )
                    )
                print()
            return self.apps_cooked
        else:
            if not self.quiet:
                sys.exit(1)
            else:
                return False


class getBackups:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.apps = getApps().main()

    def main(self):
        self.backups = {}
        for self.app in self.apps:
            self.endpoint = "k8s/v1/managedApps/%s/appBackups" % self.app  # appID
            self.url = self.base + self.endpoint

            self.data = {}
            self.params = {"include": "name,id,state,metadata"}

            if not self.quiet:
                print()
                print("Listing Backups for %s %s" % (self.app, self.apps[self.app][0]))
                print()
                print(colored("API URL: %s" % self.url, "green"))
            try:
                self.ret = requests.get(
                    self.url, data=self.data, headers=self.headers, params=self.params
                )
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            if not self.quiet:
                print("API HTTP Status Code: %s" % self.ret.status_code)
                print()
            if self.ret.ok:
                self.results = self.ret.json()
                self.backups[self.app] = {}
                for item in self.results["items"]:
                    self.backupName = item[0]
                    self.backupID = item[1]
                    self.backupState = item[2]
                    self.backupTimeStamp = item[3].get("creationTimestamp")[:-1]
                    if self.backupName not in self.backups[self.app]:
                        self.backups[self.app][self.backupName] = [
                            self.backupID,
                            self.backupState,
                            self.backupTimeStamp,
                        ]
                if not self.quiet:
                    print("Backups:")
                    for self.item in self.backups[self.app]:
                        print(
                            "\tbackupName: %s\t backupID: %s\t backupState: %s"
                            % (
                                self.item,
                                self.backups[self.app][self.item][0],
                                self.backups[self.app][self.item][1],
                            )
                        )
                        print()
            else:
                continue
        if not self.quiet:
            print(self.backups)
        else:
            return self.backups


class takeBackup:
    def __init__(self, output=True):
        self.output = output
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.headers["accept"] = "application/astra-appBackup+json"
        self.headers["Content-Type"] = "application/astra-appBackup+json"

    def main(self, appID, backupName):
        self.endpoint = "k8s/v1/managedApps/%s/appBackups" % appID
        self.url = self.base + self.endpoint
        self.params = {}
        self.data = {
            "type": "application/astra-appBackup",
            "version": "1.0",
            "name": backupName,
        }
        try:
            self.ret = requests.post(
                self.url, json=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if self.ret.ok:
            self.results = self.ret.json()
            if self.output:
                print(self.results)
            else:
                return self.results.get("id") or True
        else:
            if self.output:
                print(self.ret.status_code)
                print(self.ret.reason)
            else:
                return False


class cloneApp:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig.getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/astra-managedApp+json"

    def main(
        self,
        cloneName,
        backupID,
        clusterID,
        sourceClusterID,
        namespace,
        sourceAppID=None,
    ):
        self.endpoint = "k8s/v1/managedApps"
        self.url = self.base + self.endpoint
        self.params = {}
        self.data = {
            "type": "application/astra-managedApp",
            "version": "1.0",
            "name": cloneName,
            "backupID": backupID,
            "clusterID": clusterID,
            "sourceClusterID": sourceClusterID,
            "namespace": namespace,
        }
        if sourceAppID:
            self.data["sourceAppID"] = sourceAppID

        try:
            self.ret = requests.post(
                self.url, json=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        if self.ret.ok:
            self.results = self.ret.json()
            if not self.quiet:
                print(self.results)
            else:
                return self.results
        else:
            if not self.quiet:
                print(self.ret.status_code)
                print(self.ret.reason)
                sys.exit(1)
            else:
                return False


class getClusters:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")

    def main(self):
        self.endpoint = "topology/v1/apps"
        self.url = self.base + self.endpoint

        self.data = {}
        self.params = {"include": "clusterName,clusterID,clusterType"}

        if not self.quiet:
            print()
            print("Listing clusters...")
            print()
            print(colored("API URL: %s" % self.url, "green"))
            print()
        try:
            self.ret = requests.get(
                self.url, data=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if not self.quiet:
            print("API HTTP Status Code: %s" % self.ret.status_code)
            print()
        if self.ret.ok:
            self.results = self.ret.json()
            self.clusters = {}
            for item in self.results["items"]:
                if item[1] not in self.clusters:
                    self.clusters[item[1]] = [item[0], item[2]]
            if not self.quiet:
                print("clusters:")
                for item in self.clusters:
                    print(
                        "\tclusterName: %s\t clusterID: %s\tclusterType: %s"
                        % (self.clusters[item][0], item, self.clusters[item][1])
                    )
                print()
            return self.clusters
        else:
            if not self.quiet:
                sys.exit(1)
            else:
                return False


class createProtectionpolicy:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.headers["accept"] = "application/astra-schedule+json"
        self.headers["Content-Type"] = "application/astra-schedule+json"

    def main(
        self,
        granularity,
        backupRetention,
        snapshotRetention,
        dayOfWeek,
        dayOfMonth,
        hour,
        minute,
        appID,
    ):
        self.endpoint = "k8s/v1/managedApps/%s/schedules" % appID
        self.url = self.base + self.endpoint
        self.params = {}
        self.data = {
            "type": "application/astra-schedule",
            "version": "1.0",
            "backupRetention": backupRetention,
            "dayOfMonth": dayOfMonth,
            "dayOfWeek": dayOfWeek,
            "enabled": "true",
            "granularity": granularity,
            "hour": hour,
            "minute": minute,
            "name": "%s schedule" % granularity,
            "snapshotRetention": snapshotRetention,
        }
        try:
            self.ret = requests.post(
                self.url, json=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if self.ret.ok:
            self.results = self.ret.json()
            if not self.quiet:
                print(self.results)
                return True
            else:
                return True
        else:
            if not self.quiet:
                print(self.ret.status_code)
                print(self.ret.reason)
                return False
            else:
                return False


class manageApp:
    def __init__(self, appID, quiet=True):
        self.quiet = quiet
        self.appID = appID
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/managedApp+json"

    def main(self):
        self.endpoint = "k8s/v1/managedApps"
        self.url = self.base + self.endpoint
        self.params = {}
        self.data = {
            "type": "application/astra-managedApp",
            "version": "1.1",
            "id": self.appID,
        }
        try:
            self.ret = requests.post(
                self.url, json=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if self.ret.ok:
            self.results = self.ret.json()
            if not self.quiet:
                print(self.results)
            else:
                return True
        else:
            if not self.quiet:
                print(self.ret.status_code)
                print(self.ret.reason)
            else:
                return False


class takeSnap:
    def __init__(self, output=True):
        self.output = output
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.headers["accept"] = "application/astra-appSnap+json"
        self.headers["Content-Type"] = "application/astra-appSnap+json"

    def main(self, appID, snapName):
        self.endpoint = "k8s/v1/managedApps/%s/appSnaps" % appID
        self.url = self.base + self.endpoint
        print(self.url)
        self.params = {}
        self.data = {
            "type": "application/astra-appSnap",
            "version": "1.0",
            "name": snapName,
        }
        try:
            self.ret = requests.post(
                self.url, json=self.data, headers=self.headers, params=self.params
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if self.ret.ok:
            self.results = self.ret.json()
            if self.output:
                print(self.results)
            else:
                return self.results.get("id") or True
        else:
            if self.output:
                print(self.ret.status_code)
                print(self.ret.reason)
            else:
                return False


class getSnaps:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.apps = getApps().main()

    def main(self):
        self.snaps = {}
        for self.app in self.apps:
            self.endpoint = "k8s/v1/managedApps/%s/appSnaps" % self.app
            self.url = self.base + self.endpoint

            self.data = {}
            self.params = {"include": "name,id,state"}

            if not self.quiet:
                print()
                print("Listing Snapshots for %s" % self.app)
                print()
                print(colored("API URL: %s" % self.url, "green"))
                print(colored("API Method: GET", "green"))
                print(colored("API Headers: %s" % self.headers, "green"))
                print(colored("API data: %s" % self.data, "green"))
                print(colored("API params: %s" % self.params, "green"))
                print()
                time.sleep(1)
                print("Making API Call", end="", flush=True)
                for i in range(3):
                    print(".", end="", flush=True)
                    time.sleep(1)
                print()
            try:
                self.ret = requests.get(
                    self.url, data=self.data, headers=self.headers, params=self.params
                )
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            if not self.quiet:
                print("API HTTP Status Code: %s" % self.ret.status_code)
                print()
            if self.ret.ok:
                self.results = self.ret.json()
                self.snaps[self.app] = {}
                for item in self.results["items"]:
                    self.appName = item[0]
                    self.snapID = item[1]
                    self.snapState = item[2]
                    if self.appName not in self.snaps[self.app]:
                        self.snaps[self.app][self.appName] = [
                            self.snapID,
                            self.snapState,
                        ]
                if not self.quiet:
                    print("Snapshots:")
                    for self.item in self.snaps[self.app]:
                        print(
                            "\tsnapshotName: %s\t snapshotID: %s\t snapshotState: %s"
                            % (
                                self.item,
                                self.snaps[self.app][self.item][0],
                                self.snaps[self.app][self.item][1],
                            )
                        )
                        print()
            else:
                continue

        if not self.quiet:
            print(self.snaps)
        else:
            return self.snaps
