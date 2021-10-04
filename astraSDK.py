#!/usr/bin/env python
"""
   Copyright 2021 NetApp, Inc

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

import inspect
import os
import sys
import time
import yaml
from termcolor import colored
import requests
from urllib3 import disable_warnings


class getConfig:
    """In order to make API calls to Astra Control we need to know which Astra Control instance
    to connect to, and the credentials to make calls.  This info is found in config.yaml,
    which we search for in the following four places:
    1) The directory that toolkit.py in located in
    2) ~/.config/astra-toolkits/
    3) /etc/astra-toolkits/
    4) The directory pointed to by the shell env var ASTRATOOLKITS_CONF

    Note that astra_project is used to construct an URL assuming it will be
    Astra Control Service.  This will need to get modified in the future to
    handle arbitrary Astra Control Center URLs, and probably to handle self signed SSL
    certs as well.
    """

    def __init__(self):
        path = sys.argv[0] or inspect.getfile(getConfig)
        self.conf = None
        for loc in (
            os.path.realpath(os.path.dirname(path)),
            os.path.join(os.path.expanduser("~"), ".config", "astra-toolkits"),
            "/etc/astra-toolkits",
            os.environ.get("ASTRATOOLKITS_CONF"),
        ):
            # loc could be None, which would blow up os.path.join()
            if loc:
                configFile = os.path.join(loc, "config.yaml")
            else:
                continue
            try:
                if os.path.isfile(configFile):
                    with open(configFile, "r") as f:
                        self.conf = yaml.safe_load(f)
                        break
            except IOError:
                continue
            except yaml.YAMLError:
                print("%s not valid YAML" % configFile)
                continue

        if self.conf is None:
            print("config.yaml not found.")
            sys.exit(4)

        for item in ["astra_project", "uid", "headers"]:
            try:
                assert self.conf.get(item) is not None
            except AssertionError:
                print("astra_project is a required field in %s" % configFile)
                sys.exit(3)

        if "." in self.conf.get("astra_project"):
            self.base = "https://%s/accounts/%s/" % (
                self.conf.get("astra_project"),
                self.conf.get("uid"),
            )
        else:
            self.base = "https://%s.astra.netapp.io/accounts/%s/" % (
                self.conf.get("astra_project"),
                self.conf.get("uid"),
            )
        self.headers = self.conf.get("headers")

        if self.conf.get("verifySSL") is False:
            disable_warnings()
            self.verifySSL = False
        else:
            self.verifySSL = True

    def main(self):
        return {
            "base": self.base,
            "headers": self.headers,
            "verifySSL": self.verifySSL,
        }


class getApps:
    """List all apps known to Astra.
    Discovered=True means managedState="managed"
    Discovered=False means managedState="unmanaged"
    source provides filtering for appDefnSource.  This is useful for
    finding top level namespaces.
    namespace provides filtering for namespace.  Useful for "find all apps
    in the namespace named <X>

    Note that there is an API endpoint that will just list managedApps.  However
    it has the same return value as topology/v1/apps when filtering for
    managedState="managed"

    One thing this class won't do is list all of the managed and unmanaged apps.
    """

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")

    def main(self, discovered=False, source=None, namespace=None, cluster=None):
        endpoint = "topology/v1/apps"
        params = {
            "include": "name,id,clusterName,clusterID,namespace,state,managedState,appDefnSource"
        }
        url = self.base + endpoint
        data = {}

        # self.quiet = True if the CLI was run with -q or
        # we've been imported and called as a library
        if not self.quiet:
            print()
            print("Listing Apps...")
            print()
            print(colored("API URL: %s" % url, "green"))
        try:
            ret = requests.get(
                url,
                data=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if not self.quiet:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()
        if ret.ok:
            try:
                results = ret.json()
            except ValueError:
                print("Results contained illegal JSON")
                results = None
            """
            "name,id,clusterName,clusterID,namespace,state,managedState,appDefnSource"
            self.results = {'items':
                [['kube-system', '65ae3322-a1d1-4287-8d01-a3180e7d4ff4',
                  'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                  'kube-system', 'running', 'unmanaged', 'other'],
                 ['trident', '90995ad0-62c6-40c4-a5e3-57727b272385',
                  'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                  'trident', 'running', 'unmanaged', 'other'],
                 ['kube-system', 'b6356386-29b6-4790-abe9-cfe76276e1fa',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'kube-system', 'running', 'unmanaged', 'other'],
                 ['trident', '9af1931d-da02-4662-824c-71bc32cfa576',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'trident', 'running', 'unmanaged', 'other'],
                 ['jp3k', '739e7b1f-a71a-42bd-ac6f-db3ff9131133',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'jp3k', 'running', 'unmanaged', 'namespace'],
                 ['wp-mariadb', '697d2a64-61f0-4958-b746-13248be6e6a1',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'jp3k', 'running', 'managed', 'helm'],
                 ['wp-wordpress', 'ee7e683c-7532-4f79-9c4b-3e26d8ece391',
                  'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                  'jp3k', 'running', 'unmanaged', 'helm']],
                            'metadata': {}}
            """
            apps = {}
            for item in results.get("items"):
                # make item[1] the key in self.apps
                if item[1] not in apps:
                    appID = item.pop(1)
                    apps[appID] = item
            """
            apps:
                {'65ae3322-a1d1-4287-8d01-a3180e7d4ff4':
                    ['kube-system', 'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                     'kube-system', 'running', 'unmanaged', 'other'],
                 '90995ad0-62c6-40c4-a5e3-57727b272385':
                    ['trident', 'cluster-1-jp', '29df26ee-7a8e-4ed9-a76c-d49f39d54185',
                     'trident', 'running', 'unmanaged', 'other'],
                 'b6356386-29b6-4790-abe9-cfe76276e1fa':
                    ['kube-system', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'kube-system', 'running', 'unmanaged', 'other'],
                 '9af1931d-da02-4662-824c-71bc32cfa576':
                    ['trident', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'trident', 'running', 'unmanaged', 'other'],
                 '739e7b1f-a71a-42bd-ac6f-db3ff9131133':
                    ['jp3k', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'jp3k', 'running', 'unmanaged', 'namespace'],
                 '697d2a64-61f0-4958-b746-13248be6e6a1':
                    ['wp-mariadb', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'jp3k', 'running', 'managed', 'helm'],
                 'ee7e683c-7532-4f79-9c4b-3e26d8ece391':
                    ['wp-wordpress', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
                     'jp3k', 'running', 'unmanaged', 'helm']}
            """
            systemApps = ["trident", "kube-system"]
            if discovered:
                managedFilter = "unmanaged"
            else:
                managedFilter = "managed"

            # There's really 16 cases here.  managed or unmanaged, each with eight combinations
            # of source, namespace, and cluster
            # source    |y|n|
            # namespace |y|n|
            # cluster   |y|n|
            if source:
                if namespace:
                    if cluster:
                        # case 1: filter on source, namespace, and cluster
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[1] == cluster
                            and v[3] == namespace
                            and v[5] == managedFilter
                            and v[6] == source
                        }
                    else:
                        # case 2: filter on source, namespace
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[3] == namespace
                            and v[5] == managedFilter
                            and v[6] == source
                        }
                else:
                    if cluster:
                        # case 3: filter on source, cluster
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[1] == cluster
                            and v[5] == managedFilter
                            and v[6] == source
                        }
                    else:
                        # case 4: filter on source
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[5] == managedFilter
                            and v[6] == source
                        }
            else:
                if namespace:
                    if cluster:
                        # case 5: filter on namespace, cluster
                        if namespace:
                            appsCooked = {
                                k: v
                                for (k, v) in apps.items()
                                if v[0] not in systemApps
                                and v[1] == cluster
                                and v[3] == namespace
                                and v[5] == managedFilter
                            }
                    else:
                        # case 6: filter on namespace
                        if namespace:
                            appsCooked = {
                                k: v
                                for (k, v) in apps.items()
                                if v[0] not in systemApps
                                and v[3] == namespace
                                and v[5] == managedFilter
                            }
                else:
                    if cluster:
                        # case 7: filtering on cluster, but not source or namespace
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps
                            and v[1] == cluster
                            and v[5] == managedFilter
                        }
                    else:
                        # case 8: not filtering on source, namespace, OR cluster
                        appsCooked = {
                            k: v
                            for (k, v) in apps.items()
                            if v[0] not in systemApps and v[5] == managedFilter
                        }

            if not self.quiet:
                print("apps:")
                for item in appsCooked:
                    print(
                        "\tappName: %s\t appID: %s\t clusterName: %s\t namespace: %s\t state: %s"
                        % (
                            appsCooked[item][0],
                            item,
                            appsCooked[item][1],
                            appsCooked[item][3],
                            appsCooked[item][4],
                        )
                    )
                print()
            return appsCooked
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class getBackups:
    """Iterate over every managed app, and list all of it's backups.
    Failure reporting is not implimented, failure to list backups for
    one (or more) of N many apps just results in an empty list of backups
    for that app.
    """

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.apps = getApps().main()

    def main(self, appFilter=None):
        """self.apps = {'739e7b1f-a71a-42bd-ac6f-db3ff9131133':
            ['jp3k', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
             'jp3k', 'running', 'managed', 'namespace'],
        '697d2a64-61f0-4958-b746-13248be6e6a1':
            ['wp-mariadb', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
             'jp3k', 'running', 'managed', 'helm'],
        'ee7e683c-7532-4f79-9c4b-3e26d8ece391':
            ['wp-wordpress', 'cluster-2-jp', 'c4ee1e0f-96d5-4746-a415-e58285b403eb',
             'jp3k', 'running', 'managed', 'helm']}
        """
        backups = {}
        for app in self.apps:
            if appFilter:
                if self.apps[app][0] != appFilter:
                    continue
            endpoint = "k8s/v1/managedApps/%s/appBackups" % app  # appID
            url = self.base + endpoint

            data = {}
            params = {"include": "name,id,state,metadata"}

            if not self.quiet:
                print()
                print("Listing Backups for %s %s" % (app, self.apps[app][0]))
                print()
                print(colored("API URL: %s" % url, "green"))
            try:
                ret = requests.get(
                    url,
                    data=data,
                    headers=self.headers,
                    params=params,
                    verify=self.verifySSL,
                )
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            if not self.quiet:
                print("API HTTP Status Code: %s" % ret.status_code)
                print()
            if ret.ok:
                try:
                    results = ret.json()
                except ValueError:
                    print("response contained invalid JSON")
                    continue
                # Remember this is on a per AppID basis
                """results:
                     {'items':
                        [['hourly-rlezp-xsxmz',
                          '493c862d-71a9-4d47-87d3-eab9006c726f',
                          'completed', {'labels': [],
                                        'creationTimestamp': '2021-08-16T17:00:01Z',
                                        'modificationTimestamp': '2021-08-16T17:00:01Z',
                                        'createdBy': '70fa19ad-eb95-4d1c-b5fb-76b7f4214e6c'}]],
                                        'metadata': {}}
                """
                backups[app] = {}
                for item in results["items"]:
                    backupName = item[0]
                    backupID = item[1]
                    backupState = item[2]
                    # Strip off the trailing Z from the timestamp.  We know it's UTC and the
                    # python library we use to process datetimes doesn't handle the
                    # Zulu time convention that Astra gives us.
                    backupTimeStamp = item[3].get("creationTimestamp")[:-1]
                    # TODO: the backupName is just a label and Astra can have
                    # multiple backups of an app with the same name.
                    # This should be switched to have the backupID as the key.
                    if backupName not in backups[app]:
                        backups[app][backupName] = [
                            backupID,
                            backupState,
                            backupTimeStamp,
                        ]
                if not self.quiet:
                    print("Backups:")
                    for item in backups[app]:
                        print(
                            "\tbackupName: %s\t backupID: %s\t backupState: %s"
                            % (
                                item,
                                backups[app][item][0],
                                backups[app][item][1],
                            )
                        )
                        print()
            else:
                continue
        if not self.quiet:
            print(backups)
        else:
            return backups


class takeBackup:
    """Take a backup of an app.  An AppID and backupName is provided and
    either the result JSON is returned or the backupID of the newly created
    backup is returned."""

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.headers["accept"] = "application/astra-appBackup+json"
        self.headers["Content-Type"] = "application/astra-appBackup+json"

    def main(self, appID, backupName):
        endpoint = "k8s/v1/managedApps/%s/appBackups" % appID
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appBackup",
            "version": "1.0",
            "name": backupName,
        }
        try:
            ret = requests.post(
                url,
                json=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None
            if not self.quiet:
                print(results)
            else:
                return results.get("id") or True
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class cloneApp:
    """Clone a backup into a new app, in a new namespace.  Note that Astra doesn't
    currently support in place restores.

    Either backupID or sourceAppID is required.

    The sourceClusterID is something you'd think would be optional, but it
    is required as well.  Even worse, Astra knows what the (only) correct answer
    is and requires you to provide it anyways.

    Namespace is the new namespace that Astra will create to put the new app into.
    It must not exist on the destination cluster or the clone will fail.

    clusterID identifies the cluster for the new clone.  It's perfectly legal to
    clone an app to the same cluster it is running on; in which case clusterID ==
    sourceClusterID.

    This class doesn't try to validate anything you pass it, if you give it garbage
    for any parameters the clone operation will fail.
    """

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/astra-managedApp+json"

    def main(
        self,
        cloneName,
        clusterID,
        sourceClusterID,
        namespace,
        backupID=None,
        sourceAppID=None,
    ):
        assert backupID or sourceAppID

        endpoint = "k8s/v1/managedApps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-managedApp",
            "version": "1.0",
            "name": cloneName,
            "clusterID": clusterID,
            "sourceClusterID": sourceClusterID,
            "namespace": namespace,
        }
        if sourceAppID:
            data["sourceAppID"] = sourceAppID
        if backupID:
            data["backupID"] = backupID

        try:
            ret = requests.post(
                url,
                json=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None

            if not self.quiet:
                print(results)
            else:
                return results
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class getClusters:
    """Iterate over the clouds and list the clusters in each."""

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.clouds = getClouds(quiet=True).main()

    def main(self, hideManaged=False, hideUnmanaged=False):
        clusters = {}
        for cloud in self.clouds:
            endpoint = "topology/v1/clouds/%s/clusters" % cloud
            url = self.base + endpoint
            data = {}
            params = {}

            if not self.quiet:
                print()
                print(
                    "Getting clusters in cloud %s (%s)..."
                    % (cloud, self.clouds[cloud][0])
                )
                print()
                print(colored("API URL: %s" % url, "green"))
                print()
            try:
                ret = requests.get(
                    url,
                    data=data,
                    headers=self.headers,
                    params=params,
                    verify=self.verifySSL,
                )
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            if not self.quiet:
                print("API HTTP Status Code: %s" % ret.status_code)
                print()
            if ret.ok:
                try:
                    results = ret.json()
                except ValueError as e:
                    print("response contained invalid JSON: %s" % e)
                    results = None
                for item in results["items"]:
                    if item.get("id") not in clusters:
                        if hideManaged:
                            if item.get("managedState") == "managed":
                                continue
                        if hideUnmanaged:
                            if item.get("managedState") == "unmanaged":
                                continue
                        clusters[item.get("id")] = [
                            item.get("name"),
                            item.get("clusterType"),
                            item.get("managedState"),
                            cloud,
                        ]
        if not self.quiet:
            print("clusters:")
            for item in clusters:
                print(
                    "\tclusterName: %s\t clusterID: %s\tclusterType: %s\tmanagedState: %s"
                    % (
                        clusters[item][0],
                        item,
                        clusters[item][1],
                        clusters[item][2],
                    )
                )
            print()
        else:
            return clusters


class createProtectionpolicy:
    """Create a backup or snapshot policy on an appID.
    The rules of how dayOfWeek, dayOfMonth, hour, and minute
    need to be set vary based on whether granularity is set to
    hourly, daily, weekly, or monthly
    This class does no validation of the arguments, leaving that
    to the API call itself.  toolkit.py can be used as a guide as to
    what the API requirements are in case the swagger isn't sufficient.
    """

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.headers["accept"] = "application/astra-schedule+json"
        self.headers["Content-Type"] = "application/astra-schedule+json"

    def main(
        self,
        granularity,
        backupRetention,
        snapshotRetention,
        dayOfWeek,
        dayOfMonth,
        hour,
        minute,
        appID,
    ):
        endpoint = "k8s/v1/managedApps/%s/schedules" % appID
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-schedule",
            "version": "1.0",
            "backupRetention": backupRetention,
            "dayOfMonth": dayOfMonth,
            "dayOfWeek": dayOfWeek,
            "enabled": "true",
            "granularity": granularity,
            "hour": hour,
            "minute": minute,
            "name": "%s schedule" % granularity,
            "snapshotRetention": snapshotRetention,
        }
        try:
            ret = requests.post(
                url,
                json=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None
            if not self.quiet:
                print(results)
            return True
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class manageApp:
    """This class switches a discovered app to a managed app."""

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.headers["accept"] = "application/astra-managedApp+json"
        self.headers["Content-Type"] = "application/managedApp+json"

    def main(self, appID):
        endpoint = "k8s/v1/managedApps"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-managedApp",
            "version": "1.1",
            "id": appID,
        }
        try:
            ret = requests.post(
                url,
                json=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None
            if not self.quiet:
                print(results)
            return True
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class takeSnap:
    """Take a snapshot of an app.  An AppID and snapName is provided and
    either the result JSON is returned or the snapID of the newly created
    backup is returned."""

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.headers["accept"] = "application/astra-appSnap+json"
        self.headers["Content-Type"] = "application/astra-appSnap+json"

    def main(self, appID, snapName):
        endpoint = "k8s/v1/managedApps/%s/appSnaps" % appID
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-appSnap",
            "version": "1.0",
            "name": snapName,
        }
        try:
            ret = requests.post(
                url,
                json=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None
            if not self.quiet:
                print(results)
            else:
                return results.get("id") or True
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class getSnaps:
    """Iterate over every managed app, and list all of it's snapshots.
    Failure reporting is not implimented, failure to list snapshots for
    one (or more) of N many apps just results in an empty list of snapshots
    for that app.
    """

    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.apps = getApps().main()

    def main(self, appFilter=None):
        snaps = {}
        for app in self.apps:
            if appFilter:
                if self.apps[app][0] != appFilter:
                    continue
            endpoint = "k8s/v1/managedApps/%s/appSnaps" % app
            url = self.base + endpoint

            data = {}
            params = {"include": "name,id,state"}

            if not self.quiet:
                print()
                print("Listing Snapshots for %s" % app)
                print()
                print(colored("API URL: %s" % url, "green"))
                print(colored("API Method: GET", "green"))
                print(colored("API Headers: %s" % self.headers, "green"))
                print(colored("API data: %s" % data, "green"))
                print(colored("API params: %s" % params, "green"))
                print()
                time.sleep(1)
                print("Making API Call", end="", flush=True)
                for i in range(3):
                    print(".", end="", flush=True)
                    time.sleep(1)
                print()
            try:
                ret = requests.get(
                    url,
                    data=data,
                    headers=self.headers,
                    params=params,
                    verify=self.verifySSL,
                )
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            if not self.quiet:
                print("API HTTP Status Code: %s" % ret.status_code)
                print()
            if ret.ok:
                try:
                    results = ret.json()
                except ValueError:
                    print("response contained invalid JSON")
                    continue
                snaps[app] = {}
                for item in results["items"]:
                    appName = item[0]
                    snapID = item[1]
                    snapState = item[2]
                    if appName not in snaps[app]:
                        snaps[app][appName] = [
                            snapID,
                            snapState,
                        ]
                if not self.quiet:
                    print("Snapshots:")
                    for item in snaps[app]:
                        print(
                            "\tsnapshotName: %s\t snapshotID: %s\t snapshotState: %s"
                            % (
                                item,
                                snaps[app][item][0],
                                snaps[app][item][1],
                            )
                        )
                        print()
            else:
                continue

        if not self.quiet:
            print(snaps)
        else:
            return snaps


class getClouds:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")

    def main(self):
        endpoint = "topology/v1/clouds"
        url = self.base + endpoint

        data = {}
        params = {"include": "id,name,state"}

        if not self.quiet:
            print()
            print("Listing clouds...")
            print()
            print(colored("API URL: %s" % url, "green"))
            print()
        try:
            ret = requests.get(
                url,
                data=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if not self.quiet:
            print("API HTTP Status Code: %s" % ret.status_code)
            print()
        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None
            clouds = {}
            for item in results["items"]:
                if item.get("id") not in clouds:
                    clouds[item.get("id")] = [
                        item.get("name"),
                        item.get("cloudType"),
                    ]
            if not self.quiet:
                print("clouds:")
                for item in clouds:
                    print(
                        "\tcloudName: %s\t cloudID: %s\tcloudType: %s"
                        % (
                            clouds[item][0],
                            item,
                            clouds[item][1],
                        )
                    )
                print()
            return clouds
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False


class getStorageClasses:
    def __init__(self, quiet=True):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.clouds = getClouds().main()
        self.clusters = getClusters().main()

    def main(self):
        storageClasses = {}
        for cloud in self.clouds:
            storageClasses[cloud] = {}
            for cluster in self.clusters:
                # exclude invalid combinations of cloud/cluster
                if self.clusters[cluster][3] != cloud:
                    continue
                storageClasses[cloud][cluster] = {}
                endpoint = "topology/v1/clouds/%s/clusters/%s/storageClasses" % (
                    cloud,
                    cluster,
                )
                url = self.base + endpoint

                data = {}
                params = {}

                if not self.quiet:
                    print()
                    print(
                        "Listing StorageClasses for cluster: %s in cloud: %s"
                        % (cluster, cloud)
                    )
                    print()
                    print(colored("API URL: %s" % url, "green"))
                    print(colored("API Method: GET", "green"))
                    print(colored("API Headers: %s" % self.headers, "green"))
                    print(colored("API data: %s" % data, "green"))
                    print(colored("API params: %s" % params, "green"))
                    print()
                    time.sleep(1)
                    print("Making API Call", end="", flush=True)
                    for i in range(3):
                        print(".", end="", flush=True)
                        time.sleep(1)
                    print()
                try:
                    ret = requests.get(
                        url,
                        data=data,
                        headers=self.headers,
                        params=params,
                        verify=self.verifySSL,
                    )
                except requests.exceptions.RequestException as e:
                    raise SystemExit(e)

                if not self.quiet:
                    print("API HTTP Status Code: %s" % ret.status_code)
                    print()
                if ret.ok:
                    try:
                        results = ret.json()
                    except ValueError:
                        print("response contained invalid JSON")
                        continue
                    for entry in results.get("items"):
                        storageClasses[cloud][cluster][entry.get("id")] = entry.get(
                            "name"
                        )

        if not self.quiet:
            for cloud in storageClasses:
                print("cloud: %s (%s)" % (cloud, self.clouds[cloud][0]))
                for cluster in storageClasses[cloud]:
                    print("\tcluster: %s (%s)" % (cluster, self.clusters[cluster][0]))
                    for storageClass in storageClasses[cloud][cluster]:
                        print(
                            "\t\tstorage class: %s (%s)"
                            % (
                                storageClass,
                                storageClasses[cloud][cluster][storageClass],
                            )
                        )
        return storageClasses


class manageCluster:
    """This class switches an unmanaged cluster to a managed cluster"""

    def __init__(self, quiet=False):
        self.quiet = quiet
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")
        self.headers["accept"] = "application/astra-managedCluster+json"
        self.headers["Content-Type"] = "application/managedCluster+json"

    def main(self, clusterID, storageClassID):
        endpoint = "topology/v1/managedClusters"
        url = self.base + endpoint
        params = {}
        data = {
            "defaultStorageClass": storageClassID,
            "id": clusterID,
            "type": "application/astra-managedCluster",
            "version": "1.0",
        }
        try:
            ret = requests.post(
                url,
                json=data,
                headers=self.headers,
                params=params,
                verify=self.verifySSL,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if ret.ok:
            try:
                results = ret.json()
            except ValueError as e:
                print("response contained invalid JSON: %s" % e)
                results = None
            if not self.quiet:
                print(results)
            return True
        else:
            if not self.quiet:
                print(ret.status_code)
                print(ret.reason)
            return False
