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
from termcolor import colored

from .common import SDKCommon


class getApps(SDKCommon):
    """List all apps known to Astra.  With App 2.0 API spec in the Aug 2022 release, there's
    no longer a "discovered" or "ignored" construct with apps.  There's simply managed apps
    (which is what this class covers), or yet-to-be-managed (referred to as unmanaged) apps,
    which are handled by the getNamespaces class.

    Therefore this class cannot list all of the managed and unmanaged apps.
    """

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

    def main(
        self,
        namespace=None,
        nameFilter=None,
        cluster=None,
    ):
        """namespace: Filter by the namespace the app is in
        cluster: Filter by a specific k8s cluster"""

        endpoint = "k8s/v2/apps"
        params = {}
        url = self.base + endpoint
        data = {}

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
            apps = super().jsonifyResults(ret)
            appsCooked = copy.deepcopy(apps)
            """
            apps = {"items":[
                    {
                        "type": "application/astra-app",
                        "version": "2.0",
                        "id": "36ba2699-66dc-4ad1-949b-26c1108f42e2",
                        "name": "wordpress-app",
                        "namespaceScopedResources": [
                            {
                                "namespace": "wordpress",
                                "labelSelectors": []
                            }
                        ],
                        "state": "ready",
                        "lastResourceCollectionTimestamp": "2022-07-20T18:19:35Z",
                        "stateTransitions": [
                            { "to": ["pending"] },
                            { "to": ["provisioning"] },
                            { "from": "pending", "to": ["discovering", "failed"] },
                            { "from": "discovering", "to": ["ready", "failed"] },
                            {
                                "from": "ready",
                                "to": [ "discovering", "restoring", "unavailable", "failed"]
                            },
                            { "from": "unavailable", "to": ["ready", "restoring"] },
                            { "from": "provisioning", "to": ["discovering", "failed"] },
                            { "from": "restoring", "to": ["discovering", "failed"] }
                        ],
                        "stateDetails": [],
                        "protectionState": "none",
                        "protectionStateDetails": [],
                        "namespaces": [
                            "wordpress"
                        ],
                        "clusterName": "uscentral1-cluster",
                        "clusterID": "b81bdd8f-c2c7-40eb-a602-4af06d3c6e4d",
                        "clusterType": "gke",
                        "metadata": {
                            "labels": [],
                            "creationTimestamp": "2022-07-20T18:19:30Z",
                            "modificationTimestamp": "2022-07-20T18:20:36Z",
                            "createdBy": "12a5d9dd-851e-4235-af27-86c0b63bf3a9"
                        }
                    }],
                "metadata":{}
            }
            """

            # Loop through all apps and delete those that don't match filters
            for counter, app in enumerate(apps.get("items")):
                # If there's a given filter, delete non-matching values
                if namespace:
                    delApp = True
                    for ns in app["namespaces"]:
                        if ns == namespace:
                            delApp = False
                    if delApp:
                        appsCooked["items"].remove(apps["items"][counter])
                        continue
                if cluster and not (cluster == app["clusterName"] or cluster == app["clusterID"]):
                    appsCooked["items"].remove(apps["items"][counter])
                elif nameFilter and nameFilter not in app.get("name"):
                    appsCooked["items"].remove(apps["items"][counter])

            if self.output == "json":
                dataReturn = appsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(appsCooked)
            elif self.output == "table":
                tabHeader = [
                    "appName",
                    "appID",
                    "clusterName",
                    "namespace",
                    "state",
                ]
                tabData = []
                for app in appsCooked.get("items"):
                    tabData.append(
                        [
                            (
                                app["name"]
                                if "replicationSourceAppID" not in app
                                else app["name"] + colored(" (replication destination)", "blue")
                            ),
                            app["id"],
                            app["clusterName"],
                            ", ".join(app["namespaces"]),
                            app["state"],
                        ]
                    )
                dataReturn = tabulate(tabData, tabHeader, tablefmt="grid")

            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            return False


