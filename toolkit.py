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

import astraSDK
import argparse
import subprocess
import sys
import time
import yaml


def userSelect(pickList):
    """pickList is a dictionary of keys that are objIDs and values that are a list.
    Print the items in the dictionary, have the user pick one
    then return the key (presumably an objID) of what they picked"""
    # Rather than just index the existing dictionary create a parallel dictionary
    # with the index and key of the passed in dict.
    # picklist = {"deadc0de": ["test-1", "gke"],
    #             "deadbeef": ["test-2", "aks"]
    #            }
    # choices_dict = {1: "deadc0de".
    #                 2: "deadbeef"
    #                }

    if not isinstance(pickList, dict):
        return False

    choicesDict = {}
    for counter, item in enumerate(pickList, start=1):
        if isinstance(pickList[item], list):
            choicesDict[counter] = item
            # the third %s prints lists with an arbitrary number of items
            print("%s:\t%s\t%s" % (counter, item, "\t".join(pickList[item])))
        else:
            print("Skipping key: %s with non-list value" % item)
    while True:
        ret = input("Select a line (1-%s): " % counter)
        try:
            # choicesDict.get() returns None if the index isn't
            # in the dict, the try/except catches cases where the
            # user enters something other than a number.
            objectID = choicesDict.get(int(ret))
            if objectID:
                return objectID
            else:
                continue
        except ValueError:
            continue


def updateHelm():
    """Check to see if the bitnami helm repo is installed
    If it is, get the name of the repo
    otherwise install it
    ignore_errors=True here because helm repo list returns 1 if there are no
    repos configured"""
    ret = run("helm repo list -o yaml", captureOutput=True, ignoreErrors=True)
    repos = {
        "https://charts.gitlab.io": None,
        "https://charts.bitnami.com/bitnami": None,
    }
    if ret != 1:
        retYaml = yaml.load(ret, Loader=yaml.SafeLoader)
        # [{'name': 'stable', 'url': 'https://charts.helm.sh/stable'},
        #  {'name': 'bitnami', 'url': 'https://charts.bitnami.com/bitnami'}
        # ]
        for repoUrlToMatch in repos:
            for item in retYaml:
                if item.get("url") == repoUrlToMatch:
                    repos[repoUrlToMatch] = item.get("name")
    for k, v in repos.items():
        if not v:
            repoName = k.split(".")[1]
            run("helm repo add %s %s" % (repoName, k))
            repos[k] = repoName

    run("helm repo update")
    chartsDict = {}
    for val in repos.values():
        charts = run("helm -o yaml search repo %s" % val, captureOutput=True)
        chartsYaml = yaml.load(charts, Loader=yaml.SafeLoader)
        for line in chartsYaml:
            chartsDict[(line.get("name").split("/")[1])] = val
    return chartsDict


def run(command, captureOutput=False, ignoreErrors=False):
    """Run an arbitrary shell command.  Our API is terrible.  If ignore_errors=False
    raise the SystemExit exception if the commands returns != 0 (e.g.: failure)
    If ignore_errors=True, return the shell return code if it is != 0
    If the shell return code is 0 (success) either return True or the contents of stdout, depending
    on whether capture_output is set to True or False"""
    command = command.split(" ")
    try:
        ret = subprocess.run(command, capture_output=captureOutput)
    except OSError as e:
        raise SystemExit("%s OSError: %s" % (command, e))
    # Shell returns 0 for success, a positive int for an error
    # inverted from python True/False
    if ret.returncode:
        if ignoreErrors:
            return ret.returncode
        else:
            raise SystemExit("%s returned failure: %s" % (command, ret.returncode))
    else:
        if captureOutput:
            return ret.stdout
        else:
            return True


