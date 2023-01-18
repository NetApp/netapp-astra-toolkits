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
import copy
from tabulate import tabulate

from .common import SDKCommon
from .apps import getApps


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
        self.apps = getApps(quiet=True, verbose=verbose).main()

    def main(self, appFilter=None):
        if self.apps is False:
            print("Call to getApps() failed")
            return False

        endpoint = "k8s/v1/appMirrors"
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
            # Handle ACS environments
            if ret.text.strip():
                print(json.loads(ret.text).get("detail"))
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

        ret = super().apicall(
            "put",
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
