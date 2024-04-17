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

import json
import kubernetes
import os
import sys
import yaml
from tabulate import tabulate
import textwrap
import requests
from urllib3 import disable_warnings

RED = "\033[31m"
GREEN = "\033[32m"
ENDC = "\033[0m"


class getConfig:
    """In order to make API calls to Astra Control we need to know which Astra Control instance
    to connect to, and the credentials to make calls.  This info is found in config.yaml,
    which we search for in the following four places:
    1) The current working directory that the executed function is located in
    2) ~/.config/astra-toolkits/
    3) /etc/astra-toolkits/
    4) The directory pointed to by the shell env var ASTRATOOLKITS_CONF
    """

    def __init__(self):
        self.conf = None
        for loc in (
            os.getcwd(),
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
                print(f"{configFile} not valid YAML")
                continue

        if self.conf is None:
            raise SystemExit("config.yaml not found.")

        for item in ["astra_project", "uid", "headers"]:
            try:
                assert self.conf.get(item) is not None
            except AssertionError:
                raise SystemExit(f"{item} is a required field in {configFile}")

        if "." in self.conf.get("astra_project"):
            self.domain = self.conf.get("astra_project")
        else:
            self.domain = "%s.astra.netapp.io" % (self.conf.get("astra_project"))
        self.account_id = self.conf.get("uid")
        self.base = "https://%s/accounts/%s/" % (self.domain, self.account_id)
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
            "domain": self.domain,
            "account_id": self.account_id,
        }


class BaseCommon:
    def __init__(self):
        pass

    def printError(self, ret):
        """Function to print relevant error information when a call fails"""
        try:
            sys.stderr.write(RED + json.dumps(json.loads(ret.text), indent=2) + f"{ENDC}\n")
        except json.decoder.JSONDecodeError:
            sys.stderr.write(f"{RED}{ret.text}{ENDC}")
        except AttributeError:
            sys.stderr.write(f"{RED}{ret}{ENDC}")

    def recursiveGet(self, k, item, conCatList=None):
        """Recursion function which is just a wrapper around dict.get(key), to handle cases
        where there's a dict or list within a dict:
         - '.' in the key name ('metadata.creationTimestamp') is used to identify a dict
         - '[]' in the key name ('spec.includedNamespaces[]') is used to identify a list
         - '*' as a key represents a wildcard (returns first entry)
         - 'KEYS' represents returning the keys rather than the vaules."""
        if len(k.split(".")) > 1 and k.split(".")[0] == "":
            return self.recursiveGet(k.split(".", 1)[1], item, conCatList)
        elif (len(k.split(".")) > 1 and len(k.split("[]")) == 1) or (
            len(k.split(".")[0]) < len(k.split("[]")[0])
        ):
            if k.split(".")[0] == "*":
                return self.recursiveGet(k.split(".", 1)[1], item[next(iter(item))], conCatList)
            elif k.split(".")[0] == "KEYS":
                return self.recursiveGet(
                    k.split(".", 1)[1], item[k.split(".")[0]].keys(), conCatList
                )
            try:
                return self.recursiveGet(k.split(".", 1)[1], item[k.split(".")[0]], conCatList)
            except KeyError:
                return "None"
        elif (len(k.split("[]")) > 1 and len(k.split(".")) == 1) or (
            len(k.split("[]")[0]) < len(k.split(".")[0])
        ):
            if conCatList is None:
                conCatList = []
            for i in item[k.split("[]")[0]]:
                if add := self.recursiveGet(k.split("[]", 1)[1], i, []):
                    conCatList.append(add)
            return ", ".join(conCatList)
        if k == "KEYS":
            return list(item.keys())
        elif k == "*":
            return item[next(iter(item))]
        elif isinstance(item, dict) and isinstance(item.get(k), dict):
            return str(item.get(k))
        elif isinstance(item, dict):
            return item.get(k)
        return ""

    def basicTable(self, tabHeader, tabKeys, dataDict, tablefmt="grid"):
        """Function to create a basic tabulate table for terminal printing"""
        tabData = []
        for item in dataDict["items"]:
            # Generate a table row based on the keys list
            row = [self.recursiveGet(k, item, []) for k in tabKeys]
            # Handle cases where table row has a nested list
            for c, r in enumerate(row):
                if type(r) is list:
                    row[c] = ", ".join(r)
            # Wrap text over 80 characters
            row = [textwrap.fill(r, width=80) if isinstance(r, str) else r for r in row]
            tabData.append(row)
        return tabulate(tabData, tabHeader, tablefmt=tablefmt)


