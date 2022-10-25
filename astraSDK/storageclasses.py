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
from .clouds import getClouds
from .clusters import getClusters


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
                ["storageclassName", "storageclassID", "clusterName", "clusterID", "cloudType"],
                ["name", "id", "clusterName", "clusterID", "cloudType"],
                storageClasses,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn
