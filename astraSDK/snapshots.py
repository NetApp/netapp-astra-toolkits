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
        self.apps = getApps(quiet=True, verbose=verbose).main()

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
                                [
                                    "snapshotName",
                                    "snapshotID",
                                    "snapshotState",
                                    "creationTimestamp",
                                ],
                                ["name", "id", "state", "metadata.creationTimestamp"],
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
                ["appID", "snapshotName", "snapshotID", "snapshotState", "creationTimestamp"],
                ["appID", "name", "id", "state", "metadata.creationTimestamp"],
                snaps,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


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
