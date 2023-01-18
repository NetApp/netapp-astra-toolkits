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
            return False


class createCredential(SDKCommon):
    """Create a kubeconfig, S3, or cloud credential.  This class does not perform any validation
    of the inputs.  Please see toolkit.py for further examples if the swagger definition does
    not provide all the information you require.

    Cloud credentials must have a 'keyType' of 'generic' while also having the 'credType' label
    be 'service-account', so this class handles the discrepancy by accepting a 'keyType' of
    'service-account' as an input and modifying it to be 'generic' in the payload."""

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
        cloudName=None,
    ):

        endpoint = "core/v1/credentials"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-credential",
            "version": "1.1",
            "keyStore": keyStore,
            "keyType": ("generic" if keyType == "service-account" else keyType),
            "name": credName,
            "metadata": {
                "labels": [
                    {"name": "astra.netapp.io/labels/read-only/credType", "value": keyType},
                ],
            },
        }
        if cloudName:
            data["metadata"]["labels"].append(
                {"name": "astra.netapp.io/labels/read-only/cloudName", "value": cloudName}
            )

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
