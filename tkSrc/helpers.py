#!/usr/bin/env python3
"""
   Copyright 2023 NetApp, Inc

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
import tempfile
import yaml

from jinja2 import Environment, FileSystemLoader


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
            if isinstance(value, list):
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
            if isinstance(arg, list):
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
        if isinstance(value, list):
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


def createNamespaceMapping(appNamespaces, singleNs, multiNsMapping, parser):
    """Create a list of dictionaries of source and destination namespaces for cloning an
    application, as the user can provide a variety of input.  Return object format:
    [ { "source": "sourcens1", "destination": "destns1" },
      { "source": "sourcens2", "destination": "destns2" } ]"""
    # Ensure that multiNsMapping was used for multi-namespace apps
    if multiNsMapping is None and len(appNamespaces) > 1:
        parser.error("for multi-namespace apps, --multiNsMapping must be used.")
    # For single-namespace apps, the namespace mapping is **not** a required field
    elif singleNs is None and multiNsMapping is None:
        return None
    # Handle --cloneNamespace argument
    elif singleNs:
        return [
            {
                "source": appNamespaces[0]["namespace"],
                "destination": isRFC1123(singleNs),
            }
        ]
    # Handle multiNsMapping cases
    elif multiNsMapping:
        # Create a single list of mappings (nargs can produce a variety of lists of lists)
        mappingList = []
        for NsMapping in multiNsMapping:
            if isinstance(NsMapping, list):
                for mapping in NsMapping:
                    mappingList.append(mapping)
            else:
                mappingList.append(NsMapping)
        # Ensure the mappings are of 'sourcens=destns' format
        for mapping in mappingList:
            if len(mapping.split("=")) != 2:
                raise SystemExit(f"Error: '{mapping}' does not conform to 'sourcens=destns' format")
        # Ensure that the user-provided source mapping equals the app namespaces
        sortedMappingSourceNs = sorted([i.split("=")[0] for i in mappingList])
        sortedAppSourceNs = sorted([i["namespace"] for i in appNamespaces])
        if sortedMappingSourceNs != sortedAppSourceNs:
            raise SystemExit(
                "Error: the source namespaces provided by --multiNsMapping do not match the "
                + f"namespaces in the source app:\nsourceApp:\t{sortedAppSourceNs}"
                + f"\nmultiNsMapping:\t{sortedMappingSourceNs}"
            )
        # Generate the return mapping list and return it
        returnList = []
        for mapping in mappingList:
            returnList.append(
                {"source": mapping.split("=")[0], "destination": isRFC1123(mapping.split("=")[1])}
            )
        return returnList
    else:
        raise SystemExit("Unknown Error")


def updateNamespaceSpec(mapping, spec):
    """Function which takes a mapping like:
    [{'source': 'ns1', 'destination': 'ns1-clone'},
     {'source': 'ns2', 'destination': 'ns2-clone'}]
    And a spec like:
    {'includedNamespaces': [
        {'labelSelector': {}, 'namespace': 'ns1'},
        {'labelSelector': {}, 'namespace': 'ns2'}
    ]}
    And returns a new spec like:
    {'includedNamespaces': [
        {'labelSelector': {}, 'namespace': 'ns1-clone'},
        {'labelSelector': {}, 'namespace': 'ns2-clone'}
    ]}
    """
    for m in mapping:
        for ns in spec["includedNamespaces"]:
            if m["source"] == ns["namespace"]:
                ns["namespace"] = m["destination"]
    return spec


def createNamespaceList(namespaceArguments, v3=False):
    """Create a list of dictionaries of namespace key/value and (optionally) labelSelectors
    key/value(list) for managing an app, as nargs="*" can provide a variety of input."""
    returnList = []
    for mapping in namespaceArguments:
        returnList.append({"namespace": mapping[0]})
        if len(mapping) == 2:
            if v3:
                returnList[-1]["labelSelector"] = {
                    "matchLabels": {mapping[1].split("=")[0]: mapping[1].split("=")[1]}
                }
            else:
                returnList[-1]["labelSelectors"] = [mapping[1]]
        elif len(mapping) > 2:
            raise SystemExit(
                "Error: --additionalNamespace should have at most two arguments per flag:\n"
                + "  -a namespace1\n  -a namespace1 app=appname\n"
                + "  -a namespace1 -a namespace2 app=app2name"
            )
    return returnList


def createCsrList(CSRs, apiResourcesDict, v3=False):
    """Create a list of dictionaries of clusterScopedResources and (optionally) labelSelectors
    key/value(list) for managing an app, as nargs="*" can provide a variety of input."""
    returnList = []
    for csr in CSRs:
        for resource in apiResourcesDict["items"]:
            if csr[0] == resource["kind"]:
                gvk_dict = {
                    "group": resource["apiVersion"].split("/")[0],
                    "kind": resource["kind"],
                    "version": resource["apiVersion"].split("/")[1],
                }
                if v3:
                    returnList.append({"groupVersionKind": gvk_dict})
                else:
                    returnList.append({"GVK": gvk_dict})
                if len(csr) == 2:
                    if v3:
                        returnList[-1]["labelSelector"] = csr[1]
                    else:
                        returnList[-1]["labelSelectors"] = [csr[1]]
                elif len(csr) > 2:
                    raise SystemExit(
                        "Error: --clusterScopedResource should have at most two arguments per "
                        + "flag:\n  -a csr-kind1\n  -a csr-kind1 app=appname\n"
                        + "  -a csr-kind1 -a csr-kind2 app=app2name"
                    )
    if len(returnList) == 0:
        raise SystemExit(
            "Error: matching clusterScopedResource kind not found, please ensure the kind "
            + "is correct via 'list apiresources'"
        )
    return returnList


def createConstraintList(idList, labelList):
    """Create a list of strings to be used for --labelConstraint and --namespaceConstraint args,
    as nargs="*" can provide a varitey of different types of lists of lists depending on input."""
    returnList = []
    if idList:
        for arg in idList:
            if isinstance(arg, list):
                for a in arg:
                    returnList.append("namespaces:id='" + a + "'.*")
            else:
                returnList.append("namespaces:id='" + arg + "'.*")
    if labelList:
        for arg in labelList:
            if isinstance(arg, list):
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


def run(command, captureOutput=False, ignoreErrors=False, env=None):
    """Run an arbitrary shell command.
    If ignore_errors=False raise SystemExit exception if the commands returns != 0 (failure).
    If ignore_errors=True, return the shell return code if it is != 0.
    If the shell return code is 0 (success) either return True or the contents of stdout,
    depending on whether capture_output is set to True or False.
    env should either "None" or a dict of environment variables to add to current environ"""
    if isinstance(env, dict):
        env.update(os.environ)
    command = command.split(" ")
    try:
        ret = subprocess.run(command, capture_output=captureOutput, env=env)
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
        raise SystemExit(f"Exception: {e}")
    if ret:
        raise SystemExit(f"os.system exited with RC: {ret}")
    tmp.close()
    try:
        os.system(
            f"kubectl scale sts {stsName} --replicas=0 && "
            f"sleep 10 && kubectl scale sts {stsName} --replicas=1"
        )
    except OSError as e:
        raise SystemExit(f"Exception: {e}")
    if ret:
        raise SystemExit(f"os.system exited with RC: {ret}")


def isRFC1123(string):
    """isRFC1123 returns the input 'string' if it conforms to RFC 1123 spec,
    otherwise it throws an error and exits with code 15"""
    regex = re.compile("[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
    if regex.match(string) is not None and len(string) < 64:
        return string
    else:
        raise SystemExit(
            f"Error: '{string}' must consist of lower case alphanumeric characters or '-', must "
            + "start and end with an alphanumeric character, and must be at most 63 characters "
            + "(for example 'my-name' or '123-abc')."
        )


def dupeKeyError(key):
    """Print an error message if duplicate keys are used"""
    raise SystemExit(
        f"Error: '{key}' should not be specified multiple times within a single --filterSet arg"
    )


def createSetDict(setDict, filterStr, assets):
    """Given a filterStr such as:
        label=app.kubernetes.io/tier=backend,name=mysql,kind=Deployment
    Return a setDict with the following format:
        {
            "labelSelectors": ["app.kubernetes.io/tier=backend"],
            "names": ["mysql"],
            "kind": "Deployment",
        }
    Also verifies that the GVK choices are valid options for the given app."""
    for f in filterStr.split(","):
        key = f.split("=")[0].lower()
        val = f.split("=", 1)[1]
        if "namespace" in key:
            setDict.setdefault("namespaces", []).append(isRFC1123(val))
        elif "name" in key:
            setDict.setdefault("names", []).append(isRFC1123(val))
        elif "label" in key:
            setDict.setdefault("labelSelectors", []).append(val)
        elif "group" in key:
            setDict["group"] = val if not setDict.get("group") else dupeKeyError("group")
        elif "version" in key:
            setDict["version"] = val if not setDict.get("version") else dupeKeyError("version")
        elif "kind" in key:
            setDict["kind"] = val if not setDict.get("kind") else dupeKeyError("kind")
        else:
            raise SystemExit(
                f"Error: '{key}' not one of ['namespace', 'name', 'label', 'group', 'version', "
                "'kind']"
            )
    # Validate the inputs are valid assets for this app
    for key in ["group", "version", "kind"]:
        if setDict.get(key) and setDict[key] not in [a["GVK"][key] for a in assets["items"]]:
            raise SystemExit(
                f"Error: '{setDict[key]}' is not a valid '{key}' for this application, please run "
                f"'list assets {assets['metadata']['appID']}' to view possible '{key}' choices"
            )
    # Validate the inputs are valid GVK combinations
    for key1 in ["group", "version", "kind"]:
        for key2 in ["group", "version", "kind"]:
            if key1 == key2:
                continue
            if setDict.get(key1) and setDict.get(key2):
                if setDict[key1] not in [
                    a["GVK"][key1] for a in assets["items"] if a["GVK"][key2] == setDict[key2]
                ]:
                    raise SystemExit(
                        f"Error: '{key1}={setDict[key1]}' does not match with "
                        f"'{key2}={setDict[key2]}', please run 'list assets "
                        f"{assets['metadata']['appID']}' to view valid GVK combinations"
                    )


def createFilterSet(selection, filters, assets):
    """createFilterSet takes in a selection string, and a filters array of arrays, for example:
        [
            ['group=apps,version=v1,kind=Deployment'],
            ['label=app.kubernetes.io/tier=backend,name=mysql,namespace=wordpress']
        ]
    And returns an object for use in a restore filter, like so:
        {
            "GVKN": [
                {
                    "group": "apps",
                    "version": "v1",
                    "kind": "Deployment",
                },
                {
                    "labelSelectors": ["app.kubernetes.io/tier=backend"],
                    "names": ["mysql"],
                    "namespaces": ["wordpress"],
                },
            ],
            "resourceSelectionCriteria": "include",
        }
    Also performs validation to ensure that the given appID contains GVK asset type.
    """
    if selection is None:
        return None
    rFilter = {"GVKN": [], "resourceSelectionCriteria": selection}
    for fil in filters:
        setDict = {}
        if isinstance(fil, list):
            for f in fil:
                createSetDict(setDict, f, assets)
        else:
            createSetDict(setDict, fil, assets)
        rFilter["GVKN"].append(setDict)
    return rFilter


def createSingleSecretKeyDict(credKeyPair, ard, parser):
    """Given a credKeyPair list like ['s3-creds', 'accessKeyID']

    Return a dict with the following format:
    {
    "valueFromSecret":
      {
        "name": "s3-creds",
        "key": "accessKeyID",
      },
    }

    Also validate that a given key exists in the corresponding secret"""
    # argparse ensures len(args.credential) is 2, but can't ensure a valid name/key pair
    if credKeyPair[0] in [x["metadata"]["name"] for x in ard.credentials["items"]]:
        cred, key = credKeyPair
    else:
        key, cred = credKeyPair
    credDict = ard.getSingleDict("credentials", "metadata.name", cred, parser)
    if key not in credDict["data"].keys():
        parser.error(
            f"'{credKeyPair[1]}' not found in '{credKeyPair[0]}' data keys: "
            f"{', '.join(credDict['data'].keys())}"
        )
    return {"valueFromSecret": {"name": cred, "key": key}}


def createSecretKeyDict(keyNameList, args, ard, parser):
    """Use keyNameList to ensure number of credential arguments inputted is correct,
    and build the full providerCredentials dictionary"""
    # Ensure correct args.credentials length matches keyNameList length
    if len(args.credential) != len(keyNameList):
        parser.error(
            f"-s/--credential must be specified {len(keyNameList)} time(s) for "
            f"'{args.provider}' provider"
        )
    # argparse ensures len(args.credential) is 2, but can't ensure a valid name/key pair
    providerCredentials = {}
    for i, credKeyPair in enumerate(args.credential):
        providerCredentials[keyNameList[i]] = createSingleSecretKeyDict(credKeyPair, ard, parser)
    return providerCredentials


def prependDump(obj, prepend, indent=2):
    """Function to prepend a certain amount of spaces in a yaml.dump(obj) to properly
    align in nested yaml"""
    if obj is not None:
        arr = [(" " * prepend + i) for i in yaml.dump(obj, indent=indent).split("\n")]
        return "\n".join(arr).rstrip()
    return None


def checkv3Support(args, parser, supportedDict):
    """Function to ensure a v3-specific actoolkit command is currently supported by v3"""
    if supported := supportedDict.get(args.subcommand):
        if supported is True:
            return True
        elif args.objectType in supported:
            return True
    parser.error(f"'{args.subcommand} {args.objectType}' is not currently a supported --v3 command")


def setupJinja(
    objectType, filesystem=os.path.dirname(os.path.realpath(__file__)) + "/templates/jinja"
):
    """Function to load a jinja template from the filesystem based on parser objectType"""
    env = Environment(loader=FileSystemLoader(filesystem))
    return env.get_template(f"{objectType}.jinja")


def getOperatorURL(version):
    """Function to return the astraconnector_operator.yaml URL based on the version"""
    base = "https://github.com/NetApp/astra-connector-operator/releases"
    filename = "astraconnector_operator.yaml"
    if version == "latest":
        return f"{base}/{version}/download/{filename}"
    elif "-main" in version:
        return f"{base}/download/{version}/{filename}"
    return f"{base}/download/{version}-main/{filename}"
