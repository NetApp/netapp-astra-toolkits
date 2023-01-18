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
        self.apps = getApps(quiet=True, verbose=verbose).main()

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
            return results
        else:
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
