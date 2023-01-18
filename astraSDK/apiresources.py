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
from tabulate import tabulate

from .common import SDKCommon
from .clusters import getClusters


class getApiResources(SDKCommon):
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

    def main(self, cluster=None):
        if self.clusters is False:
            print("getClusters().main() failed")
            return False
        if len(self.clusters["items"]) == 0:
            print("No clusters found")
            return True

        apiResources = {}
        apiResources["items"] = []
        for sCluster in self.clusters["items"]:
            # exclude non-matching clusters if cluster filter is provided
            if cluster and cluster != sCluster["id"] and cluster != sCluster["name"]:
                continue
            endpoint = f"topology/v1/managedClusters/{sCluster['id']}/apiResources"
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
                for entry in results.get("items"):
                    # Adding a custom clusterID key/value pair
                    if not entry.get("clusterID"):
                        entry["clusterID"] = sCluster["id"]
                    apiResources["items"].append(entry)

        if self.output == "json":
            dataReturn = apiResources
        elif self.output == "yaml":
            dataReturn = yaml.dump(apiResources)
        elif self.output == "table":
            tabHeader = ["group", "version", "kind", "clusterID"]
            tabData = []
            for resource in apiResources.get("items"):
                tabData.append(
                    [
                        resource["apiVersion"].split("/")[0],
                        resource["apiVersion"].split("/")[1],
                        resource["kind"],
                        resource["clusterID"],
                    ]
                )
            dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn
