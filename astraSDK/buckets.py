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
                print("Bucket unmanaged")
            return True
        else:
            return False
