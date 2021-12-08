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
from tabulate import tabulate
from termcolor import colored
import requests
from urllib3 import disable_warnings


class getConfig:
    """In order to make API calls to Astra Control we need to know which Astra Control instance
    to connect to, and the credentials to make calls.  This info is found in config.yaml,
    which we search for in the following four places:
    1) The directory that toolkit.py in located in
    2) ~/.config/astra-toolkits/
    3) /etc/astra-toolkits/
    4) The directory pointed to by the shell env var ASTRATOOLKITS_CONF

    Note that astra_project is used to construct an URL assuming it will be
    Astra Control Service.  This will need to get modified in the future to
    handle arbitrary Astra Control Center URLs, and probably to handle self signed SSL
    certs as well.
    """

    def __init__(self):
        path = sys.argv[0] or inspect.getfile(getConfig)
        self.conf = None
        for loc in (
            os.path.realpath(os.path.dirname(path)),
            os.path.join(os.path.expanduser("~"), ".config", "astra-toolkits"),
            "/etc/astra-toolkits",
            os.environ.get("ASTRATOOLKITS_CONF"),
        ):
            # loc could be None, which would blow up os.path.join()
            if loc:
                configFile = os.path.join(loc, "config.yaml")
            else:
                continue
            try:
                if os.path.isfile(configFile):
                    with open(configFile, "r") as f:
                        self.conf = yaml.safe_load(f)
                        break
            except IOError:
                continue
            except yaml.YAMLError:
                print("%s not valid YAML" % configFile)
                continue

        if self.conf is None:
            print("config.yaml not found.")
            sys.exit(4)

        for item in ["astra_project", "uid", "headers"]:
            try:
                assert self.conf.get(item) is not None
            except AssertionError:
                print("astra_project is a required field in %s" % configFile)
                sys.exit(3)

        if "." in self.conf.get("astra_project"):
            self.base = "https://%s/accounts/%s/" % (
                self.conf.get("astra_project"),
                self.conf.get("uid"),
            )
        else:
            self.base = "https://%s.astra.netapp.io/accounts/%s/" % (
                self.conf.get("astra_project"),
                self.conf.get("uid"),
            )
        self.headers = self.conf.get("headers")

        if self.conf.get("verifySSL") is False:
            disable_warnings()
            self.verifySSL = False
        else:
            self.verifySSL = True

    def main(self):
        return {
            "base": self.base,
            "headers": self.headers,
            "verifySSL": self.verifySSL,
        }


class SDKCommon:
    def __init__(self):
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")

    def apicall(self, method, url, data, headers, params, verify):
        """Make a call using the requests module.
        method can be get, put, post, patch, or delete"""
        try:
            r = getattr(requests, method)
        except AttributeError as e:
            raise SystemExit(e)
        try:
            ret = r(url, json=data, headers=headers, params=params, verify=verify)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        return ret

    def jsonifyResults(self, requestsObject):
        try:
            results = requestsObject.json()
        except ValueError as e:
            print("response contained invalid JSON: %s" % e)
            results = None
        return results


