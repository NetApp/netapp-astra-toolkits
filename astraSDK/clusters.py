#!/usr/bin/env python3
"""
   Copyright 2024 NetApp, Inc

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

import copy
import yaml
import json

from .common import SDKCommon
from .clouds import getClouds


class getClusters(SDKCommon):
    """Iterate over the clouds and list the clusters in each."""

    def __init__(self, quiet=True, verbose=False, output="json", config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        self.config = config
        super().__init__(config=config)
        self.clouds = getClouds(quiet=True, verbose=verbose, config=config).main()

    def main(self, hideManaged=False, hideUnmanaged=False, nameFilter=None):
        if hideUnmanaged:
            return getManagedClusters(
                quiet=self.quiet, verbose=self.verbose, output=self.output, config=self.config
            ).main(nameFilter=nameFilter)
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
                    clusters["items"].append(item)
            else:
                if not self.quiet:
                    super().printError(ret)
                continue

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
                    "state",
                    "managedState",
                    "defaultBucketID",
                ],
                [
                    "name",
                    "id",
                    "clusterType",
                    "location",
                    "state",
                    "managedState",
                    "defaultBucketID",
                ],
                clusters,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


class getManagedClusters(SDKCommon):
    """Call the managedClusters endpoint to get all managed clusters"""

    def __init__(self, quiet=True, verbose=False, output="json", config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        self.output = output
        super().__init__(config=config)

    def main(self, nameFilter=None):
        endpoint = "topology/v1/managedClusters"
        url = self.base + endpoint
        data = {}
        params = {}

        ret = super().apicall(
            "get",
            url,
            data,
            self.headers,
            params,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            clusters = super().jsonifyResults(ret)
            if nameFilter:
                filterCopy = copy.deepcopy(clusters)
                for counter, r in enumerate(filterCopy.get("items")):
                    if nameFilter not in self.recursiveGet("name", r):
                        clusters["items"].remove(filterCopy["items"][counter])

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
                        "state",
                        "managedState",
                        "tridentStateAllowed",
                    ],
                    [
                        "name",
                        "id",
                        "clusterType",
                        "location",
                        "state",
                        "managedState",
                        "tridentManagedStateAllowed",
                    ],
                    clusters,
                )

            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                super().printError(ret)
            return False


class manageCluster(SDKCommon):
    """This class switches an unmanaged cluster to a managed cluster"""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
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
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                super().printError(ret)
            return False


class unmanageCluster(SDKCommon):
    """This class switches a managed cluster to an un managed cluster"""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
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
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            if not self.quiet:
                print("Cluster unmanaged")
            return True
        else:
            if not self.quiet:
                super().printError(ret)
            return False


class addCluster(SDKCommon):
    """This class adds an (ACC) Kubernetes cluster into the 'unmanaged' cluster list,
    after which it can then be changed from an unmanged to a managed cluster."""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
        self.headers["accept"] = "application/astra-cluster+json"
        self.headers["Content-Type"] = "application/astra-cluster+json"

    def main(
        self, cloudID, credentialID=None, privateRouteID=None, name=None, connectorInstall=False
    ):
        if (not credentialID) and (not name or not connectorInstall):
            raise SystemExit(
                "Either credentialID or both of (name and connectorInstall) should be specified"
            )
        endpoint = f"topology/v1/clouds/{cloudID}/clusters"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-cluster",
            "version": "1.6",
        }
        if credentialID:
            data["credentialID"] = credentialID
        if privateRouteID:
            data["privateRouteID"] = privateRouteID
        if name:
            data["name"] = name
        if connectorInstall:
            data["connectorInstall"] = "pending"

        ret = super().apicall(
            "post",
            url,
            data,
            self.headers,
            params,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                super().printError(ret)
            return False


class deleteCluster(SDKCommon):
    """This class deletes a cluster.  It's meant for ACC environments only, and should
    be called after unmanageCluster if it's an ACC-managed cluster."""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
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
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            if not self.quiet:
                print(f"Cluster {clusterID} destroyed")
            return True
        else:
            if not self.quiet:
                super().printError(ret)
            return False


class updateCluster(SDKCommon):
    """This class updates a managed cluster, it is currently intended for updating the
    or defaultBucketID of a cluster, but has been created in a way to allow other kinds of
    updates in future versions."""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
        self.headers["Content-Type"] = "application/astra-managedCluster+json"

    def main(self, clusterID, defaultBucketID=None):
        endpoint = f"topology/v1/managedClusters/{clusterID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-managedCluster",
            "version": "1.6",
        }
        if defaultBucketID:
            data["defaultBucketID"] = defaultBucketID

        ret = super().apicall(
            "put",
            url,
            data,
            self.headers,
            params,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            results = super().jsonifyResults(ret)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            if not self.quiet:
                super().printError(ret)
            return False