class manageApp(SDKCommon):
    """This class switches an unmanaged (aka undefined) app to a managed (aka defined) app.
    By default, it handles the simplest case, managing a single, entire namespace.

    Through the label argument (str), that single namespace can be filtered via a label selector.

    Any number of additional namespaces (and optional label selectors) can be provided through
    the addNamespaces argument, which must be a list of dictionaries:
        [{"namespace": "ns2"}, {"namespace": "ns3", "labelSelectors": ["app=name"]}]

    Any number of clusterScopedResources (and optional label selectors) can be provided through
    the clusterScopedResources argument, which must be a list of dictionaries:
        [{"GVK": {"group": "rbac.authorization.k8s.io", "kind": "ClusterRole", "version": "v1"},
          "labelSelectors": ["app=name"]}]

    There is no validation of this input, that instead is left to the calling method."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"

    def main(
        self,
        appName,
        namespace,
        clusterID,
        label=None,
        addNamespaces=None,
        clusterScopedResources=None,
    ):

        endpoint = "k8s/v2/apps"
        url = self.base + endpoint
        params = {}
        data = {
            "clusterID": clusterID,
            "name": appName,
            "namespaceScopedResources": [{"namespace": namespace}],
            "type": "application/astra-app",
            "version": "2.1",
        }
        if label:
            data["namespaceScopedResources"][0]["labelSelectors"] = [label]
        if addNamespaces:
            data["namespaceScopedResources"] += addNamespaces
        if clusterScopedResources:
            data["clusterScopedResources"] = clusterScopedResources

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


class unmanageApp(SDKCommon):
    """This class undefines a managed application."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"

    def main(self, appID):

        endpoint = f"k8s/v2/apps/{appID}"
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
                print("App unmanaged")
            return True
        else:
            return False


class cloneApp(SDKCommon):
    """Clone an app to a new app and namespace.
    Either backupID, snapshotID, or sourceAppID is required.
    The sourceClusterID is required as well.

    clusterID identifies the cluster for the new clone.  It's perfectly legal to
    clone an app to the same cluster it is running on; in which case clusterID ==
    sourceClusterID.

    This class doesn't try to validate anything you pass it, if you give it garbage
    for any parameters the clone operation will fail.
    """

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"

    def main(
        self,
        cloneName,
        clusterID,
        sourceClusterID,
        namespaceMapping=None,
        backupID=None,
        snapshotID=None,
        sourceAppID=None,
    ):
        assert backupID or snapshotID or sourceAppID

        endpoint = "k8s/v2/apps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-app",
            "version": "2.0",
            "name": cloneName,
            "clusterID": clusterID,
            "sourceClusterID": sourceClusterID,
        }
        if sourceAppID:
            data["sourceAppID"] = sourceAppID
        if backupID:
            data["backupID"] = backupID
        if snapshotID:
            data["snapshotID"] = snapshotID
        if namespaceMapping:
            data["namespaceMapping"] = namespaceMapping

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
            else:
                return results
        else:
            return False


class restoreApp(SDKCommon):
    """Restore a backup or snapshot of an app.
    Must pass in an AppID and either a snapshotID or a backupID
    Note that this is a destructive operation that overwrites the current AppID
    with the backup/snapshot.

    Also note that the return code this class returns is referring to submitting
    the restore job.  To know if the restore job itself succeeds or fails you
    need to monitor the state of the app, watching for it to switch from
    "restoring" to "running" or "failed".
    """

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return True/False
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-app+json"
        self.headers["Content-Type"] = "application/astra-app+json"
        self.headers["ForceUpdate"] = "true"

    def main(
        self,
        appID,
        backupID=None,
        snapshotID=None,
    ):
        assert backupID or snapshotID

        endpoint = f"k8s/v2/apps/{appID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-app",
            "version": "2.0",
        }
        if backupID:
            data["backupID"] = backupID
        elif snapshotID:
            data["snapshotID"] = snapshotID

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

        return True if ret.ok else False


class getAppAssets(SDKCommon):
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

    def main(self, appID):

        endpoint = f"k8s/v1/apps/{appID}/appAssets"
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
            assets = super().jsonifyResults(ret)
            if self.output == "json":
                dataReturn = assets
            elif self.output == "yaml":
                dataReturn = yaml.dump(assets)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["assetName", "assetType"],
                    ["assetName", "assetType"],
                    assets,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            return False