class getApps(SDKCommon):
    """List all apps known to Astra.

    Note that there is an API endpoint that will just list managedApps.  However
    it has the same return value as topology/v1/apps when filtering for
    managedState="managed"

    One thing this class won't do is list all of the managed and unmanaged apps.
    """

    def __init__(self, quiet=True, verbose=False, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__()

    def main(self, discovered=False, source=None, namespace=None, cluster=None):
        """discovered: True: show unmanaged apps False: show managed apps
        source: Filter by the app source field.  eg: helm, namespace
        namespace: Filter by the namespace the app is in
        cluster: Filter by a specific k8s cluster"""
        endpoint = "topology/v1/apps"
        params = {
            "include": "name,id,clusterName,clusterID,namespace,state,managedState,appDefnSource"
        }
        url = self.base + endpoint
        data = {}

        if self.verbose:
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: GET", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            """
            "name,id,clusterName,clusterID,namespace,state,managedState,appDefnSource"
            self.results = {'items':
                [['kube-system', '65ae3322-a1d1-4287-8d01-a3180e7d4ff4',
                  'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                  'kube-system', 'running', 'unmanaged', 'other'],
                 ['trident', '90995ad0-62c6-40c4-a5e3-57727b272385',
                  'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                  'trident', 'running', 'unmanaged', 'other'],
                 ['kube-system', 'b6356386-29b6-4790-abe9-cfe76276e1fa',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'kube-system', 'running', 'unmanaged', 'other'],
                 ['trident', '9af1931d-da02-4662-824c-71bc32cfa576',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'trident', 'running', 'unmanaged', 'other'],
                 ['jp3k', '739e7b1f-a71a-42bd-ac6f-db3ff9131133',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'jp3k', 'running', 'unmanaged', 'namespace'],
                 ['wp-mariadb', '697d2a64-61f0-4958-b746-13248be6e6a1',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'jp3k', 'running', 'managed', 'helm'],
                 ['wp-wordpress', 'ee7e683c-7532-4f79-9c4b-3e26d8ece391',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'jp3k', 'running', 'unmanaged', 'helm']],
                            'metadata': {}}
            """
            apps = {}
            for item in results.get("items"):
                # make item[1] the key in self.apps
                if item[1] not in apps:
                    appID = item.pop(1)
                    apps[appID] = item
            """
            apps:
                {'65ae3322-a1d1-4287-8d01-a3180e7d4ff4':
                    ['kube-system', 'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                     'kube-system', 'running', 'unmanaged', 'other'],
                 '90995ad0-62c6-40c4-a5e3-57727b272385':
                    ['trident', 'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                     'trident', 'running', 'unmanaged', 'other'],
                 'b6356386-29b6-4790-abe9-cfe76276e1fa':
                    ['kube-system', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'kube-system', 'running', 'unmanaged', 'other'],
                 '9af1931d-da02-4662-824c-71bc32cfa576':
                    ['trident', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'trident', 'running', 'unmanaged', 'other'],
                 '739e7b1f-a71a-42bd-ac6f-db3ff9131133':
                    ['jp3k', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'jp3k', 'running', 'unmanaged', 'namespace'],
                 '697d2a64-61f0-4958-b746-13248be6e6a1':
                    ['wp-mariadb', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'jp3k', 'running', 'managed', 'helm'],
                 'ee7e683c-7532-4f79-9c4b-3e26d8ece391':
                    ['wp-wordpress', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'jp3k', 'running', 'unmanaged', 'helm']}
            """
            systemApps = ["trident", "kube-system"]
            if discovered:
                managedFilter = "unmanaged"
            else:
                managedFilter = "managed"

            # There's really 16 cases here.  managed or unmanaged, each with eight combinations
            # of source, namespace, and cluster
            # source    |y|n|
            # namespace |y|n|
            # cluster   |y|n|
            if source:
                if namespace:
                    if cluster:
                        # case 1: filter on source, namespace, and cluster
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[1] == cluster
                            and v[3] == namespace
                            and v[5] == managedFilter
                            and v[6] == source
                        }
                    else:
                        # case 2: filter on source, namespace
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[3] == namespace
                            and v[5] == managedFilter
                            and v[6] == source
                        }
                else:
                    if cluster:
                        # case 3: filter on source, cluster
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[1] == cluster
                            and v[5] == managedFilter
                            and v[6] == source
                        }
                    else:
                        # case 4: filter on source
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[5] == managedFilter
                            and v[6] == source
                        }
            else:
                if namespace:
                    if cluster:
                        # case 5: filter on namespace, cluster
                        if namespace:
                            appsCooked = {
                                k: v
                                for (k, v) in apps.items()
                                if v[0] not in systemApps
                                and v[1] == cluster
                                and v[3] == namespace
                                and v[5] == managedFilter
                            }
                    else:
                        # case 6: filter on namespace
                        if namespace:
                            appsCooked = {
                                k: v
                                for (k, v) in apps.items()
                                if v[0] not in systemApps
                                and v[3] == namespace
                                and v[5] == managedFilter
                            }
                else:
                    if cluster:
                        # case 7: filtering on cluster, but not source or namespace
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[1] == cluster
                            and v[5] == managedFilter
                        }
                    else:
                        # case 8: not filtering on source, namespace, OR cluster
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps and v[5] == managedFilter
                        }

            if self.output == "json":
                dataReturn = appsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(appsCooked)
            elif self.output == "table":
                tabHeader = [
                    "appName",
                    "appID",
                    "clusterName",
                    "namespace",
                    "state",
                    "source",
                ]
                tabData = []
                for item in appsCooked:
                    tabData.append(
                        [
                            appsCooked[item][0],
                            item,
                            appsCooked[item][1],
                            appsCooked[item][3],
                            appsCooked[item][4],
                            appsCooked[item][6],
                        ]
                    )
                dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")

            if not self.quiet:
                print(dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class getBackups(SDKCommon):
    """Iterate over every managed app, and list all of it's backups.
    Failure reporting is not implimented, failure to list backups for
    one (or more) of N many apps just results in an empty list of backups
    for that app.
    """

    def __init__(self, quiet=True, verbose=False, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__()
        self.apps = getApps().main()

    def main(self, appFilter=None):
        """self.apps = {'739e7b1f-a71a-42bd-ac6f-db3ff9131133':
            ['jp3k', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
             'jp3k', 'running', 'managed', 'namespace'],
        '697d2a64-61f0-4958-b746-13248be6e6a1':
            ['wp-mariadb', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
             'jp3k', 'running', 'managed', 'helm'],
        'ee7e683c-7532-4f79-9c4b-3e26d8ece391':
            ['wp-wordpress', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
             'jp3k', 'running', 'managed', 'helm']}
        """
        backups = {}
        if self.output == "table":
            globaltabHeader = ["AppID", "backupName", "backupID", "backupState"]
            globaltabData = []
        for app in self.apps:
            if appFilter:
                if self.apps[app][0] != appFilter:
                    continue
            endpoint = "k8s/v1/managedApps/%s/appBackups" % app  # appID
            url = self.base + endpoint

            data = {}
            params = {"include": "name,id,state,metadata"}

            if self.verbose:
                print("Listing Backups for %s %s" % (app, self.apps[app][0]))
                print(colored("API URL: %s" % url, "green"))
                print(colored("API Method: GET", "green"))
                print(colored("API Headers: %s" % self.headers, "green"))
                print(colored("API data: %s" % data, "green"))
                print(colored("API params: %s" % params, "green"))

            ret = super().apicall(
                "get", url, data, self.headers, params, self.verifySSL
            )

            if self.verbose:
                print("API HTTP Status Code: %s" % ret.status_code)
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                if results is None:
                    continue
                # Remember this is on a per AppID basis
                """results:
                     {'items':
                        [['hourly-rlezp-xsxmz',
                          '493c862d-71a9-4d47-87d3-eab9006c726f',
                          'completed', {'labels': [],
                                        'creationTimestamp': '2021-08-16T17:00:01Z',
                                        'modificationTimestamp': '2021-08-16T17:00:01Z',
                                        'createdBy': '70fa19ad-eb95-4d1c-b5fb-76b7f4214e6c'}]],
                                        'metadata': {}}
                """
                backups[app] = {}
                for item in results["items"]:
                    backupName = item[0]
                    backupID = item[1]
                    backupState = item[2]
                    # Strip off the trailing Z from the timestamp.  We know it's UTC and the
                    # python library we use to process datetimes doesn't handle the
                    # Zulu time convention that Astra gives us.
                    backupTimeStamp = item[3].get("creationTimestamp")[:-1]
                    # TODO: the backupName is just a label and Astra can have
                    # multiple backups of an app with the same name.
                    # This should be switched to have the backupID as the key.
                    if backupName not in backups[app]:
                        backups[app][backupName] = [
                            backupID,
                            backupState,
                            backupTimeStamp,
                        ]
                if self.output == "table":
                    tabHeader = ["backupName", "backupID", "backupState"]
                    tabData = []
                    for item in backups[app]:
                        tabData.append(
                            [
                                item,
                                backups[app][item][0],
                                backups[app][item][1],
                            ]
                        )
                        globaltabData.append(
                            [
                                app,
                                item,
                                backups[app][item][0],
                                backups[app][item][1],
                            ]
                        )
                if not self.quiet and self.verbose:
                    print("Backups for %s" % app)
                    if self.output == "json":
                        print(backups[app])
                    elif self.output == "yaml":
                        print(yaml.dump(backups[app]))
                    elif self.output == "table":
                        print(tabulate(tabData, tabHeader, tablefmt="grid"))
                        print()
            else:
                continue
        if self.output == "json":
            dataReturn = backups
        elif self.output == "yaml":
            dataReturn = yaml.dump(backups)
        elif self.output == "table":
            dataReturn = tabulate(globaltabData, globaltabHeader, tablefmt="grid")

        if not self.quiet:
            print(dataReturn)
        return dataReturn


class takeBackup(SDKCommon):
    """Take a backup of an app.  An AppID and backupName is provided and
    either the result JSON is returned or the backupID of the newly created
    backup is returned."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-appBackup+json"
        self.headers["Content-Type"] = "application/astra-appBackup+json"

    def main(self, appID, backupName):
        endpoint = "k8s/v1/managedApps/%s/appBackups" % appID
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appBackup",
            "version": "1.0",
            "name": backupName,
        }

        if self.verbose:
            print("Taking backup for %s" % appID)
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(results)
            else:
                return results.get("id") or True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class destroyBackup(SDKCommon):
    """Given an appID and backupID destroy the backup.  Note that this doesn't
    unmanage a backup, it actively destroys it. There is no coming back from this."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-appBackup+json"
        self.headers["Content-Type"] = "application/astra-appBackup+json"

    def main(self, appID, backupID):
        endpoint = "k8s/v1/managedApps/%s/appBackups/%s" % (appID, backupID)
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appBackup",
            "version": "1.0",
        }

        if self.verbose:
            print("Deleting backup %s for %s" % (backupID, appID))
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: DELETE", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class cloneApp(SDKCommon):
    """Clone a backup into a new app, in a new namespace.  Note that Astra doesn't
    currently support in place restores.

    Either backupID, snapshotID, or sourceAppID is required.

    The sourceClusterID is something you'd think would be optional, but it
    is required as well.  Even worse, Astra knows what the (only) correct answer
    is and requires you to provide it anyways.

    Namespace is the new namespace that Astra will create to put the new app into.
    It must not exist on the destination cluster or the clone will fail.

    clusterID identifies the cluster for the new clone.  It's perfectly legal to
    clone an app to the same cluster it is running on; in which case clusterID ==
    sourceClusterID.

    This class doesn't try to validate anything you pass it, if you give it garbage
    for any parameters the clone operation will fail.
    """

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/astra-managedApp+json"

    def main(
        self,
        cloneName,
        clusterID,
        sourceClusterID,
        namespace,
        backupID=None,
        snapshotID=None,
        sourceAppID=None,
    ):
        assert backupID or snapshotID or sourceAppID

        endpoint = "k8s/v1/managedApps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-managedApp",
            "version": "1.0",
            "name": cloneName,
            "clusterID": clusterID,
            "sourceClusterID": sourceClusterID,
            "namespace": namespace,
        }
        if sourceAppID:
            data["sourceAppID"] = sourceAppID
        if backupID:
            data["backupID"] = backupID
        if snapshotID:
            data["snapshotID"] = snapshotID

        if self.verbose:
            print("Cloning app")
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)

            if not self.quiet:
                print(results)
            else:
                return results
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class restoreApp(SDKCommon):
    """Restore a backup or snapshot of an app.
    Must pass in an AppID and either a snapshotID or a backupID
    Note that this is a destructive operation that overwrites the current AppID
    with the backup/snapshot.

    Also note that the return code this class returns is referring to submitting
    the restore job.  To know if the restore job itself succeeds or fails you
    need to monitor the state of the app, watching for it to switch from
    "restoring" to "running" or "failed".
    """

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return True/False
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/astra-managedApp+json"
        self.headers["ForceUpdate"] = "true"

    def main(
        self,
        appID,
        backupID=None,
        snapshotID=None,
    ):
        assert backupID or snapshotID

        endpoint = "k8s/v1/managedApps/%s" % appID
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-managedApp",
            "version": "1.2",
        }
        if backupID:
            data["backupID"] = backupID
        elif snapshotID:
            data["snapshotID"] = snapshotID

        if self.verbose:
            print("Restoring app")
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: PUT", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("put", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class getClusters(SDKCommon):
    """Iterate over the clouds and list the clusters in each."""

    def __init__(self, quiet=True, verbose=False, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__()
        self.clouds = getClouds(quiet=True).main()

    def main(self, hideManaged=False, hideUnmanaged=False):
        clusters = {}
        for cloud in self.clouds:
            endpoint = "topology/v1/clouds/%s/clusters" % cloud
            url = self.base + endpoint
            data = {}
            params = {}

            if self.verbose:
                print(
                    "Getting clusters in cloud %s (%s)..."
                    % (cloud, self.clouds[cloud][0])
                )
                print(colored("API URL: %s" % url, "green"))
                print(colored("API Method: POST", "green"))
                print(colored("API Headers: %s" % self.headers, "green"))
                print(colored("API data: %s" % data, "green"))
                print(colored("API params: %s" % params, "green"))

            ret = super().apicall(
                "get", url, data, self.headers, params, self.verifySSL
            )

            if self.verbose:
                print("API HTTP Status Code: %s" % ret.status_code)
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                for item in results["items"]:
                    if item.get("id") not in clusters:
                        if hideManaged:
                            if item.get("managedState") == "managed":
                                continue
                        if hideUnmanaged:
                            if item.get("managedState") == "unmanaged":
                                continue
                        clusters[item.get("id")] = [
                            item.get("name"),
                            item.get("clusterType"),
                            item.get("managedState"),
                            cloud,
                        ]

        if self.output == "json":
            dataReturn = clusters
        elif self.output == "yaml":
            dataReturn = yaml.dump(clusters)
        elif self.output == "table":
            tabHeader = ["clusterName", "clusterID", "clusterType", "managedState"]
            tabData = []
            for item in clusters:
                tabData.append(
                    [
                        clusters[item][0],
                        item,
                        clusters[item][1],
                        clusters[item][2],
                    ]
                )
            dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")

        if not self.quiet:
            print(dataReturn)
        return dataReturn


class createProtectionpolicy(SDKCommon):
    """Create a backup or snapshot policy on an appID.
    The rules of how dayOfWeek, dayOfMonth, hour, and minute
    need to be set vary based on whether granularity is set to
    hourly, daily, weekly, or monthly
    This class does no validation of the arguments, leaving that
    to the API call itself.  toolkit.py can be used as a guide as to
    what the API requirements are in case the swagger isn't sufficient.
    """

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
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
        endpoint = "k8s/v1/managedApps/%s/schedules" % appID
        url = self.base + endpoint
        params = {}
        data = {
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

        if self.verbose:
            print("Creating %s protection policy for app: %s" % (granularity, appID))
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(results)
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class manageApp(SDKCommon):
    """This class switches a discovered app to a managed app."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/managedApp+json"

    def main(self, appID):
        endpoint = "k8s/v1/managedApps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-managedApp",
            "version": "1.1",
            "id": appID,
        }

        if self.verbose:
            print("Managing app: %s" % appID)
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(results)
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class unmanageApp(SDKCommon):
    """This class switches a managed app to a discovered app."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/managedApp+json"

    def main(self, appID):
        endpoint = "k8s/v1/managedApps/%s" % appID
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print("unmanaging app: %s" % appID)
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: DELETE", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            if not self.quiet:
                print("App unmanaged")
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class takeSnap(SDKCommon):
    """Take a snapshot of an app.  An AppID and snapName are required and
    either the result JSON is returned or the snapID of the newly created
    backup is returned."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-appSnap+json"
        self.headers["Content-Type"] = "application/astra-appSnap+json"

    def main(self, appID, snapName):
        endpoint = "k8s/v1/managedApps/%s/appSnaps" % appID
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appSnap",
            "version": "1.0",
            "name": snapName,
        }

        if self.verbose:
            print("Taking snapshot for %s" % appID)
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(results)
            else:
                return results.get("id") or True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class getSnaps(SDKCommon):
    """Iterate over every managed app, and list all of it's snapshots.
    Failure reporting is not implimented, failure to list snapshots for
    one (or more) of N many apps just results in an empty list of snapshots
    for that app.
    """

    def __init__(self, quiet=True, verbose=False, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__()
        self.apps = getApps().main()

    def main(self, appFilter=None):
        snaps = {}
        if self.output == "table":
            globaltabHeader = ["appID", "snapshotName", "snapshotID", "snapshotState"]
            globaltabData = []
        for app in self.apps:
            if appFilter:
                if self.apps[app][0] != appFilter:
                    continue
            endpoint = "k8s/v1/managedApps/%s/appSnaps" % app
            url = self.base + endpoint

            data = {}
            params = {"include": "name,id,state"}

            if self.verbose:
                print("Listing Snapshots for %s %s" % (app, self.apps[app][0]))
                print(colored("API URL: %s" % url, "green"))
                print(colored("API Method: GET", "green"))
                print(colored("API Headers: %s" % self.headers, "green"))
                print(colored("API data: %s" % data, "green"))
                print(colored("API params: %s" % params, "green"))

            ret = super().apicall(
                "get", url, data, self.headers, params, self.verifySSL
            )

            if self.verbose:
                print("API HTTP Status Code: %s" % ret.status_code)
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                if results is None:
                    continue
                snaps[app] = {}
                for item in results["items"]:
                    appName = item[0]
                    snapID = item[1]
                    snapState = item[2]
                    if appName not in snaps[app]:
                        snaps[app][appName] = [
                            snapID,
                            snapState,
                        ]
                if self.output == "table":
                    tabHeader = ["snapshotName", "snapshotID", "snapshotState"]
                    tabData = []
                    for item in snaps[app]:
                        tabData.append(
                            [
                                item,
                                snaps[app][item][0],
                                snaps[app][item][1],
                            ]
                        )
                        globaltabData.append(
                            [
                                app,
                                item,
                                snaps[app][item][0],
                                snaps[app][item][1],
                            ]
                        )
                if not self.quiet and self.verbose:
                    print("Snapshots for %s" % app)
                    if self.output == "json":
                        print(snaps[app])
                    elif self.output == "yaml":
                        print(yaml.dump(snaps[app]))
                    elif self.output == "table":
                        print(tabulate(tabData, tabHeader, tablefmt="grid"))
                        print()
            else:
                continue
        if self.output == "json":
            dataReturn = snaps
        elif self.output == "yaml":
            dataReturn = yaml.dump(snaps)
        elif self.output == "table":
            dataReturn = tabulate(globaltabData, globaltabHeader, tablefmt="grid")

        if not self.quiet:
            print(dataReturn)
        return dataReturn


class destroySnapshot(SDKCommon):
    """Given an appID and snapID destroy the snapshot.  Note that this doesn't
    unmanage a snapshot, it actively destroys it. There is no coming back from this."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-appSnap+json"
        self.headers["Content-Type"] = "application/astra-appSnap+json"

    def main(self, appID, snapID):
        endpoint = "k8s/v1/managedApps/%s/appSnaps/%s" % (appID, snapID)
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appSnap",
            "version": "1.0",
        }

        if self.verbose:
            print("Deleting snapshot %s for %s" % (snapID, appID))
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: DELETE", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class getClouds(SDKCommon):
    def __init__(self, quiet=True, verbose=False, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__()

    def main(self):
        endpoint = "topology/v1/clouds"
        url = self.base + endpoint

        data = {}
        params = {"include": "id,name,state"}

        if self.verbose:
            print("Getting clouds...")
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            clouds = {}
            for item in results["items"]:
                if item.get("id") not in clouds:
                    clouds[item.get("id")] = [
                        item.get("name"),
                        item.get("cloudType"),
                    ]
            if self.output == "json":
                dataReturn = clouds
            elif self.output == "yaml":
                dataReturn = yaml.dump(clouds)
            elif self.output == "table":
                tabHeader = ["cloudName", "cloudID", "cloudType"]
                tabData = []
                for item in clouds:
                    tabData.append(
                        [
                            clouds[item][0],
                            item,
                            clouds[item][1],
                        ]
                    )
                dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")
            if not self.quiet:
                print(dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class getStorageClasses(SDKCommon):
    def __init__(self, quiet=True, verbose=False, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__()
        self.clouds = getClouds().main()
        self.clusters = getClusters().main()

    def main(self):
        storageClasses = {}
        for cloud in self.clouds:
            storageClasses[cloud] = {}
            for cluster in self.clusters:
                # exclude invalid combinations of cloud/cluster
                if self.clusters[cluster][3] != cloud:
                    continue
                storageClasses[cloud][cluster] = {}
                endpoint = "topology/v1/clouds/%s/clusters/%s/storageClasses" % (
                    cloud,
                    cluster,
                )
                url = self.base + endpoint

                data = {}
                params = {}

                if self.verbose:
                    print()
                    print(
                        "Listing StorageClasses for cluster: %s in cloud: %s"
                        % (cluster, cloud)
                    )
                    print()
                    print(colored("API URL: %s" % url, "green"))
                    print(colored("API Method: GET", "green"))
                    print(colored("API Headers: %s" % self.headers, "green"))
                    print(colored("API data: %s" % data, "green"))
                    print(colored("API params: %s" % params, "green"))
                    print()

                ret = super().apicall(
                    "get", url, data, self.headers, params, self.verifySSL
                )

                if self.verbose:
                    print("API HTTP Status Code: %s" % ret.status_code)
                    print()
                if ret.ok:
                    results = super().jsonifyResults(ret)
                    if results is None:
                        continue
                    for entry in results.get("items"):
                        storageClasses[cloud][cluster][entry.get("id")] = entry.get(
                            "name"
                        )

        if self.output == "json":
            dataReturn = storageClasses
        elif self.output == "yaml":
            dataReturn = yaml.dump(storageClasses)
        elif self.output == "table":
            tabData = []
            tabHeader = ["cloud", "cluster", "storageclassID", "storageclassName"]
            for cloud in storageClasses:
                for cluster in storageClasses[cloud]:
                    for storageClass in storageClasses[cloud][cluster]:
                        tabData.append(
                            [
                                self.clouds[cloud][0],
                                self.clusters[cluster][0],
                                storageClass,
                                storageClasses[cloud][cluster][storageClass],
                            ]
                        )
            dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")

        if not self.quiet:
            print(dataReturn)
        return dataReturn


class manageCluster(SDKCommon):
    """This class switches an unmanaged cluster to a managed cluster"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedCluster+json"
        self.headers["Content-Type"] = "application/managedCluster+json"

    def main(self, clusterID, storageClassID):
        endpoint = "topology/v1/managedClusters"
        url = self.base + endpoint
        params = {}
        data = {
            "defaultStorageClass": storageClassID,
            "id": clusterID,
            "type": "application/astra-managedCluster",
            "version": "1.0",
        }

        if self.verbose:
            print()
            print("Managing: %s" % clusterID)
            print()
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: POST", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))
            print()

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(results)
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False


class unmanageCluster(SDKCommon):
    """This class switches a managed cluster to an un managed cluster"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedCluster+json"
        self.headers["Content-Type"] = "application/managedCluster+json"

    def main(self, clusterID):
        endpoint = "topology/v1/managedClusters/%s" % clusterID
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print()
            print("Unmanaging: %s" % clusterID)
            print()
            print(colored("API URL: %s" % url, "green"))
            print(colored("API Method: DELETE", "green"))
            print(colored("API Headers: %s" % self.headers, "green"))
            print(colored("API data: %s" % data, "green"))
            print(colored("API params: %s" % params, "green"))
            print()

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()

        if ret.ok:
            if not self.quiet:
                print("Cluster unmanaged")
            return True
        else:
            if not self.quiet:
                print("API HTTP Status Code: %s - %s" % (ret.status_code, ret.reason))
                if ret.text.strip():
                    print("Error text: %s" % ret.text)
            return False
