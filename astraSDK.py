#!/usr/bin/env python
"""
   Copyright 2022 NetApp, Inc

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
import json
import copy
from tabulate import tabulate
from termcolor import colored
import requests
from urllib3 import disable_warnings
from datetime import datetime, timedelta


class getConfig:
    """In order to make API calls to Astra Control we need to know which Astra Control instance
    to connect to, and the credentials to make calls.  This info is found in config.yaml,
    which we search for in the following four places:
    1) The directory that astraSDK.py is located in
    2) ~/.config/astra-toolkits/
    3) /etc/astra-toolkits/
    4) The directory pointed to by the shell env var ASTRATOOLKITS_CONF
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
                print(f"{configFile} not valid YAML")
                continue

        if self.conf is None:
            print("config.yaml not found.")
            sys.exit(4)

        for item in ["astra_project", "uid", "headers"]:
            try:
                assert self.conf.get(item) is not None
            except AssertionError:
                print(f"{item} is a required field in {configFile}")
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

    def apicall(self, method, url, data, headers, params, verify, quiet=False):
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
        if not ret.ok and not quiet:
            if ret.status_code >= 400 and ret.status_code < 500:
                if "x-pcloud-accountid" in ret.text:
                    print("preflight API call to Astra Control failed (check uid in config.json)")
                elif ret.status_code == 401:
                    print(
                        "preflight API call to Astra Control failed "
                        "(check Authoriztion in config.json)"
                    )
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                print(f"text: {ret.text}")
            else:
                print("preflight API call to Astra Control failed (Internal Server Error)")
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                print(f"text: {ret.text}")
        return ret

    def jsonifyResults(self, requestsObject):
        try:
            results = requestsObject.json()
        except ValueError as e:
            print(f"response contained invalid JSON: {e}")
            results = None
        return results

    def printVerbose(self, url, method, headers, data, params):
        """Function to print API call details when in verbose mode"""
        print(colored(f"API URL: {url}", "green"))
        print(colored(f"API Method: {method}", "green"))
        print(colored(f"API Headers: {headers}", "green"))
        print(colored(f"API data: {data}", "green"))
        print(colored(f"API params: {params}", "green"))

    def basicTable(self, tabHeader, tabKeys, dataDict):
        """Function to create a basic tabulate table for terminal printing"""
        tabData = []
        for item in dataDict["items"]:
            # Generate a table row based on the keys list
            row = [item.get(i) for i in tabKeys]
            # Handle cases where table row has a nested list
            for c, r in enumerate(row):
                if type(r) is list:
                    row[c] = ", ".join(r)
            tabData.append(row)
        return tabulate(tabData, tabHeader, tablefmt="grid")