def doProtectionTask(protectionType, appID, name):
    """Take a snapshot/backup of appID giving it name <name>
    Return the snapshotID/backupID of the backup taken or False if the protection task fails"""
    if protectionType == "backup":
        protectionID = astraSDK.takeBackup(output=False).main(appID, name)
    elif protectionType == "snapshot":
        protectionID = astraSDK.takeSnap(output=False).main(appID, name)

    print("Starting %s of %s: " % (protectionType, appID))
    print("Waiting for %s to complete." % protectionType, end="")
    sys.stdout.flush()
    while True:
        if protectionType == "backup":
            objects = astraSDK.getBackups().main()
        elif protectionType == "snapshot":
            objects = astraSDK.getSnaps().main()
        if not objects:
            # This isn't technically true.  Trying to list the backups/snapshots after taking the
            # protection job failed
            print("Taking %s failed" % protectionType)
            return False
        for obj in objects[appID]:
            # There's no API for monitoring long running tasks.  Just because
            # the API call to create a backup/snapshot succeeded, that doesn't mean the
            # actual backup will succeed as well.  So we spin on checking the backups/snapshots
            # waiting for our backupsnapshot to either show completed or failed.
            if objects[appID][obj][0] == protectionID:
                if objects[appID][obj][1] == "completed":
                    print("complete!")
                    sys.stdout.flush()
                    return protectionID
                elif objects[appID][obj][1] == "failed":
                    print("%s job failed" % protectionType)
                    return False
        time.sleep(5)
        print(".", end="")
        sys.stdout.flush()


