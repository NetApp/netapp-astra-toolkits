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


class getClusters(SDKCommon):
    """Iterate over the clouds and list the clusters in each."""

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
        self.clouds = getClouds(quiet=True, verbose=verbose).main()

    def main(self, hideManaged=False, hideUnmanaged=False, nameFilter=None):
        clusters = {}
        clusters["items"] = []
        if self.clouds is False:
            print("Call to get clouds failed")
            return False
        if len(self.clouds["items"]) == 0:
            print("No clouds found")
            return True
        for cloud in self.clouds["items"]:
            endpoint = f"topology/v1/clouds/{cloud['id']}/clusters"
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
                for item in results["items"]:
                    if nameFilter and nameFilter not in item.get("name"):
                        continue
                    if hideManaged and item.get("managedState") == "managed":
                        continue
                    if hideUnmanaged and item.get("managedState") == "unmanaged":
                        continue
                    clusters["items"].append(item)

        if self.output == "json":
            dataReturn = clusters
        elif self.output == "yaml":
            dataReturn = yaml.dump(clusters)
        elif self.output == "table":
            dataReturn = self.basicTable(
                [
                    "clusterName",
                    "clusterID",
                    "clusterType",
                    "location",
                    "managedState",
                    "tridentState",
                    "tridentVersion",
                ],
                [
                    "name",
                    "id",
                    "clusterType",
                    "location",
                    "managedState",
                    "tridentManagedStateAllowed",
                    "tridentVersion",
                ],
                clusters,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


class manageCluster(SDKCommon):
    """This class switches an unmanaged cluster to a managed cluster"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedCluster+json"
        self.headers["Content-Type"] = "application/managedCluster+json"

    def main(self, clusterID, storageClassID=None):

        endpoint = "topology/v1/managedClusters"
        url = self.base + endpoint
        params = {}
        data = {
            "id": clusterID,
            "type": "application/astra-managedCluster",
            "version": "1.2",
        }
        if storageClassID:
            data["defaultStorageClass"] = storageClassID

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


class unmanageCluster(SDKCommon):
    """This class switches a managed cluster to an un managed cluster"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-managedCluster+json"
        self.headers["Content-Type"] = "application/managedCluster+json"
        self.clusters = getClusters().main()

    def main(self, clusterID):

        endpoint = f"topology/v1/managedClusters/{clusterID}"
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
                print("Cluster unmanaged")
            return True
        else:
            return False


class addCluster(SDKCommon):
    """This class adds an (ACC) Kubernetes cluster into the 'unmanaged' cluster list,
    after which it can then be changed from an unmanged to a managed cluster."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-cluster+json"
        self.headers["Content-Type"] = "application/astra-cluster+json"

    def main(self, cloudID, credentialID):

        endpoint = f"topology/v1/clouds/{cloudID}/clusters"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-cluster",
            "version": "1.1",
            "credentialID": credentialID,
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


class deleteCluster(SDKCommon):
    """This class deletes a cluster.  It's meant for ACC environments only, and should
    be called after unmanageCluster if it's an ACC-managed cluster."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-cluster+json"
        self.headers["Content-Type"] = "application/astra-cluster+json"

    def main(self, clusterID, cloudID):

        endpoint = f"topology/v1/clouds/{cloudID}/clusters/{clusterID}"
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
                print("Cluster deleted")
            return True
        else:
            return False