class SDKCommon(BaseCommon):
    def __init__(self):
        super().__init__()
        self.conf = getConfig().main()
        self.base = self.conf.get("base")
        self.headers = self.conf.get("headers")
        self.verifySSL = self.conf.get("verifySSL")

    def apicall(self, method, url, data, headers, params, verify, quiet=False, verbose=False):
        """Make a call using the requests module.
        method can be get, put, post, patch, or delete"""
        try:
            r = getattr(requests, method)
        except AttributeError as e:
            raise SystemExit(e)
        try:
            if verbose:
                self.printVerbose(url, method, headers, data, params)
            ret = r(url, json=data, headers=headers, params=params, verify=verify)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        if not ret.ok:
            # GET clouds has more response information than other calls, so if
            # there's an error make a second API call to improve error messaging
            if (
                url.split("/")[-1] != "clouds"
                or (url.split("/")[-1] == "clouds" and method != "get")
                or (url.split("/")[-1] == "clouds" and quiet is True)
            ):
                self.apicall(
                    "get",
                    self.base + "topology/v1/clouds",
                    {},
                    self.headers,
                    {},
                    self.verifySSL,
                    quiet=False,
                    verbose=False,
                )
            elif ret.status_code >= 400 and ret.status_code < 500:
                if "x-pcloud-accountid" in ret.text:
                    print(f"API call to Astra Control failed: {RED}check uid in config.json{ENDC}")
                elif ret.status_code == 401:
                    print(
                        "API call to Astra Control failed: "
                        f"{RED}check Authorization in config.json{ENDC}"
                    )
                else:
                    print(
                        "API call to Astra Control failed: "
                        f"{RED}{ret.status_code} - {ret.reason}{ENDC}"
                    )
                    if ret.text.strip():
                        print(f"text: {ret.text.strip()}")
            else:
                print("API call to Astra Control failed (Internal Server Error)")
                print(f"API HTTP Status Code: {ret.status_code} - {ret.reason}")
                if ret.text.strip():
                    print(f"text: {ret.text}")
        if verbose:
            print(f"{GREEN}API HTTP Status Code: {ret.status_code}{ENDC}")
        return ret

    def jsonifyResults(self, requestsObject):
        try:
            results = requestsObject.json()
        except ValueError as e:
            print(f"response contained invalid JSON: {e}")
            results = None
        return results

    def printVerbose(self, url, method, headers, data, params):
        """Function to print API call details when in verbose mode"""
        print(f"{GREEN}API URL: {url}{ENDC}")
        print(f"{GREEN}API Method: {method}{ENDC}")
        print(f"{GREEN}API Headers: {headers}{ENDC}")
        print(f"{GREEN}API data: {data}{ENDC}")
        print(f"{GREEN}API params: {params}{ENDC}")


class KubeCommon(BaseCommon):
    def __init__(self, config_context=None, client_configuration=None, silently_fail=False):
        super().__init__()
        if (
            isinstance(client_configuration, kubernetes.client.configuration.Configuration)
            and client_configuration.verify_ssl is False
        ):
            disable_warnings()

        # Setup the config_file and context based on the config_context input
        config_file, context = None, None
        # If "None" was passed, just use current kube config_file and context
        if config_context == "None":
            pass
        # If a "@" is present, it must be a context@config_file mapping
        elif config_context and "@" in config_context:
            context, config_file = tuple(config_context.split("@"))
            config_file = None if config_file == "None" else config_file
        # If a "@" isn't present, we need to determine if a config_file or context was passed
        elif config_context:
            try:
                # First see if the input is part of the contexts on the default kubeconfig
                default_contexts, _ = kubernetes.config.kube_config.list_kube_config_contexts(
                    config_file=None
                )
                if config_context in [c["name"] for c in default_contexts]:
                    context = config_context
                # If it's not, assume a config_file was passed
                else:
                    config_file = config_context
            # Or if an exception occurs, the default ~/.kube/config likely doesn't exist, in which
            # case also assume a config_file was passed
            except kubernetes.config.config_exception.ConfigException:
                config_file = config_context
        try:
            # Create the api_client
            kubernetes.config.load_kube_config(
                config_file=config_file, context=context, client_configuration=client_configuration
            )
            self.api_client = kubernetes.client.ApiClient(configuration=client_configuration)

        # If that fails, then try an incluster config
        except kubernetes.config.config_exception.ConfigException as err:
            try:
                self.api_client = kubernetes.client.ApiClient(
                    configuration=kubernetes.config.load_incluster_config()
                )
            except kubernetes.config.config_exception.ConfigException:
                if not silently_fail:
                    self.printError(f"{err}\n")
                    self.printError(
                        f"Please ensure '{config_context}' is either a valid kubernetes "
                        "config_file, context, or 'context@config_file' mapping, and you have "
                        "network connectivity to the cluster.\n"
                    )
                    raise SystemExit()
                self.api_client = None

        # Catch other errors (like malformed files), print error message, and exit
        except Exception as err:
            if not silently_fail:
                self.printError(
                    "Error loading kubeconfig, please check kubeconfig file to ensure it is valid\n"
                )
                self.printError(f"{err}\n")
                raise SystemExit()
            self.api_client = None

    def notInstalled(self, path):
        server = self.api_client.configuration.host.split("//")[-1].split(":")[0].split("/")[0]
        self.printError(
            f"Error: {path} not found, please ensure the AstraConnector Operator is installed on "
            f"cluster {server}.\n"
        )
        raise SystemExit()

    def printKubeError(self, e):
        if hasattr(e, "body"):
            e.text = e.body
            self.printError(e)
        elif hasattr(e, "reason"):
            self.printError(e.reason)
        else:
            self.printError(e)

    class WriteVerbose:
        def __init__(self):
            self.content = []

        def write(self, string):
            if string[:2] == "b'" or string[:2] == 'b"':
                string = string[2:-1]
            elif (string[:1] == "'" and string[-1:] == "'") or (
                string[:1] == '"' and string[-1:] == '"'
            ):
                string = string[1:-1]
            self.content.append(string)

        def print(self):
            verbose_info = "".join(self.content).replace("\\r\\n", "\n")
            verbose_info = "\n".join(
                [ll.rstrip() for ll in verbose_info.splitlines() if ll.strip()]
            )
            print(f"{GREEN}{verbose_info}{ENDC}")
