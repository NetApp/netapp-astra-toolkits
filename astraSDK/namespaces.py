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
from datetime import datetime, timedelta

from .common import SDKCommon
from .apps import getApps
from .clusters import getClusters


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
        self.clusters = getClusters(quiet=True, verbose=verbose).main()
        self.apps = getApps(quiet=True, verbose=verbose).main() if self.clusters else False

    def main(
        self,
        clusterID=None,
        nameFilter=None,
        showRemoved=False,
        unassociated=False,
        minuteFilter=False,
    ):
        if self.clusters is False:
            print("Call to getClusters().main() failed")
            return False
        elif self.apps is False:
            print("Call to getApps().main() failed")
            return False

        if clusterID:
            endpoint = f"topology/v1/clusters/{clusterID}/namespaces"
        else:
            endpoint = "topology/v1/namespaces"
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
            return False
