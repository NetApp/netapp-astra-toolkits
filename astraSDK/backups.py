#!/usr/bin/env python3
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

import yaml
import json

from .common import SDKCommon
from .apps import getApps


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
        self.apps = getApps(quiet=True, verbose=verbose).main()

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

            ret = super().apicall(
                "get",
                url,
                data,
                self.headers,
                params,
                self.verifySSL,
                quiet=self.quiet,
                verbose=self.verbose,
            )

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
                                ["backupName", "backupID", "backupState", "creationTimestamp"],
                                ["name", "id", "state", "metadata.creationTimestamp"],
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
                ["AppID", "backupName", "backupID", "backupState", "creationTimestamp"],
                ["appID", "name", "id", "state", "metadata.creationTimestamp"],
                backups,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


class takeBackup(SDKCommon):
    """Take a backup of an app.  An AppID and backupName are required fields,
    a bucketID and snpshotID are optional fields, and either the result JSON is
    returned or the backupID of the newly created backup is returned."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-appBackup+json"
        self.headers["Content-Type"] = "application/astra-appBackup+json"

    def main(self, appID, backupName, bucketID=None, snapshotID=None):

        endpoint = f"k8s/v1/apps/{appID}/appBackups"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appBackup",
            "version": "1.1",
            "name": backupName,
        }
        if bucketID:
            data["bucketID"] = bucketID
        if snapshotID:
            data["snapshotID"] = snapshotID

        ret = super().apicall(
            "post",
            url,
            data,
            self.headers,
            params,
            self.verifySSL,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results.get("id") or True
        else:
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

        ret = super().apicall(
            "delete",
            url,
            data,
            self.headers,
            params,
            self.verifySSL,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        return True if ret.ok else False
