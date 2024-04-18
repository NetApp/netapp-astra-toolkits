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

import base64
import json
import os
import re
import subprocess
import yaml

from jinja2 import Environment, FileSystemLoader

import astraSDK


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
                "destination": isRFC1123(singleNs, parser=parser),
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
                {
                    "source": mapping.split("=")[0],
                    "destination": isRFC1123(mapping.split("=")[1], parser=parser),
                }
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
            if csr[0] == f"{resource['apiVersion']}/{resource['kind']}":
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
                        returnList[-1]["labelSelector"] = {
                            "matchLabels": {csr[1].split("=")[0]: csr[1].split("=")[1]}
                        }
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


def isRFC1123(string, parser=None, ignore_length=False):
    """isRFC1123 returns the input 'string' if it conforms to RFC 1123 spec,
    otherwise it throws an error and exits"""
    regex = re.compile("[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
    if regex.match(string) is not None and (len(string) < 64 or ignore_length):
        return string
    else:
        error = (
            f"'{string}' must consist of lower case alphanumeric characters or '-', must start "
            "and end with an alphanumeric character, and must be at most 63 characters (for "
            "example 'my-name' or '123-abc')."
        )
        if parser is not None:
            parser.error(error)
        else:
            raise SystemExit(f"Error: {error}")


def dupeKeyError(key, parser):
    """Print an error message if duplicate keys are used"""
    parser.error(f"'{key}' should not be specified multiple times within a single --filterSet arg")


def createSetDict(setDict, filterStr, assets, parser, v3=False):
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
            setDict["group"] = val if not setDict.get("group") else dupeKeyError("group", parser)
        elif "version" in key:
            setDict["version"] = (
                val if not setDict.get("version") else dupeKeyError("version", parser)
            )
        elif "kind" in key:
            setDict["kind"] = val if not setDict.get("kind") else dupeKeyError("kind", parser)
        else:
            parser.error(
                f"'{key}' not one of ['namespace', 'name', 'label', 'group', 'version', 'kind']"
            )
    # TODO: Add v3 validation once ASTRACTL-31946 is complete
    if not v3:
        # Validate the inputs are valid assets for this app
        for key in ["group", "version", "kind"]:
            if setDict.get(key) and setDict[key] not in [a["GVK"][key] for a in assets["items"]]:
                parser.error(
                    f"'{setDict[key]}' is not a valid '{key}' for this application, please run '"
                    f"list assets {assets['metadata']['appID']}' to view possible '{key}' choices"
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
                        parser.error(
                            f"'{key1}={setDict[key1]}' does not match with '{key2}={setDict[key2]}'"
                            f", please run 'list assets {assets['metadata']['appID']}' to view "
                            "valid GVK combinations"
                        )


def createFilterSet(selection, filters, assets, parser, v3=False):
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
    if v3:
        filterKey = "resourceMatchers"
    else:
        filterKey = "GVKN"
    rFilter = {filterKey: [], "resourceSelectionCriteria": selection}
    for fil in filters:
        setDict = {}
        if isinstance(fil, list):
            for f in fil:
                createSetDict(setDict, f, assets, parser, v3=v3)
        else:
            createSetDict(setDict, fil, assets, parser, v3=v3)
        rFilter[filterKey].append(setDict)
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


def createSecretKeyDict(keyNameList, credential, provider, ard, parser):
    """Use keyNameList to ensure number of credential arguments inputted is correct,
    and build the full providerCredentials dictionary"""
    # Ensure correct credential length matches keyNameList length
    if len(credential) != len(keyNameList):
        parser.error(
            f"-s/--credential must be specified {len(keyNameList)} time(s) for "
            f"'{provider}' provider"
        )
    # argparse ensures len(args.credential) is 2, but can't ensure a valid name/key pair
    providerCredentials = {}
    for i, credKeyPair in enumerate(credential):
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
    elif "-" in version:
        return f"{base}/download/{version}/{filename}"
    return f"{base}/download/{version}-main/{filename}"


def sameK8sCluster(cluster1, cluster2, skip_tls_verify=False):
    """Function which determines if cluster1 and cluster2 are the same underlying Kubernetes
    clusters or not. Returns True if metadata.uid of the kube-system NS are the same."""
    namespaces1 = astraSDK.k8s.getNamespaces(
        config_context=cluster1, skip_tls_verify=skip_tls_verify
    ).main(systemNS=[])
    namespaces2 = astraSDK.k8s.getNamespaces(
        config_context=cluster2, skip_tls_verify=skip_tls_verify
    ).main(systemNS=[])
    ks1 = next(n for n in namespaces1["items"] if n["metadata"]["name"] == "kube-system")
    ks2 = next(n for n in namespaces2["items"] if n["metadata"]["name"] == "kube-system")
    if ks1["metadata"]["uid"] == ks2["metadata"]["uid"]:
        return True
    return False


def getCommonAppVault(cluster1, cluster2, parser, skip_tls_verify=False):
    """Function which takes in two cluster contexts, and finds and returns an appVault that's
    common between the two of them, as designated by status.uid"""
    c1AppVaults = astraSDK.k8s.getResources(
        config_context=cluster1, skip_tls_verify=skip_tls_verify
    ).main("appvaults")
    c2AppVaults = astraSDK.k8s.getResources(
        config_context=cluster2, skip_tls_verify=skip_tls_verify
    ).main("appvaults")
    for c1av in c1AppVaults["items"]:
        for c2av in c2AppVaults["items"]:
            if c1av.get("status") and c1av["status"].get("uid"):
                if c2av.get("status") and c2av["status"].get("uid"):
                    if c1av["status"]["uid"] == c2av["status"]["uid"]:
                        return c1av
    parser.error(f"A common appVault was not found between cluster {cluster1} and {cluster2}")


def swapAppVaultRef(sourceAppVaultRef, sourceCluster, destCluster, parser, skip_tls_verify=False):
    """Function which takes in the name of a sourceCluster's appVaultRef, and then returns
    the name of the destCluster's same appVaultRef (appVaults can be named differently across
    clusters due to Astra Control auto-appending a unique identifier)."""
    sourceAppVaults = astraSDK.k8s.getResources(
        config_context=sourceCluster, skip_tls_verify=skip_tls_verify
    ).main("appvaults")
    destAppVaults = astraSDK.k8s.getResources(
        config_context=destCluster, skip_tls_verify=skip_tls_verify
    ).main("appvaults")
    try:
        sourceAppVault = next(
            a for a in sourceAppVaults["items"] if a["metadata"]["name"] == sourceAppVaultRef
        )
        sourceUid = sourceAppVault["status"]["uid"]
    except StopIteration:
        parser.error(f"'{sourceAppVaultRef}' not found on the source cluster,\n{sourceAppVaults=}")
    except KeyError as err:
        parser.error(f"{err} key not found in '{sourceAppVaultRef}' object,\n{sourceAppVaults=}")
    try:
        destAppVault = next(a for a in destAppVaults["items"] if a["status"]["uid"] == sourceUid)
        return destAppVault["metadata"]["name"]
    except StopIteration:
        destAppVaultSum = [
            {"name": d["metadata"]["name"], "uid": d["status"]["uid"]}
            for d in destAppVaults["items"]
        ]
        parser.error(
            f"An appVault with status.uid of '{sourceUid}' not found on the destination cluster,"
            f" destination app vaults: {destAppVaultSum}"
        )
    except KeyError as err:
        parser.error(f"{err} key not found in 'destAppVault' object,\n{destAppVaults=}")


def openJson(path, parser):
    """Given a file path, open the json file, and return a dict of its contents"""
    with open(path, encoding="utf8") as f:
        try:
            return json.loads(f.read().rstrip())
        except json.decoder.JSONDecodeError:
            parser.error(f"{path} does not seem to be valid JSON")


def openScript(path, parser):
    """Given a file path, open the text file, and return a str of its contents"""
    with open(path, encoding="utf8") as f:
        return base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")


def openYaml(path, parser):
    """Given a file path, open the yaml file, and return a dict of its contents"""
    with open(path, encoding="utf8") as f:
        try:
            return yaml.load(f.read().rstrip(), Loader=yaml.SafeLoader)
        except (yaml.scanner.ScannerError, IsADirectoryError):
            parser.error(f"{path} does not seem to be valid YAML")


def getNestedValue(obj, key):
    """Iterate through a nested dict / list to search for a particular key,
    it returns the first match"""
    if hasattr(obj, "items"):
        for k, o in obj.items():
            if k == key:
                yield o
            if isinstance(o, dict):
                for result in getNestedValue(o, key):
                    yield result
            elif isinstance(o, list):
                for d in o:
                    for result in getNestedValue(d, key):
                        yield result


def extractAwsKeys(path, parser):
    """Returns a tuple of the AccessKeyId, SecretAccessKey in an AWS credential JSON"""
    awsCreds = openJson(path, parser)
    accessKeyID = "".join(getNestedValue(awsCreds, "AccessKeyId"))
    secretAccessKey = "".join(getNestedValue(awsCreds, "SecretAccessKey"))
    if not accessKeyID:
        parser.error(f"'AccessKeyId' not found in '{path}'")
    if not secretAccessKey:
        parser.error(f"'SecretAccessKey' not found in '{path}'")
    return accessKeyID, secretAccessKey


def combineResources(*args):
    """Accepts any number of {"items":[]} inputs, concatenates the lists, returns a dict"""
    base_dict = {"apiVersion": "v1", "items": [], "kind": "List"}
    for resource in args:
        base_dict["items"] += resource["items"]
    return base_dict