class toolkit:
    def __init__(self):
        self.conf = astraSDK.getConfig().main()

    def deploy(self, chartName, repoName, appName, nameSpace, domain, email):
        """Deploy a helm chart <chartName>, from helm repo <repoName>
        naming the app <appName> into <nameSpace>"""

        if chartName == "gitlab":
            assert domain is not None
            assert email is not None

        # pre_apps, post_apps and apps_to_manage are hoops we jump through
        # so we only switch apps to managed that we install.
        self.preApps = astraSDK.getApps(discovered=True, namespace=nameSpace).main()
        run("kubectl create namespace %s" % nameSpace)
        run("kubectl config set-context --current --namespace=%s" % nameSpace)
        if chartName == "gitlab":
            run(
                "helm install %s %s/%s --timeout 600s "
                "--set certmanager-issuer.email=%s "
                "--set global.hosts.domain=%s "
                "--set global.hosts.gitlab.name=gl-nginx-ingress-controller.%s "
                "--set global.hosts.registry.name=registry.%s "
                "--set global.hosts.minio.name=minio.%s "
                "--set prometheus.alertmanager.persistentVolume.enabled=false "
                "--set prometheus.server.persistentVolume.enabled=false "
                "--set gitlab.gitaly.persistence.enabled=false"
                % (appName, repoName, chartName, email, domain, domain, domain, domain)
            )
        else:
            run("helm install %s %s/%s" % (appName, repoName, chartName))
        print("Waiting for Astra to discover apps.", end="")
        sys.stdout.flush()
        time.sleep(3)
        self.postApps = astraSDK.getApps(discovered=True, namespace=nameSpace).main()

        while self.preApps == self.postApps:
            # It takes Astra some time to realize new apps have been installed
            print(".", end="")
            sys.stdout.flush()
            time.sleep(3)
            self.postApps = astraSDK.getApps(
                discovered=True, namespace=nameSpace
            ).main()
        print("Discovery complete!")
        sys.stdout.flush()

        # self.apps_to_manage will be logically self.post_apps - self.pre_apps
        self.appsToManage = {
            self.k: self.v
            for (self.k, self.v) in self.postApps.items()
            if self.k not in self.preApps.keys()
        }
        for self.app in self.appsToManage:
            # Spin on managing apps.  Astra Control won't allow switching an
            # app that is in the pending state to managed.  So we retry endlessly
            # with the assumption that eventually the app will switch from
            # pending to running and the manageapp call will succeed.
            # (Note this is taking > 8 minutes in Q2)
            print("Managing: %s." % self.app, end="")
            sys.stdout.flush()
            rv = astraSDK.manageApp(self.app).main()
            while not rv:
                print(".", end="")
                sys.stdout.flush()
                time.sleep(3)
                rv = astraSDK.manageApp(self.app).main()
            print("Success.")
            sys.stdout.flush()

        # Find the appID of the namespace we just created
        # Since we switched everything we had discovered to managed we'll list all the
        # managed apps, in the hopes that our new namespace is in there.
        print("Getting appID of namespace: %s..." % nameSpace, end="")
        sys.stdout.flush()
        loop = True
        while loop:
            self.appID = None
            self.applist = astraSDK.getApps(
                source="namespace", namespace=nameSpace
            ).main()
            for self.item in self.applist:
                if self.applist[self.item][0] == nameSpace:
                    self.appID = self.item
                    print("Found")
                    sys.stdout.flush()
                    loop = False
                    break
            if self.appID is None:
                print("appID wasn't found")
                sys.stdout.flush()
                # So what this tells you is that astra wasn't finished discovering apps
                # when self.preApps became != self.postApps
                # (Astra doesn't discover things atomically)
                # potification:
                # We may have found the namespace and there might be other apps Astra didn't
                # find that are missing from the list.  We don't care about that because we'll
                # be backing up the top level namespace, and whether the apps in that namespace are
                # managed or not they still get backed up.
                print(
                    "Waiting for namespace: %s to be discovered..." % nameSpace,
                    end="",
                )
                sys.stdout.flush()
                while True:
                    # reallyPostApps is a bad name.  It will contain a discovered app that is
                    # a namespace and has a specific name.  There will only ever be one app
                    # that matches.
                    self.reallyPostApps = astraSDK.getApps(
                        discovered=True, source="namespace", namespace=nameSpace
                    ).main()
                    if not self.reallyPostApps:
                        time.sleep(3)
                        print(".", end="")
                        sys.stdout.flush()
                    else:
                        print("Discovered.")
                        sys.stdout.flush()
                        break
                for self.appID in self.reallyPostApps:
                    print("Managing: %s" % self.appID)
                    astraSDK.manageApp(self.appID).main()
                loop = False
        # and then create a protection policy on that namespace (using it's appID)
        self.backupRetention = "1"
        self.snapshotRetention = "1"
        self.minute = "0"
        self.cpp = astraSDK.createProtectionpolicy(quiet=True)
        self.cppData = {
            "hourly": {"dayOfWeek": "*", "dayOfMonth": "*", "hour": "*"},
            "daily": {"dayOfWeek": "*", "dayOfMonth": "*", "hour": "2"},
            "weekly": {"dayOfWeek": "0", "dayOfMonth": "*", "hour": "2"},
            "monthly": {"dayOfWeek": "*", "dayOfMonth": "1", "hour": "2"},
        }
        for self.period in self.cppData:
            print("Setting %s protection policy on %s" % (self.period, self.appID))
            self.dayOfWeek = self.cppData[self.period]["dayOfWeek"]
            self.dayOfMonth = self.cppData[self.period]["dayOfMonth"]
            self.hour = self.cppData[self.period]["hour"]
            cppRet = self.cpp.main(
                self.period,
                self.snapshotRetention,
                self.backupRetention,
                self.dayOfWeek,
                self.dayOfMonth,
                self.hour,
                self.minute,
                self.appID,
            )
            if cppRet is False:
                raise SystemExit("cpp.main(%s...) returned False" % self.period)

    def clone(
        self,
        clusterID,
        destNamespace,
        cloneName,
        namespaces,
        sourceAppID,
        backupID,
    ):
        """Create a clone."""
        # The REST API for cloning requires the sourceClusterID, we look that
        # up from the passed in namespaces var.
        #         appID
        # {'e6661eba-229b-4d7c-8c6c-cfca0db9068e':
        #    ['appName', 'clusterNameAppIsRunningOn', 'clusterIDthatAppIsRunningOn', 'namespace']}
        self.sourceClusterID = namespaces[sourceAppID][2]

        self.cloneRet = astraSDK.cloneApp().main(
            cloneName,
            backupID,
            clusterID,
            self.sourceClusterID,
            destNamespace,
            sourceAppID,
        )
        if self.cloneRet:
            print("Submitting clone succeeded.")
            print("Waiting for clone to become available.", end="")
            sys.stdout.flush()
            self.appID = self.cloneRet.get("id")
            self.state = self.cloneRet.get("state")
            while self.state != "running":
                self.apps = astraSDK.getApps().main()
                for self.app in self.apps:
                    if self.app == self.appID:
                        if self.apps[self.app][4] == "running":
                            self.state = self.apps[self.app][4]
                            print("Cloning operation complete.")
                            sys.stdout.flush()
                        else:
                            print(".", end="")
                            sys.stdout.flush()
                            time.sleep(3)
        else:
            print("Submitting clone failed.")

    def dataProtection(self, protectionType, sourceNamespace, backupName):
        """Take a backup of <sourceNamespace> and give it <backupName>"""
        self.protectionID = doProtectionTask(
            protectionType, sourceNamespace, backupName
        )
        if not self.protectionID:
            return False
        else:
            print("%s succeeded" % protectionType)
            return self.protectionID


