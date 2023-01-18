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

from .common import SDKCommon


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
            return False


class manageCloud(SDKCommon):
    """This class manages a cloud"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-cloud+json"
        self.headers["Content-Type"] = "application/astra-cloud+json"

    def main(self, cloudName, cloudType, credentialID=None, description=None, defaultBucketID=None):

        endpoint = "topology/v1/clouds"
        url = self.base + endpoint
        params = {}
        data = {
            "name": cloudName,
            "cloudType": cloudType,
            "type": "application/astra-cloud",
            "version": "1.0",
        }
        if credentialID:
            data["credentialID"] = credentialID
        if description:
            data["description"] = description
        if defaultBucketID:
            data["defaultBucketID"] = defaultBucketID

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


class unmanageCloud(SDKCommon):
    """This class unmanages a cloud"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-cloud+json"
        self.headers["Content-Type"] = "application/astra-cloud+json"

    def main(self, cloudID):

        endpoint = f"topology/v1/clouds/{cloudID}"
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

        if ret.ok:
            if not self.quiet:
                print("Cloud unmanaged")
            return True
        else:
            return False