class getApps(SDKCommon):
    """List all apps known to Astra.  With App 2.0 API spec in the Aug 2022 release, there's
    no longer a "discovered" or "ignored" construct with apps.  There's simply managed apps
    (which is what this class covers), or yet-to-be-managed (referred to as unmanaged) apps,
    which are handled by the getNamespaces class.

    Therefore this class cannot list all of the managed and unmanaged apps.
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

    def main(
        self,
        namespace=None,
        nameFilter=None,
        cluster=None,
    ):
        """namespace: Filter by the namespace the app is in
        cluster: Filter by a specific k8s cluster"""

        endpoint = "k8s/v2/apps"
        params = {}
        url = self.base + endpoint
        data = {}

        if self.verbose:
            print("Getting apps...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            apps = super().jsonifyResults(ret)
            appsCooked = copy.deepcopy(apps)
            """
            apps = {"items":[
                    {
                        "type": "application/astra-app",
                        "version": "2.0",
                        "id": "36ba2699-66dc-4ad1-949b-26c1108f42e2",
                        "name": "wordpress-app",
                        "namespaceScopedResources": [
                            {
                                "namespace": "wordpress",
                                "labelSelectors": []
                            }
                        ],
                        "state": "ready",
                        "lastResourceCollectionTimestamp": "2022-07-20T18:19:35Z",
                        "stateTransitions": [
                            { "to": ["pending"] },
                            { "to": ["provisioning"] },
                            { "from": "pending", "to": ["discovering", "failed"] },
                            { "from": "discovering", "to": ["ready", "failed"] },
                            {
                                "from": "ready",
                                "to": [ "discovering", "restoring", "unavailable", "failed"]
                            },
                            { "from": "unavailable", "to": ["ready", "restoring"] },
                            { "from": "provisioning", "to": ["discovering", "failed"] },
                            { "from": "restoring", "to": ["discovering", "failed"] }
                        ],
                        "stateDetails": [],
                        "protectionState": "none",
                        "protectionStateDetails": [],
                        "namespaces": [
                            "wordpress"
                        ],
                        "clusterName": "uscentral1-cluster",
                        "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d",
                        "clusterType": "gke",
                        "metadata": {
                            "labels": [],
                            "creationTimestamp": "2022-07-20T18:19:30Z",
                            "modificationTimestamp": "2022-07-20T18:20:36Z",
                            "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"
                        }
                    }],
                "metadata":{}
            }
            """

            # Loop through all apps and delete those that don't match filters
            for counter, app in enumerate(apps.get("items")):
                # If there's a given filter, delete non-matching values
                if namespace:
                    delApp = True
                    for ns in app["namespaces"]:
                        if ns == namespace:
                            delApp = False
                    if delApp:
                        appsCooked["items"].remove(apps["items"][counter])
                        continue
                if cluster and not (cluster == app["clusterName"] or cluster == app["clusterID"]):
                    appsCooked["items"].remove(apps["items"][counter])
                elif nameFilter and nameFilter not in app.get("name"):
                    appsCooked["items"].remove(apps["items"][counter])

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
                ]
                tabData = []
                for app in appsCooked.get("items"):
                    tabData.append(
                        [
                            (
                                app["name"]
                                if "replicationSourceAppID" not in app
                                else app["name"] + colored(" (replication destination)", "blue")
                            ),
                            app["id"],
                            app["clusterName"],
                            ", ".join(app["namespaces"]),
                            app["state"],
                        ]
                    )
                dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")

            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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
        if self.apps is False:
            print("Call to getApps().main() failed")
            return False

        """self.apps = {"items":[{"appDefnSource":"namespace","appLabels":[],
            "clusterID":"420a9ab0-1608-4e2e-a5ed-ca5b26a7fe69","clusterName":"useast1-cluster",
            "clusterType":"gke","collectionState":"fullyCollected","collectionStateDetails":[],
            "collectionStateTransitions":[{"from":"notCollected","to":["partiallyCollected",
            "fullyCollected"]},{"from":"partiallyCollected","to":["fullyCollected"]},
            {"from":"fullyCollected","to":[]}],"id":"d8cf2f17-d8d6-4b9f-aa42-f945d43b9a87",
            "managedState":"managed","managedStateUnready":[],
            "managedTimestamp":"2022-05-12T14:35:36Z","metadata":{"createdBy":"system",
            "creationTimestamp":"2022-05-12T14:35:27Z","labels":[],
            "modificationTimestamp":"2022-05-12T18:47:45Z"},"name":"wordpress-ns",
            "namespace":"wordpress-ns","protectionState":"protected","protectionStateUnready":[],
            "state":"running","stateUnready":[],"system":"false","type":"application/astra-app",
            "version":"1.1"}],"metadata":{}}
        """
        backups = {}
        backups["items"] = []

        for app in self.apps["items"]:
            if appFilter:
                if app["name"] != appFilter and app["id"] != appFilter:
                    continue
            endpoint = f"k8s/v1/apps/{app['id']}/appBackups"
            url = self.base + endpoint

            data = {}
            params = {}

            if self.verbose:
                print(f"Listing Backups for {app['id']} {app['name']}")
                self.printVerbose(url, "GET", self.headers, data, params)

            ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

            if self.verbose:
                print(f"API HTTP Status Code: {ret.status_code}")
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                if results is None:
                    continue
                # Remember this is on a per AppID basis
                for item in results["items"]:
                    # Adding custom 'appID' key/value pair
                    if not item.get("appID"):
                        item["appID"] = app["id"]
                    backups["items"].append(item)
                if not self.quiet and self.verbose:
                    print(f"Backups for {app['id']}")
                    if self.output == "json":
                        print(json.dumps(results))
                    elif self.output == "yaml":
                        print(yaml.dump(results))
                    elif self.output == "table":
                        print(
                            self.basicTable(
                                ["backupName", "backupID", "backupState"],
                                ["name", "id", "state"],
                                results,
                            )
                        )
                        print()
            else:
                continue
        if self.output == "json":
            dataReturn = backups
        elif self.output == "yaml":
            dataReturn = yaml.dump(backups)
        elif self.output == "table":
            dataReturn = self.basicTable(
                ["AppID", "backupName", "backupID", "backupState"],
                ["appID", "name", "id", "state"],
                backups,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
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

        endpoint = f"k8s/v1/apps/{appID}/appBackups"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appBackup",
            "version": "1.1",
            "name": backupName,
        }

        if self.verbose:
            print(f"Taking backup for {appID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            else:
                return results.get("id") or True
        else:
            print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
            if ret.text.strip():
                print(f"Error text: {ret.text}")
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

        endpoint = f"k8s/v1/apps/{appID}/appBackups/{backupID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appBackup",
            "version": "1.1",
        }

        if self.verbose:
            print(f"Deleting backup {backupID} for {appID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class cloneApp(SDKCommon):
    """Clone an app to a new app and namespace.
    Either backupID, snapshotID, or sourceAppID is required.
    The sourceClusterID is required as well.

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
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"

    def main(
        self,
        cloneName,
        clusterID,
        sourceClusterID,
        cloneNamespace=None,
        backupID=None,
        snapshotID=None,
        sourceAppID=None,
    ):
        assert backupID or snapshotID or sourceAppID

        endpoint = "k8s/v2/apps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-app",
            "version": "2.0",
            "name": cloneName,
            "clusterID": clusterID,
            "sourceClusterID": sourceClusterID,
        }
        if sourceAppID:
            data["sourceAppID"] = sourceAppID
        if backupID:
            data["backupID"] = backupID
        if snapshotID:
            data["snapshotID"] = snapshotID
        if cloneNamespace:
            data["namespaceScopedResources"] = [{"namespace": cloneNamespace, "labelSelectors": []}]

        if self.verbose:
            print("Cloning app")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)

            if not self.quiet:
                print(json.dumps(results))
            else:
                return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"
        self.headers["ForceUpdate"] = "true"

    def main(
        self,
        appID,
        backupID=None,
        snapshotID=None,
    ):
        assert backupID or snapshotID

        endpoint = f"k8s/v2/apps/{appID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-app",
            "version": "2.0",
        }
        if backupID:
            data["backupID"] = backupID
        elif snapshotID:
            data["snapshotID"] = snapshotID

        if self.verbose:
            print("Restoring app")
            self.printVerbose(url, "PUT", self.headers, data, params)

        ret = super().apicall("put", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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

    def main(self, hideManaged=False, hideUnmanaged=False, nameFilter=None):
        clusters = {}
        clusters["items"] = []
        if self.clouds is False:
            print("Call to get clouds failed")
            return False
        if len(self.clouds["items"]) == 0:
            print("No clouds found")
            return True
        for cloud in self.clouds["items"]:
            endpoint = f"topology/v1/clouds/{cloud['id']}/clusters"
            url = self.base + endpoint
            data = {}
            params = {}

            if self.verbose:
                print(f"Getting clusters in cloud {cloud['id']} ({cloud['name']})...")
                self.printVerbose(url, "GET", self.headers, data, params)

            ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

            if self.verbose:
                print(f"API HTTP Status Code: {ret.status_code}")
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                for item in results["items"]:
                    if nameFilter and nameFilter not in item.get("name"):
                        continue
                    if hideManaged and item.get("managedState") == "managed":
                        continue
                    if hideUnmanaged and item.get("managedState") == "unmanaged":
                        continue
                    clusters["items"].append(item)

        if self.output == "json":
            dataReturn = clusters
        elif self.output == "yaml":
            dataReturn = yaml.dump(clusters)
        elif self.output == "table":
            dataReturn = self.basicTable(
                ["clusterName", "clusterID", "clusterType", "managedState"],
                ["name", "id", "clusterType", "managedState"],
                clusters,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


class getProtectionpolicies(SDKCommon):
    """Get all the Protection policies (aka backup / snapshot schedules) for each app, unless an
    optional appFilter is passed (can be either app name or app ID, but must be an exact match."""

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
        if self.apps is False:
            print("Call to getApps() failed")
            return False

        protections = {}
        protections["items"] = []

        for app in self.apps["items"]:
            if appFilter:
                if app["name"] != appFilter and app["id"] != appFilter:
                    continue
            endpoint = f"k8s/v1/apps/{app['id']}/schedules"
            url = self.base + endpoint

            data = {}
            params = {}

            if self.verbose:
                print(f"Getting protection policies for {app['id']} {app['name']}...")
                self.printVerbose(url, "GET", self.headers, data, params)

            ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

            if self.verbose:
                print(f"API HTTP Status Code: {ret.status_code}")
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                if results is None:
                    continue
                for item in results["items"]:
                    # Adding custom 'appID' key/value pair
                    if not item.get("appID"):
                        item["appID"] = app["id"]
                    protections["items"].append(item)
                if not self.quiet and self.verbose:
                    print(f"Protection policies for {app['id']}")
                    if self.output == "json":
                        print(json.dumps(results))
                    elif self.output == "yaml":
                        print(yaml.dump(results))
                    elif self.output == "table":
                        print(
                            self.basicTable(
                                [
                                    "protectionID",
                                    "granularity",
                                    "minute",
                                    "hour",
                                    "dayOfWeek",
                                    "dayOfMonth",
                                    "snapRetention",
                                    "backupRetention",
                                ],
                                [
                                    "id",
                                    "granularity",
                                    "minute",
                                    "hour",
                                    "dayOfWeek",
                                    "dayOfMonth",
                                    "snapshotRetention",
                                    "backupRetention",
                                ],
                                results,
                            )
                        )
                        print()
            else:
                continue
        if self.output == "json":
            dataReturn = protections
        elif self.output == "yaml":
            dataReturn = yaml.dump(protections)
        elif self.output == "table":
            dataReturn = self.basicTable(
                [
                    "appID",
                    "protectionID",
                    "granularity",
                    "minute",
                    "hour",
                    "dayOfWeek",
                    "dayOfMonth",
                    "snapRetention",
                    "backupRetention",
                ],
                [
                    "appID",
                    "id",
                    "granularity",
                    "minute",
                    "hour",
                    "dayOfWeek",
                    "dayOfMonth",
                    "snapshotRetention",
                    "backupRetention",
                ],
                protections,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
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
        recurrenceRule=None,
    ):

        endpoint = f"k8s/v1/apps/{appID}/schedules"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-schedule",
            "version": "1.2",
            "backupRetention": backupRetention,
            "dayOfMonth": dayOfMonth,
            "dayOfWeek": dayOfWeek,
            "enabled": "true",
            "granularity": granularity,
            "hour": hour,
            "minute": minute,
            "name": f"{granularity} schedule",
            "snapshotRetention": snapshotRetention,
        }
        if recurrenceRule:
            data["recurrenceRule"] = recurrenceRule
            data["replicate"] = "true"

        if self.verbose:
            print(f"Creating {granularity} protection policy for app: {appID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class destroyProtectiontionpolicy(SDKCommon):
    """This class destroys a protection policy"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-schedule+json"
        self.headers["Content-Type"] = "application/astra-schedule+json"

    def main(self, appID, protectionID):

        endpoint = f"k8s/v1/apps/{appID}/schedules/{protectionID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Deleting {protectionID} of app {appID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class manageApp(SDKCommon):
    """This class switches an unmanaged (aka undefined) app to a managed (aka defined) app."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"

    def main(self, appName, namespace, clusterID, label=None):

        endpoint = "k8s/v2/apps"
        url = self.base + endpoint
        params = {}
        data = {
            "clusterID": clusterID,
            "name": appName,
            "namespaceScopedResources": [{"namespace": namespace}],
            "type": "application/astra-app",
            "version": "2.0",
        }
        if label:
            data["namespaceScopedResources"][0]["labelSelectors"] = [label]

        if self.verbose:
            print(f"Managing app: {appName}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL, self.quiet)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class unmanageApp(SDKCommon):
    """This class switches a managed app to a discovered app."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"

    def main(self, appID):

        endpoint = f"k8s/v2/apps/{appID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Unmanaging app: {appID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            if not self.quiet:
                print("App unmanaged")
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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

        endpoint = f"k8s/v1/apps/{appID}/appSnaps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appSnap",
            "version": "1.1",
            "name": snapName,
        }

        if self.verbose:
            print(f"Taking snapshot for {appID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            else:
                return results.get("id") or True
        else:
            print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
            if ret.text.strip():
                print(f"Error text: {ret.text}")
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
        if self.apps is False:
            print("Call to getApps() failed")
            return False

        snaps = {}
        snaps["items"] = []

        for app in self.apps["items"]:
            if appFilter:
                if app["name"] != appFilter and app["id"] != appFilter:
                    continue
            endpoint = f"k8s/v1/apps/{app['id']}/appSnaps"
            url = self.base + endpoint

            data = {}
            params = {}

            if self.verbose:
                print(f"Listing Snapshots for {app['id']} {app['name']}")
                self.printVerbose(url, "GET", self.headers, data, params)

            ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

            if self.verbose:
                print(f"API HTTP Status Code: {ret.status_code}")
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                if results is None:
                    continue
                for item in results["items"]:
                    # Adding custom 'appID' key/value pair
                    if not item.get("appID"):
                        item["appID"] = app["id"]
                    snaps["items"].append(item)
                if not self.quiet and self.verbose:
                    print(f"Snapshots for {app['id']}")
                    if self.output == "json":
                        print(json.dumps(results))
                    elif self.output == "yaml":
                        print(yaml.dump(results))
                    elif self.output == "table":
                        print(
                            self.basicTable(
                                ["snapshotName", "snapshotID", "snapshotState"],
                                ["name", "id", "state"],
                                results,
                            ),
                        )
                        print()
            else:
                continue
        if self.output == "json":
            dataReturn = snaps
        elif self.output == "yaml":
            dataReturn = yaml.dump(snaps)
        elif self.output == "table":
            dataReturn = self.basicTable(
                ["appID", "snapshotName", "snapshotID", "snapshotState"],
                ["appID", "name", "id", "state"],
                snaps,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
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

        endpoint = f"k8s/v1/apps/{appID}/appSnaps/{snapID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appSnap",
            "version": "1.1",
        }

        if self.verbose:
            print(f"Deleting snapshot {snapID} for {appID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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

    def main(self, cloudType=None):

        endpoint = "topology/v1/clouds"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting clouds...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            clouds = super().jsonifyResults(ret)
            cloudsCooked = copy.deepcopy(clouds)
            for counter, cloud in enumerate(clouds.get("items")):
                if cloudType and cloudType != cloud["cloudType"]:
                    cloudsCooked["items"].remove(clouds["items"][counter])
            if self.output == "json":
                dataReturn = cloudsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(cloudsCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["cloudName", "cloudID", "cloudType"], ["name", "id", "cloudType"], cloudsCooked
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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

    def main(self, cloudType=None):
        if self.clouds is False:
            print("getClouds().main() failed")
            return False
        if self.clusters is False:
            print("getClusters().main() failed")
            return False
        if len(self.clouds["items"]) == 0:
            print("No clouds found")
            return True
        if len(self.clusters["items"]) == 0:
            print("No clusters found")
            return True

        storageClasses = {}
        storageClasses["items"] = []
        for cloud in self.clouds["items"]:
            for cluster in self.clusters["items"]:
                # exclude invalid combinations of cloud/cluster
                if (
                    cluster["cloudID"] != cloud["id"]
                    or cluster["managedState"] == "ineligible"
                    or (cloudType and cloud["cloudType"] != cloudType)
                ):
                    continue
                endpoint = (
                    f"topology/v1/clouds/{cloud['id']}/clusters/{cluster['id']}/storageClasses"
                )
                url = self.base + endpoint

                data = {}
                params = {}

                if self.verbose:
                    print(
                        f"Listing StorageClasses for cluster: {cluster['id']} in cloud: {cloud['id']}"
                    )
                    self.printVerbose(url, "GET", self.headers, data, params)

                ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

                if self.verbose:
                    print(f"API HTTP Status Code: {ret.status_code}")
                    print()
                if ret.ok:
                    results = super().jsonifyResults(ret)
                    if results is None:
                        continue
                    for entry in results.get("items"):
                        # Adding three custom key/value pairs since the storageClasses API response
                        # doesn't contain cloud or cluster info
                        if not entry.get("cloudID"):
                            entry["cloudID"] = cloud["id"]
                        if not entry.get("cloudType"):
                            entry["cloudType"] = cloud["cloudType"]
                        if not entry.get("clusterID"):
                            entry["clusterID"] = cluster["id"]
                        if not entry.get("clusterName"):
                            entry["clusterName"] = cluster["name"]
                        storageClasses["items"].append(entry)

        if self.output == "json":
            dataReturn = storageClasses
        elif self.output == "yaml":
            dataReturn = yaml.dump(storageClasses)
        elif self.output == "table":
            dataReturn = self.basicTable(
                ["cloud", "cluster", "storageclassID", "storageclassName"],
                ["cloudType", "clusterName", "id", "name"],
                storageClasses,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
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
            print(f"Managing: {clusterID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class deleteCluster(SDKCommon):
    """This class deletes a cluster.  It's meant for ACC environments only, and should
    be called after unmanageCluster if it's an ACC-managed cluster."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-cluster+json"
        self.headers["Content-Type"] = "application/astra-cluster+json"

    def main(self, clusterID, cloudID):

        endpoint = f"topology/v1/clouds/{cloudID}/clusters/{clusterID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Deleting: {clusterID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            if not self.quiet:
                print("Cluster deleted")
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
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
        self.clusters = getClusters().main()

    def main(self, clusterID):

        endpoint = f"topology/v1/managedClusters/{clusterID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Unmanaging: {clusterID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            if not self.quiet:
                print("Cluster unmanaged")
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getNamespaces(SDKCommon):
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
        self.clusters = getClusters().main()

    def main(
        self,
        clusterID=None,
        nameFilter=None,
        showRemoved=False,
        unassociated=False,
        minuteFilter=False,
    ):
        if self.apps is False:
            print("Call to getApps().main() failed")
            return False

        if clusterID:
            endpoint = f"topology/v1/clusters/{clusterID}/namespaces"
        else:
            endpoint = "topology/v1/namespaces"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting namespaces...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            systemNS = ["kube-node-lease", "kube-public", "kube-system", "trident"]
            namespaces = super().jsonifyResults(ret)
            # Add in a custom key/value "associatedApps"
            for ns in namespaces["items"]:
                ns["associatedApps"] = []
                for app in self.apps["items"]:
                    if ns["clusterID"] == app["clusterID"]:
                        for nsr in app["namespaceScopedResources"]:
                            if ns["name"] == nsr["namespace"]:
                                ns["associatedApps"].append(app["name"])
            # Delete the unneeded namespaces based on filters
            namespacesCooked = copy.deepcopy(namespaces)
            clusterList = []
            for cluster in self.clusters["items"]:
                if cluster["managedState"] == "managed":
                    clusterList.append(cluster["id"])
            for counter, namespace in enumerate(namespaces.get("items")):
                if namespace.get("systemType") or namespace.get("name") in systemNS:
                    namespacesCooked["items"].remove(namespaces["items"][counter])
                elif nameFilter and nameFilter not in namespace.get("name"):
                    namespacesCooked["items"].remove(namespaces["items"][counter])
                elif not showRemoved and namespace.get("namespaceState") == "removed":
                    namespacesCooked["items"].remove(namespaces["items"][counter])
                elif namespace["clusterID"] not in clusterList:
                    namespacesCooked["items"].remove(namespaces["items"][counter])
                elif (
                    unassociated
                    and type(namespace.get("associatedApps")) is list
                    and len(namespace["associatedApps"]) > 0
                ):
                    namespacesCooked["items"].remove(namespaces["items"][counter])
                elif minuteFilter and (
                    datetime.utcnow()
                    - datetime.strptime(
                        namespace.get("metadata").get("creationTimestamp"), "%Y-%m-%dT%H:%M:%SZ"
                    )
                    > timedelta(minutes=minuteFilter)
                ):
                    namespacesCooked["items"].remove(namespaces["items"][counter])

            if self.output == "json":
                dataReturn = namespacesCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(namespacesCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["name", "namespaceID", "namespaceState", "associatedApps", "clusterID"],
                    ["name", "id", "namespaceState", "associatedApps", "clusterID"],
                    namespacesCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getScripts(SDKCommon):
    """Get all the scripts (aka hook sources) for the Astra Control account"""

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

    def main(self, scriptSourceName=None):

        endpoint = "core/v1/hookSources"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting scripts...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            scripts = super().jsonifyResults(ret)
            scriptsCooked = copy.deepcopy(scripts)
            if scriptSourceName:
                for counter, script in enumerate(scripts.get("items")):
                    if script.get("name") != scriptSourceName:
                        scriptsCooked["items"].remove(scripts["items"][counter])

            if self.output == "json":
                dataReturn = scriptsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(scriptsCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["scriptName", "scriptID", "description"],
                    ["name", "id", "description"],
                    scriptsCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class createScript(SDKCommon):
    """Create a script (aka hook source)"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-hookSource+json"
        self.headers["Content-Type"] = "application/astra-hookSource+json"

    def main(
        self,
        name,
        source,
        description=None,
    ):

        endpoint = f"core/v1/hookSources"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-hookSource",
            "version": "1.0",
            "name": name,
            "source": source,
            "sourceType": "script",
        }
        if description:
            data["description"] = description

        if self.verbose:
            print(f"Creating script {name}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class destroyScript(SDKCommon):
    """Given a scriptID destroy the script.  Note that this doesn't unmanage
    a script, it actively destroys it. There is no coming back from this."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-hookSource+json"
        self.headers["Content-Type"] = "application/astra-hookSource+json"

    def main(self, scriptID):

        endpoint = f"core/v1/hookSources/{scriptID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-hookSource",
            "version": "1.0",
        }

        if self.verbose:
            print(f"Deleting scriptID {scriptID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getAppAssets(SDKCommon):
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

    def main(self, appID):

        endpoint = f"k8s/v1/apps/{appID}/appAssets"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting app assets...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            assets = super().jsonifyResults(ret)
            if self.output == "json":
                dataReturn = assets
            elif self.output == "yaml":
                dataReturn = yaml.dump(assets)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["assetName", "assetType"],
                    ["assetName", "assetType"],
                    assets,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getHooks(SDKCommon):
    """Get all the execution hooks for every app"""

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
        if self.apps is False:
            print("Call to getApps() failed")
            return False

        hooks = {}
        hooks["items"] = []

        for app in self.apps["items"]:
            if appFilter:
                if app["name"] != appFilter and app["id"] != appFilter:
                    continue
            endpoint = f"k8s/v1/apps/{app['id']}/executionHooks"
            url = self.base + endpoint

            data = {}
            params = {}

            if self.verbose:
                print("Getting execution hooks...")
                self.printVerbose(url, "GET", self.headers, data, params)

            ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

            if self.verbose:
                print(f"API HTTP Status Code: {ret.status_code}")
                print()

            if ret.ok:
                results = super().jsonifyResults(ret)
                if results is None:
                    continue
                for item in results["items"]:
                    hooks["items"].append(item)
                if not self.quiet and self.verbose:
                    print(f"Execution hooks for {app['id']}")
                    if self.output == "json":
                        print(json.dumps(results))
                    elif self.output == "yaml":
                        print(yaml.dump(results))
                    elif self.output == "table":
                        print(
                            self.basicTable(
                                ["hookName", "hookID", "matchingImages"],
                                ["name", "id", "matchingImages"],
                                results,
                            )
                        )
                        print()
            else:
                if not self.quiet:
                    print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                    if ret.text.strip():
                        print(f"Error text: {ret.text}")
                continue
        if self.output == "json":
            dataReturn = hooks
        elif self.output == "yaml":
            dataReturn = yaml.dump(hooks)
        elif self.output == "table":
            dataReturn = self.basicTable(
                ["appID", "hookName", "hookID", "matchingImages"],
                ["appID", "name", "id", "matchingImages"],
                hooks,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


class createHook(SDKCommon):
    """Create an execution hook"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-executionHook+json"
        self.headers["Content-Type"] = "application/astra-executionHook+json"

    def main(
        self,
        appID,
        name,
        scriptID,
        stage,
        action,
        arguments,
        containerRegex=None,
        description=None,
    ):

        # endpoint = f"k8s/v1/apps/{appID}/executionHooks"
        endpoint = f"core/v1/executionHooks"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-executionHook",
            "version": "1.0",
            "name": name,
            "hookType": "custom",
            "action": action,
            "stage": stage,
            "hookSourceID": scriptID,
            "arguments": arguments,
            "appID": appID,
            "enabled": "true",
        }
        if description:
            data["description"] = description
        if containerRegex:
            data["matchingCriteria"] = [{"type": "containerImage", "value": containerRegex}]

        if self.verbose:
            print(f"Creating executionHook {name}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class destroyHook(SDKCommon):
    """Given an appID and hookID destroy the hook.  Note that this doesn't unmanage
    a hook, it actively destroys it. There is no coming back from this."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-executionHook+json"
        self.headers["Content-Type"] = "application/astra-executionHook+json"

    def main(self, appID, hookID):

        # endpoint = f"k8s/v1/apps/{appID}/executionHooks/{hookID}"
        endpoint = f"core/v1/executionHooks/{hookID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-hookSource",
            "version": "1.0",
            "appID": appID,  # Not strictly required at this time
        }

        if self.verbose:
            print(f"Deleting hookID {hookID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getCredentials(SDKCommon):
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

    def main(self, kubeconfigOnly=False):

        endpoint = "core/v1/credentials"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting credentials...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            creds = super().jsonifyResults(ret)
            credsCooked = copy.deepcopy(creds)
            if kubeconfigOnly:
                for counter, cred in enumerate(creds.get("items")):
                    delCred = True
                    if cred["metadata"].get("labels"):
                        for label in cred["metadata"]["labels"]:
                            if label["name"] == "astra.netapp.io/labels/read-only/credType":
                                if label["value"] == "kubeconfig":
                                    delCred = False
                    if delCred:
                        credsCooked["items"].remove(creds["items"][counter])
            if self.output == "json":
                dataReturn = credsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(credsCooked)
            elif self.output == "table":
                tabHeader = ["credName", "credID", "credType", "cloudName", "clusterName"]
                tabData = []
                for cred in credsCooked["items"]:
                    credType = None
                    cloudName = "N/A"
                    clusterName = "N/A"
                    if cred["metadata"].get("labels"):
                        for label in cred["metadata"]["labels"]:
                            if label["name"] == "astra.netapp.io/labels/read-only/credType":
                                credType = label["value"]
                            elif label["name"] == "astra.netapp.io/labels/read-only/cloudName":
                                cloudName = label["value"]
                            elif label["name"] == "astra.netapp.io/labels/read-only/clusterName":
                                clusterName = label["value"]
                    tabData.append(
                        [
                            cred["name"],
                            cred["id"],
                            (cred["keyType"] if not credType else credType),
                            cloudName,
                            clusterName,
                        ]
                    )
                dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class createCredential(SDKCommon):
    """Create a kubeconfig or S3 credential.  This class does not perform any validation
    of the inputs.  Please see toolkit.py for further examples if the swagger definition
    does not provide all the information you require."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-credential+json"
        self.headers["Content-Type"] = "application/astra-credential+json"

    def main(
        self,
        credName,
        keyType,
        keyStore,
        cloudName="private",
    ):

        endpoint = "core/v1/credentials"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-credential",
            "version": "1.1",
            "keyStore": keyStore,
            "keyType": keyType,
            "name": credName,
            "metadata": {
                "labels": [
                    {"name": "astra.netapp.io/labels/read-only/credType", "value": keyType},
                    {"name": "astra.netapp.io/labels/read-only/cloudName", "value": cloudName},
                ],
            },
        }

        if self.verbose:
            print(f"Creating credential {credName}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class destroyCredential(SDKCommon):
    """This class destroys a credential. Use with caution, as there's no going back."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-credential+json"
        self.headers["Content-Type"] = "application/astra-credential+json"

    def main(self, credentialID):

        endpoint = f"core/v1/credentials/{credentialID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Deleting: {credentialID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class addCluster(SDKCommon):
    """This class adds an (ACC) Kubernetes cluster into the 'unmanaged' cluster list,
    after which it can then be changed from an unmanged to a managed cluster."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-cluster+json"
        self.headers["Content-Type"] = "application/astra-cluster+json"

    def main(self, cloudID, credentialID):

        endpoint = f"topology/v1/clouds/{cloudID}/clusters"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-cluster",
            "version": "1.1",
            "credentialID": credentialID,
        }

        if self.verbose:
            print(f"Adding cluster from credential: {credentialID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getReplicationpolicies(SDKCommon):
    """Get all the Replication policies (aka snap mirror / app mirror)"""

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
        if self.apps is False:
            print("Call to getApps() failed")
            return False

        endpoint = "k8s/v1/appMirrors"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting replication policies...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            replPolicies = super().jsonifyResults(ret)
            # Add custom app name entry
            for app in self.apps["items"]:
                for repl in replPolicies["items"]:
                    if app["id"] == repl["sourceAppID"]:
                        repl["sourceAppName"] = app["name"]
                    elif app["id"] == repl["destinationAppID"]:
                        repl["destinationAppName"] = app["name"]
            # Deep copy to remove items that don't match appFilter
            replCooked = copy.deepcopy(replPolicies)
            if appFilter:
                for counter, repl in enumerate(replPolicies.get("items")):
                    if (
                        appFilter != repl.get("sourceAppName")
                        and appFilter != repl.get("destinationAppName")
                        and appFilter != repl.get("sourceAppID")
                        and appFilter != repl.get("destinationAppID")
                    ):
                        replCooked["items"].remove(replPolicies["items"][counter])

            if self.output == "json":
                dataReturn = replCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(replCooked)
            elif self.output == "table":
                tabHeader = [
                    "replicationID",
                    "sourceAppID",
                    "state",
                    "sourceNamespace",
                    "destNamespace",
                ]
                tabData = []
                for repl in replCooked["items"]:
                    sourceNS = ""
                    destNS = ""
                    if repl.get("namespaceMapping"):
                        for ns in repl["namespaceMapping"]:
                            if ns["clusterID"] == repl["sourceClusterID"]:
                                sourceNS = ", ".join(ns["namespaces"])
                            elif ns["clusterID"] == repl["destinationClusterID"]:
                                destNS = ", ".join(ns["namespaces"])
                    tabData.append(
                        [
                            repl["id"],
                            repl["sourceAppID"],
                            repl["state"],
                            sourceNS,
                            destNS,
                        ]
                    )
                dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class createReplicationpolicy(SDKCommon):
    """Create a replication policy for a source app to a destination cluster.
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
        self.headers["accept"] = "application/astra-appMirror+json"
        self.headers["Content-Type"] = "application/astra-appMirror+json"

    def main(
        self,
        sourceAppID,
        destinationClusterID,
        namespaceMapping,
        destinationStorageClass=None,
    ):

        endpoint = "k8s/v1/appMirrors"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appMirror",
            "version": "1.0",
            "sourceAppID": sourceAppID,
            "destinationClusterID": destinationClusterID,
            "namespaceMapping": namespaceMapping,
            "stateDesired": "established",
        }
        if destinationStorageClass:
            data["storageClasses"] = destinationStorageClass

        if self.verbose:
            print(f"Creating replication policy for app: {sourceAppID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class updateReplicationpolicy(SDKCommon):
    """Update a replication policy.  Intended to reverse, resync, or fail over
    the replication.  This class does no validation of the arguments, leaving
    that to the API call itself.  toolkit.py can be used as a guide as to
    what the API requirements are in case the swagger isn't sufficient.
    """

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        # self.headers["accept"] = "application/astra-appMirror+json"
        self.headers["Content-Type"] = "application/astra-appMirror+json"

    def main(
        self,
        replicationID,
        stateDesired,
        sourceAppID=None,
        sourceClusterID=None,
        destinationAppID=None,
        destinationClusterID=None,
    ):

        endpoint = f"k8s/v1/appMirrors/{replicationID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appMirror",
            "version": "1.0",
            "stateDesired": stateDesired,
        }
        if destinationAppID:
            data["destinationAppID"] = destinationAppID
        if destinationClusterID:
            data["destinationClusterID"] = destinationClusterID
        if sourceAppID:
            data["sourceAppID"] = sourceAppID
        if sourceClusterID:
            data["sourceClusterID"] = sourceClusterID

        if self.verbose:
            print(f"Updating replication policy: {replicationID}")
            self.printVerbose(url, "PUT", self.headers, data, params)

        ret = super().apicall("put", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class destroyReplicationpolicy(SDKCommon):
    """This class destroys a replication policy"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-appMirror+json"
        self.headers["Content-Type"] = "application/astra-appMirror+json"

    def main(self, replicationID):

        endpoint = f"k8s/v1/appMirrors/{replicationID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Deleting: {replicationID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getEntitlements(SDKCommon):
    """Get the Astra Control entitlements, which can be used to determine if it's
    an Astra Control Service or Center environment."""

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

        endpoint = "core/v1/entitlements"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting entitlements...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            entitlements = super().jsonifyResults(ret)
            if self.output == "json":
                dataReturn = entitlements
            elif self.output == "yaml":
                dataReturn = yaml.dump(entitlements)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["entitlementID", "product", "type", "value", "consumption"],
                    [
                        "id",
                        "product",
                        "entitlementType",
                        "entitlementValue",
                        "entitlementConsumption",
                    ],
                    entitlements,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getUsers(SDKCommon):
    """Get all the users in Astra Control"""

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

    def main(self, nameFilter=None):

        endpoint = "core/v1/users"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting users...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            users = super().jsonifyResults(ret)
            # Add custom fullName entry
            for user in users["items"]:
                if not user.get("fullName"):
                    user["fullName"] = user.get("firstName") + " " + user.get("lastName")
            usersCooked = copy.deepcopy(users)
            if nameFilter:
                for counter, user in enumerate(users.get("items")):
                    if (
                        nameFilter.lower() not in user.get("firstName").lower()
                        and nameFilter.lower() not in user.get("lastName").lower()
                    ):
                        usersCooked["items"].remove(users["items"][counter])

            if self.output == "json":
                dataReturn = usersCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(usersCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["userID", "name", "email", "authProvider", "state"],
                    ["id", "fullName", "email", "authProvider", "state"],
                    usersCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class getBuckets(SDKCommon):
    """Get all of the buckets in Astra Control"""

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

    def main(self, nameFilter=None, provider=None):

        endpoint = "topology/v1/buckets"
        url = self.base + endpoint

        data = {}
        params = {}

        if self.verbose:
            print("Getting buckets...")
            self.printVerbose(url, "GET", self.headers, data, params)

        ret = super().apicall("get", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            buckets = super().jsonifyResults(ret)
            bucketsCooked = copy.deepcopy(buckets)
            for counter, bucket in enumerate(buckets.get("items")):
                if nameFilter and nameFilter.lower() not in bucket.get("name").lower():
                    bucketsCooked["items"].remove(buckets["items"][counter])
                elif provider and provider != bucket.get("provider"):
                    bucketsCooked["items"].remove(buckets["items"][counter])

            if self.output == "json":
                dataReturn = bucketsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(bucketsCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["bucketID", "name", "credentialID", "provider", "state"],
                    ["id", "name", "credentialID", "provider", "state"],
                    bucketsCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class manageBucket(SDKCommon):
    """Manage an object storage resource for storing backups.
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
        self.headers["accept"] = "application/astra-bucket+json"
        self.headers["Content-Type"] = "application/astra-bucket+json"

    def main(self, name, credentialID, provider, bucketParameters):

        endpoint = "topology/v1/buckets"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-bucket",
            "version": "1.1",
            "name": name,
            "credentialID": credentialID,
            "provider": provider,
            "bucketParameters": bucketParameters,
        }

        if self.verbose:
            print(f"Creating bucket {name} based on credential {credentialID}")
            self.printVerbose(url, "POST", self.headers, data, params)

        ret = super().apicall("post", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False


class unmanageBucket(SDKCommon):
    """This class unmanages / removes a bucket"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-bucket+json"
        self.headers["Content-Type"] = "application/astra-bucket+json"

    def main(self, bucketID):

        endpoint = f"topology/v1/buckets/{bucketID}"
        url = self.base + endpoint
        params = {}
        data = {}

        if self.verbose:
            print(f"Removing bucket {bucketID}")
            self.printVerbose(url, "DELETE", self.headers, data, params)

        ret = super().apicall("delete", url, data, self.headers, params, self.verifySSL)

        if self.verbose:
            print(f"API HTTP Status Code: {ret.status_code}")
            print()

        if ret.ok:
            if not self.quiet:
                print("Bucket unmanaged")
            return True
        else:
            if not self.quiet:
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"Error text: {ret.text}")
            return False