if __name__ == "__main__":
    # This is a pretty big hack.  The various functions to populate the lists
    # used for choices() in the options are expensive.  argparse provides no
    # way to know what subcommand was selected prior to parsing the options.
    # By then it's too late to decide which functions to run to populate
    # the various choices the differing options for each subcommand needs.
    # So we just go around argparse's back and introspect sys.argv directly
    charts_list = []
    namespaces_list = []
    backup_list = []
    dest_cluster_list = []
    appList = []
    clusterList = []
    storageClassList = []
    if len(sys.argv) > 1:
        if sys.argv[1] == "deploy":
            chartsDict = updateHelm()
            charts_list = []
            for k in chartsDict:
                charts_list.append(k)

        elif sys.argv[1] == "clone" or sys.argv[1] == "restore":
            namespaces = astraSDK.getApps(source="namespace").main()
            namespaces_list = [x for x in namespaces.keys()]
            dest_cluster = astraSDK.getClusters().main()
            dest_cluster_list = [x for x in dest_cluster.keys()]
            backup_list = []
            backups = astraSDK.getBackups().main()
            for appID in backups:
                for backupItem in backups[appID]:
                    backup_list.append(backups[appID][backupItem][0])
        elif sys.argv[1] == "backup":
            namespaces = astraSDK.getApps(source="namespace").main()
            namespaces_list = [x for x in namespaces.keys()]
        elif (
            sys.argv[1] == "create"
            and len(sys.argv) > 2
            and (
                sys.argv[2] == "backup"
                or sys.argv[2] == "protectionpolicy"
                or sys.argv[2] == "snapshot"
            )
        ):
            appList = [x for x in astraSDK.getApps().main()]
        elif sys.argv[1] == "manage" and len(sys.argv) > 2:
            if sys.argv[2] == "app":
                appList = [x for x in astraSDK.getApps(discovered=True).main()]
            elif sys.argv[2] == "cluster":
                clusterList = []
                clusterDict = astraSDK.getClusters(quiet=True).main()
                for cluster in clusterDict:
                    if clusterDict[cluster][2] == "unmanaged":
                        clusterList.append(cluster)
                storageClassDict = astraSDK.getStorageClasses(quiet=True).main()
                storageClassList = []
                for cloud in storageClassDict:
                    for cluster in storageClassDict[cloud]:
                        if (
                            len(sys.argv) > 3
                            and sys.argv[3] in clusterList
                            and cluster != sys.argv[3]
                        ):
                            continue
                        for sc in storageClassDict[cloud][cluster]:
                            storageClassList.append(sc)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="subcommand", required=True, help="subcommand help"
    )
    #######
    # Top level subcommands
    #######
    parserDeploy = subparsers.add_parser(
        "deploy",
        help="deploy a bitnami chart",
    )
    parserClone = subparsers.add_parser(
        "clone",
        aliases=["restore"],
        help="clone a namespace to a destination cluster",
    )
    parserList = subparsers.add_parser(
        "list",
        help="List all items in a class",
    )
    parserCreate = subparsers.add_parser(
        "create",
        help="Create an object",
    )
    parserManage = subparsers.add_parser(
        "manage",
        help="Manage an object",
    )
    #######
    # End of top level subcommands
    #######

    #######
    # subcommands "list", "create", and "manage" have subcommands as well
    #######
    subparserList = parserList.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    subparserCreate = parserCreate.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    subparserManage = parserManage.add_subparsers(
        title="objectType", dest="objectType", required=True
    )
    #######
    # end of subcommand "list", "create", and "manage" subcommands
    #######

    #######
    # list 'X'
    #######
    subparserListApps = subparserList.add_parser(
        "apps",
        help="list apps",
    )
    subparserListBackups = subparserList.add_parser(
        "backups",
        help="list backups",
    )
    subparserListClouds = subparserList.add_parser(
        "clouds",
        help="list clouds",
    )
    subparserListClusters = subparserList.add_parser(
        "clusters",
        help="list clusters",
    )
    subparserListSnapshots = subparserList.add_parser(
        "snapshots",
        help="list snapshots",
    )
    subparserListStorageClasses = subparserList.add_parser(
        "storageclasses",
        help="list storageclasses",
    )
    #######
    # end of list 'X'
    #######

    #######
    # list apps args and flags
    #######
    subparserListApps.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    subparserListApps.add_argument(
        "-u",
        "--unmanaged",
        default=False,
        action="store_true",
        help="Show only unmanaged apps",
    )
    subparserListApps.add_argument("-s", "--source", help="app source")
    subparserListApps.add_argument(
        "-n", "--namespace", default=None, help="Only show apps from this namespace"
    )
    #######
    # end of list apps args and flags
    #######

    #######
    # list backups args and flags
    #######
    subparserListBackups.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of list backups args and flags
    #######

    #######
    # list clouds args and flags
    #######
    subparserListClouds.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of list clouds args and flags
    #######

    #######
    # list clusters args and flags
    #######
    subparserListClusters.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    subparserListClusters.add_argument(
        "-m",
        "--managed",
        default=False,
        action="store_true",
        help="Hide managed clusters",
    )
    subparserListClusters.add_argument(
        "-u",
        "--unmanaged",
        default=False,
        action="store_true",
        help="Hide unmanaged clusters",
    )
    #######
    # end of list clusters args and flags
    #######

    #######
    # list snapshots args and flags
    #######
    subparserListSnapshots.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of list snapshots args and flags
    #######

    #######
    # list storageclasses args and flags
    #######
    subparserListStorageClasses.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of list storageclasses args and flags
    #######

    #######
    # create 'X'
    #######
    subparserCreateBackup = subparserCreate.add_parser(
        "backup",
        help="create backup",
    )
    subparserCreateProtectionpolicy = subparserCreate.add_parser(
        "protectionpolicy",
        help="create protectionpolicy",
    )
    subparserCreateSnapshot = subparserCreate.add_parser(
        "snapshot",
        help="create snapshot",
    )
    #######
    # end of create 'X'
    #######

    #######
    # create backups args and flags
    #######
    subparserCreateBackup.add_argument(
        "appID",
        choices=appList,
        help="appID to backup",
    )
    subparserCreateBackup.add_argument(
        "name",
        help="Name of backup to be taken",
    )
    #######
    # end of create backups args and flags
    #######

    #######
    # create protectionpolicy args and flags
    #######
    granArg = subparserCreateProtectionpolicy.add_argument(
        "-g",
        "--granularity",
        required=True,
        choices=["hourly", "daily", "weekly", "monthly"],
        help="Must choose one of the four options for the schedule",
    )
    subparserCreateProtectionpolicy.add_argument(
        "-b",
        "--backupRetention",
        type=int,
        required=True,
        choices=range(60),
        help="Number of backups to retain",
    )
    subparserCreateProtectionpolicy.add_argument(
        "-s",
        "--snapshotRetention",
        type=int,
        required=True,
        choices=range(60),
        help="Number of snapshots to retain",
    )
    subparserCreateProtectionpolicy.add_argument(
        "-M", "--dayOfMonth", type=int, choices=range(1, 32), help="Day of the month"
    )
    subparserCreateProtectionpolicy.add_argument(
        "-W",
        "--dayOfWeek",
        type=int,
        choices=range(7),
        help="0 = Sunday ... 7 = Saturaday",
    )
    subparserCreateProtectionpolicy.add_argument(
        "-H", "--hour", type=int, choices=range(24), help="Hour in military time"
    )
    subparserCreateProtectionpolicy.add_argument(
        "-m", "--minute", default=0, type=int, choices=range(60), help="Minute"
    )
    subparserCreateProtectionpolicy.add_argument(
        "appID",
        choices=appList,
        help="appID of the application to create protection schecule for",
    )
    subparserCreateProtectionpolicy.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of create protectionpolicy args and flags
    #######

    #######
    # create snapshot args and flags
    #######
    subparserCreateSnapshot.add_argument(
        "appID",
        choices=appList,
        help="appID to snapshot",
    )
    subparserCreateSnapshot.add_argument(
        "name",
        help="Name of snapshot to be taken",
    )
    #######
    # end of create snapshot args and flags
    #######

    #######
    # manage 'X'
    #######
    subparserManageApp = subparserManage.add_parser(
        "app",
        help="manage app",
    )
    subparserManageCluster = subparserManage.add_parser(
        "cluster",
        help="manage cluster",
    )
    #######
    # end of manage 'X'
    #######

    #######
    # manage app args and flags
    #######
    subparserManageApp.add_argument(
        "appID",
        choices=appList,
        help="appID of app to move from discovered to managed",
    )
    subparserManageApp.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of manage app args and flags
    #######

    #######
    # manage cluster args and flags
    #######
    subparserManageCluster.add_argument(
        "clusterID",
        choices=clusterList,
        help="clusterID of the cluster to manage",
    )
    subparserManageCluster.add_argument(
        "storageClassID",
        choices=storageClassList,
        help="Default storage class ID",
    )
    subparserManageCluster.add_argument(
        "-q", "--quiet", default=False, action="store_true", help="Supress output"
    )
    #######
    # end of manage cluster args and flags
    #######

    #######
    # deploy args and flags
    #######
    parserDeploy.add_argument(
        "chart",
        choices=charts_list,
        help="chart to deploy",
    )
    parserDeploy.add_argument(
        "app",
        help="name of app",
    )
    parserDeploy.add_argument(
        "namespace", help="Namespace to deploy into (must not already exist)"
    )
    parserDeploy.add_argument(
        "--domain",
        "-d",
        required=False,
        help="Default domain to pass gitlab deployment",
    )
    parserDeploy.add_argument(
        "--email",
        "-e",
        required=False,
        help="Email address for self-signed certs (gitlab only)",
    )
    #######
    # end of deploy args and flags
    #######

    #######
    # clone args and flags
    #######
    parserClone.add_argument(
        "--sourceNamespace",
        choices=namespaces_list,
        required=False,
        default=None,
        help="Source namespace to clone",
    )
    parserClone.add_argument(
        "--backupID",
        choices=backup_list,
        required=False,
        default=None,
        help="Source backup to clone",
    )
    parserClone.add_argument(
        "--clusterID",
        choices=dest_cluster_list,
        required=False,
        default=None,
        help="Cluster to clone to",
    )
    parserClone.add_argument(
        "--destName",
        required=False,
        default=None,
        help="clone name",
    )
    parserClone.add_argument(
        "--destNamespace",
        required=False,
        default=None,
        help="Destination namespace",
    )
    #######
    # end of clone args and flags
    #######

    args = parser.parse_args()
    # print("args: %s" % args)
    if hasattr(args, "granularity"):
        if args.granularity == "hourly":
            if args.hour:
                raise argparse.ArgumentError(
                    granArg, " hourly must not specify -H / --hour"
                )
            if not hasattr(args, "minute"):
                raise argparse.ArgumentError(granArg, " hourly requires -m / --minute")
            args.hour = "*"
            args.dayOfWeek = "*"
            args.dayOfMonth = "*"
        elif args.granularity == "daily":
            if not args.hour:
                raise argparse.ArgumentError(granArg, " daily requires -H / --hour")
            args.dayOfWeek = "*"
            args.dayOfMonth = "*"
        elif args.granularity == "weekly":
            if not args.hour:
                raise argparse.ArgumentError(granArg, " weekly requires -H / --hour")
            if not args.dayOfWeek:
                raise argparse.ArgumentError(
                    granArg, " weekly requires -W / --dayOfWeek"
                )
            args.dayOfMonth = "*"
        elif args.granularity == "monthly":
            if not args.hour:
                raise argparse.ArgumentError(granArg, " monthly requires -H / --hour")
            if args.dayOfWeek:
                raise argparse.ArgumentError(
                    granArg, " hourly must not specify -W / --dayOfWeek"
                )
            if not args.dayOfMonth:
                raise argparse.ArgumentError(
                    granArg, " monthly requires -M / --dayOfMonth"
                )
            args.dayOfWeek = "*"

    ret = toolkit()
    if args.subcommand == "deploy":
        if hasattr(args, "domain"):
            domain = args.domain
        else:
            domain = None
        if hasattr(args, "email"):
            email = args.email
        else:
            email = None
        ret.deploy(
            args.chart, chartsDict[args.chart], args.app, args.namespace, domain, email
        )
    elif args.subcommand == "list":
        if args.objectType == "apps":
            astraSDK.getApps(
                quiet=args.quiet,
                discovered=args.unmanaged,
                source=args.source,
                namespace=args.namespace,
            ).main()
        elif args.objectType == "backups":
            astraSDK.getBackups(quiet=args.quiet).main()
        elif args.objectType == "clouds":
            astraSDK.getClouds(quiet=args.quiet).main()
        elif args.objectType == "clusters":
            astraSDK.getClusters(
                quiet=args.quiet, hideManaged=args.managed, hideUnmanaged=args.unmanaged
            ).main()
        elif args.objectType == "snapshots":
            astraSDK.getSnaps(quiet=args.quiet).main()
        elif args.objectType == "storageclasses":
            astraSDK.getStorageClasses(quiet=args.quiet).main()
    elif args.subcommand == "create":
        if args.objectType == "backup":
            doProtectionTask(args.objectType, args.appID, args.name)
        elif args.objectType == "protectionpolicy":
            astraSDK.createProtectionpolicy(quiet=args.quiet).main(
                args.granularity,
                str(args.backupRetention),
                str(args.snapshotRetention),
                str(args.dayOfWeek),
                str(args.dayOfMonth),
                str(args.hour),
                str(args.minute),
                args.appID,
            )
        elif args.objectType == "snapshot":
            doProtectionTask(args.objectType, args.appID, args.name)

    elif args.subcommand == "manage":
        if args.objectType == "app":
            astraSDK.manageApp(appID=args.appID, quiet=args.quiet).main()
        if args.objectType == "cluster":
            astraSDK.manageCluster(
                args.clusterID, args.storageClassID, quiet=args.quiet
            ).main()
    elif args.subcommand == "clone" or args.subcommand == "restore":
        if not args.clusterID:
            print("Select destination cluster for the clone")
            print("Index\tClusterID\tclusterName\tclusterPlatform")
            args.clusterID = userSelect(dest_cluster)
        if not args.destNamespace:
            args.destNamespace = input(
                "Namespace for the clone "
                "(This must not be a namespace that currently exists on the destination cluster): "
            )
        if not args.destName:
            args.destName = input("Name for the clone: ")
        if not args.sourceNamespace:
            if not args.backupID:
                # no source namespace/app or source backup
                print(
                    "sourceNamespace and backupID are unspecified, you can pick a"
                    " sourceNamespace, then select a backup of that sourceNamespace."
                    " (If a backup of that namespace doesn't exist one"
                    " will be created.  Or you can specify a backupID to use directly."
                )
                while True:
                    retval = input("sourceNamespace or backupID: ")
                    if retval.lower().startswith("s"):
                        retval = "sourceNamespace"
                        break
                    elif retval.lower().startswith("b"):
                        retval = "backupID"
                        break
                    else:
                        print("Enter sourceNamespace or backupID")
                # namespaces: {'f28c0716-310b-4389-8187-58e9502bc860':
                #              ['failoverfriday',
                #               'cluster-2-jp',
                #               '91ef5e4b-b5fd-4839-9df1-fa6f015f5acd',
                #               'namespace']}
                if retval == "sourceNamespace":
                    print("Select source namespace to be cloned")
                    print("Index\tAppID\tappName\tclusterName\tClusterID")
                    args.sourceNamespace = userSelect(namespaces)
                    appBackups = backups[args.sourceNamespace]
                    """
                    appBackups: {'failoverfriday-backup-20210713192550':
                                    ['d1625f68-6dc9-45b8-b80f-81785d9e25d3',
                                     'completed',
                                     '2021-07-13T19:25:53'],
                                 'hourly-qpwfl-lebau':
                                    ['7bedcb38-ec3e-4a60-9df0-8a77e050cf2f',
                                     'completed',
                                     '2021-07-13T20:00:00']
                    """
                    appBackupscooked = {}
                    for k, v in appBackups.items():
                        if v[1] == "completed":
                            appBackupscooked[v[0]] = [k, v[2], args.sourceNamespace]
                    if appBackupscooked:
                        print("Select source backup")
                        print("Index\tBackupID\tBackupName\tTimestamp\tAppID")
                        args.backupID = userSelect(appBackupscooked)
                        print("args.backupID: %s" % args.backupID)
                    else:
                        # Take a backup
                        print("No backups found, taking backup.")
                        backupRetval = doProtectionTask(
                            "backup", args.sourceNamespace, "toolkit-%s" % args.destName
                        )
                        if not backupRetval:
                            print("Exiting due to backup task failing.")
                            sys.exit(7)
                elif retval == "backupID":
                    # No namespace or backupID was specified on the CLI
                    # user opted to specify a backupID, from there we
                    # can work backwards to get the namespace.
                    backup_dict = {}
                    for appID in backups:
                        for k, v in backups[appID].items():
                            if v[1] == "completed":
                                backup_dict[v[0]] = [k, v[2], appID]
                    if not backup_dict:
                        print("No backups found.")
                        sys.exit(6)
                    print("Index\tBackupID\tBackupName\tTimestamp\tappID")
                    args.backupID = userSelect(backup_dict)
                    args.sourceNamespace = backup_dict[args.backupID][2]

            else:
                # no source namespace/app but we have a backupID
                # work backwards to get the appID
                for appID in backups.keys():
                    for backup in backups[appID].keys():
                        if backups[appID][backup][0] == args.backupID:
                            args.sourceNamespace = appID
                if not args.sourceNamespace:
                    print("Can't determine appID from backupID")
                    sys.exit(9)
        else:
            # we have a source namespace/app
            # if we have a backupID we have everything we need
            if not args.backupID:
                appBackups = backups[args.sourceNamespace]
                """
                appBackups: {'failoverfriday-backup-20210713192550':
                                ['d1625f68-6dc9-45b8-b80f-81785d9e25d3',
                                 'completed',
                                 '2021-07-13T19:25:53'],
                             'hourly-qpwfl-lebau':
                                ['7bedcb38-ec3e-4a60-9df0-8a77e050cf2f',
                                 'completed',
                                 '2021-07-13T20:00:00']
                """
                appBackupscooked = {}
                for k, v in appBackups.items():
                    if v[1] == "completed":
                        appBackupscooked[v[0]] = [k, v[2], args.sourceNamespace]
                if appBackupscooked:
                    print("Select source backup")
                    print("Index\tBackupID\tBackupName\tTimestamp\tAppID")
                    args.backupID = userSelect(appBackupscooked)
                    print("args.backupID: %s" % args.backupID)
                else:
                    # Take a backup
                    backupRetval = doProtectionTask(
                        "backup", args.sourceNamespace, "toolkit-%s" % args.destName
                    )
                    if not backupRetval:
                        print("Exiting due to backup task failing.")
                        sys.exit(7)
        ret.clone(
            args.clusterID,
            args.destNamespace,
            args.destName,
            namespaces,
            sourceAppID=args.sourceNamespace,
            backupID=args.backupID,
        )
