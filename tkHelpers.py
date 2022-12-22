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

import json
import os
import re
import subprocess
import sys
import tempfile
import yaml


def subKeys(subObject, key):
    """Short recursion function for when the userSelect dict object has another
    dict as one of its key's values"""
    subKey = key.split("/", maxsplit=1)
    if len(subKey) == 1:
        return subObject[subKey[0]]
    else:
        return subKeys(subObject[subKey[0]], subKey[1])


def userSelect(pickList, keys):
    """pickList is a dictionary with an 'items' array of dicts.  Print the values
    that match the 'keys' array, have the user pick one and then return the value
    of index 0 of the keys array"""
    # pickList = {"items": [{"id": "123", "name": "webapp",  "state": "running"},
    #                       {"id": "345", "name": "mongodb", "state": "stopped"}]}
    # keys = ["id", "name"]
    # Output:
    # 1:    123         webapp
    # 2:    345         mongodb
    # User enters 2, "id" (index 0) is returned, so "345"

    if not isinstance(pickList, dict) or not isinstance(keys, list):
        return False

    for counter, item in enumerate(pickList["items"], start=1):
        outputStr = str(counter) + ":\t"
        for key in keys:
            if item.get(key):
                outputStr += str(item[key]) + "\t"
            elif "/" in key:
                outputStr += subKeys(item, key) + "\t"
        print(outputStr)

    while True:
        ret = input(f"Select a line (1-{counter}): ")
        try:
            # try/except catches errors thrown from non-valid input
            objectValue = pickList["items"][int(ret) - 1][keys[0]]
            if int(ret) > 0 and int(ret) <= counter and objectValue:
                return objectValue
            else:
                continue
        except (IndexError, TypeError, ValueError):
            continue


def createHelmStr(flagName, values):
    """Create a string to be appended to a helm command which contains a list
    of --set {value} and/or --values {file} arguments"""
    returnStr = ""
    if values:
        for value in values:
            if type(value) == list:
                for v in value:
                    returnStr += f" --{flagName} {v}"
            else:
                returnStr += f" --{flagName} {value}"
    return returnStr


def createHookList(hookArguments):
    """Create a list of strings to be used for --hookArguments, as nargs="*" can provide
    a variety of different types of lists of lists depending on how the user uses it.
    User Input                    argParse Value                      createHookList Return
    ----------                    --------------                      ---------------------
    -a arg1                       [['arg1']]                          ['arg1']
    -a arg1 arg2                  [['arg1', 'arg2']]                  ['arg1', 'arg2']
    -a arg1 -a arg2               [['arg1'], ['arg2']]                ['arg1', 'arg2']
    -a "arg1 s_arg" arg2          [['arg1 s_arg', 'arg2']]            ['arg1 s_arg', 'arg2']
    -a "arg1 s_arg" arg2 -a arg3  [['arg1 s_arg', 'arg2'], ['arg3']]  ['arg1 s_arg', 'arg2', 'arg3']
    """
    returnList = []
    if hookArguments:
        for arg in hookArguments:
            if type(arg) == list:
                for a in arg:
                    returnList.append(a)
            else:
                returnList.append(arg)
    return returnList


def createFilterTypeList(fType, valueList):
    """Creates a list of dicts like {"type": "containerImage", "value": "\\bmariadb\\b"} based on
    the passed filter type and value list strings.  Called by createCriteriaList which aggregates
    the entire list"""
    returnList = []
    for value in valueList:
        if type(value) == list:
            for v in value:
                returnList.append({"type": fType, "value": v})
        else:
            returnList.append({"type": fType, "value": value})
    return returnList


def createCriteriaList(images, namespaces, pods, labels, names):
    """Create a list of dictionaries for hook filters (aka matchingCriteria) of various types, as
    nargs="*" can provide a variety of different types of lists of lists."""
    return (
        createFilterTypeList("containerImage", images)
        + createFilterTypeList("namespaceName", namespaces)
        + createFilterTypeList("podName", pods)
        + createFilterTypeList("podLabel", labels)
        + createFilterTypeList("containerName", names)
    )


def createNamespaceMapping(app, singleNs, multiNsMapping):
    """Create a list of dictionaries of source and destination namespaces for cloning an
    application, as the user can provide a variety of input.  Return object format:
    [ { "source": "sourcens1", "destination": "destns1" },
      { "source": "sourcens2", "destination": "destns2" } ]"""
    # Ensure that multiNsMapping was used for multi-namespace apps
    if multiNsMapping is None and len(app["namespaceScopedResources"]) > 1:
        print("Error: for multi-namespace apps, --multiNsMapping must be used.")
        sys.exit(1)
    # For single-namespace apps, the namespace mapping is **not** a required field
    elif singleNs is None and multiNsMapping is None:
        return None
    # Handle --cloneNamespace argument
    elif singleNs:
        return [
            {
                "source": app["namespaceScopedResources"][0]["namespace"],
                "destination": isRFC1123(singleNs),
            }
        ]
    # Handle multiNsMapping cases
    elif multiNsMapping:
        # Create a single list of mappings (nargs can produce a variety of lists of lists)
        mappingList = []
        for NsMapping in multiNsMapping:
            if type(NsMapping) == list:
                for mapping in NsMapping:
                    mappingList.append(mapping)
            else:
                mappingList.append(NsMapping)
        # Ensure the mappings are of 'sourcens=destns' format
        for mapping in mappingList:
            if len(mapping.split("=")) != 2:
                print(f"Error: '{mapping}' does not conform to 'sourcens=destns' format")
                sys.exit(1)
        # Ensure that the user-provided source mapping equals the app namespaces
        sortedMappingSourceNs = sorted([i.split("=")[0] for i in mappingList])
        sortedAppSourceNs = sorted([i["namespace"] for i in app["namespaceScopedResources"]])
        if sortedMappingSourceNs != sortedAppSourceNs:
            print(
                "Error: the source namespaces provided by --multiNsMapping do not match the "
                + f"namespaces in the source app:\nsourceApp:\t{sortedAppSourceNs}"
                + f"\nmultiNsMapping:\t{sortedMappingSourceNs}"
            )
            sys.exit(1)
        # Generate the return mapping list and return it
        returnList = []
        for mapping in mappingList:
            returnList.append(
                {"source": mapping.split("=")[0], "destination": isRFC1123(mapping.split("=")[1])}
            )
        return returnList
    else:
        print("Unknown Error")
        sys.exit(1)


def createNamespaceList(namespaceArguments):
    """Create a list of dictionaries of namespace key/value and (optionally) labelSelectors
    key/value(list) for managing an app, as nargs="*" can provide a variety of input."""
    returnList = []
    for mapping in namespaceArguments:
        returnList.append({"namespace": mapping[0]})
        if len(mapping) == 2:
            returnList[-1]["labelSelectors"] = [mapping[1]]
        elif len(mapping) > 2:
            print(
                "Error: --additionalNamespace should have at most two arguments per flag:\n"
                + "  -a namespace1\n  -a namespace1 app=appname\n"
                + "  -a namespace1 -a namespace2 app=app2name"
            )
            sys.exit(1)
    return returnList


def createCsrList(CSRs, apiResourcesDict):
    """Create a list of dictionaries of clusterScopedResources and (optionally) labelSelectors
    key/value(list) for managing an app, as nargs="*" can provide a variety of input."""
    returnList = []
    for csr in CSRs:
        for resource in apiResourcesDict["items"]:
            if csr[0] == resource["kind"]:
                returnList.append(
                    {
                        "GVK": {
                            "group": resource["apiVersion"].split("/")[0],
                            "kind": resource["kind"],
                            "version": resource["apiVersion"].split("/")[1],
                        }
                    }
                )
                if len(csr) == 2:
                    returnList[-1]["labelSelectors"] = [csr[1]]
                elif len(csr) > 2:
                    print(
                        "Error: --clusterScopedResource should have at most two arguments per "
                        + "flag:\n  -a csr-kind1\n  -a csr-kind1 app=appname\n"
                        + "  -a csr-kind1 -a csr-kind2 app=app2name"
                    )
                    sys.exit(1)
    if len(returnList) == 0:
        print(
            "Error: matching clusterScopedResource kind not found, please ensure the kind "
            + "is correct via 'list apiresources'"
        )
        sys.exit(1)
    return returnList


def createConstraintList(idList, labelList):
    """Create a list of strings to be used for --labelConstraint and --namespaceConstraint args,
    as nargs="*" can provide a varitey of different types of lists of lists depending on input."""
    returnList = []
    if idList:
        for arg in idList:
            if type(arg) == list:
                for a in arg:
                    returnList.append("namespaces:id='" + a + "'.*")
            else:
                returnList.append("namespaces:id='" + arg + "'.*")
    if labelList:
        for arg in labelList:
            if type(arg) == list:
                for a in arg:
                    returnList.append("namespaces:kubernetesLabels='" + a + "'.*")
            else:
                returnList.append("namespaces:kubernetesLabels='" + arg + "'.*")
    return returnList if returnList else ["*"]


def updateHelm():
    """Check to see if the {repos} are installed, install them if they are not.
    Then, return a dictionary of all charts (both user installed repos, and {repos})."""
    ret = run("helm repo list -o yaml", captureOutput=True, ignoreErrors=True)
    repos = {
        "https://charts.gitlab.io": None,
        "https://charts.bitnami.com/bitnami": None,
        "https://charts.cloudbees.com/public/cloudbees": None,
    }
    if ret != 1:
        retYaml = yaml.load(ret, Loader=yaml.SafeLoader)
        # Adding support for user-defined repos
        for item in retYaml:
            if item.get("url") not in repos:
                repos[item.get("url")] = None
        for repoUrlToMatch in repos:
            for item in retYaml:
                if item.get("url") == repoUrlToMatch:
                    repos[repoUrlToMatch] = item.get("name")
    for k, v in repos.items():
        if not v:
            repoName = k.split(".")[1]
            run(f"helm repo add {repoName} {k}")
            repos[k] = repoName

    run("helm repo update")
    chartsDict = {}
    chartsDict["items"] = []
    for val in repos.values():
        charts = run(f"helm -o json search repo {val}", captureOutput=True)
        for chart in json.loads(charts.decode("utf-8")):
            chartsDict["items"].append(chart)
    return chartsDict


def run(command, captureOutput=False, ignoreErrors=False):
    """Run an arbitrary shell command.
    If ignore_errors=False raise SystemExit exception if the commands returns != 0 (failure).
    If ignore_errors=True, return the shell return code if it is != 0.
    If the shell return code is 0 (success) either return True or the contents of stdout,
    depending on whether capture_output is set to True or False"""
    command = command.split(" ")
    try:
        ret = subprocess.run(command, capture_output=captureOutput)
    except OSError as e:
        raise SystemExit(f"{command} OSError: {e}")
    # Shell returns 0 for success, a positive int for an error
    # inverted from python True/False
    if ret.returncode:
        if ignoreErrors:
            return ret.returncode
        else:
            raise SystemExit(f"{command} returned failure: {ret.returncode}")
    else:
        if captureOutput:
            return ret.stdout
        else:
            return True


def stsPatch(patch, stsName):
    """Patch and restart a statefulset"""
    patchYaml = yaml.dump(patch)
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(bytes(patchYaml, "utf-8"))
    tmp.seek(0)
    # Use os.system a few times because the home rolled run() simply isn't up to the task
    try:
        # TODO: I suspect these gymnastics wouldn't be needed if the py-k8s module
        # were used
        ret = os.system(f'kubectl patch statefulset.apps/{stsName} -p "$(cat {tmp.name})"')
    except OSError as e:
        print(f"Exception: {e}")
        sys.exit(11)
    if ret:
        print(f"os.system exited with RC: {ret}")
        sys.exit(12)
    tmp.close()
    try:
        os.system(
            f"kubectl scale sts {stsName} --replicas=0 && "
            f"sleep 10 && kubectl scale sts {stsName} --replicas=1"
        )
    except OSError as e:
        print(f"Exception: {e}")
        sys.exit(13)
    if ret:
        print(f"os.system exited with RC: {ret}")
        sys.exit(14)


def isRFC1123(string):
    """isRFC1123 returns the input 'string' if it conforms to RFC 1123 spec,
    otherwise it throws an error and exits with code 15"""
    regex = re.compile("[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
    if regex.match(string) is not None and len(string) < 64:
        return string
    else:
        print(
            f"Error: '{string}' must consist of lower case alphanumeric characters or '-', must "
            + "start and end with an alphanumeric character, and must be at most 63 characters "
            + "(for example 'my-name' or '123-abc')."
        )
        sys.exit(15)
