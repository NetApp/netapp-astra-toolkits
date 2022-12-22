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
from .apps import getApps


class getHooks(SDKCommon):
    """Get all the execution hooks for every app"""

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
        self.apps = getApps(quiet=True, verbose=verbose).main()

    def main(self, appFilter=None):
        if self.apps is False:
            print("Call to getApps() failed")
            return False

        hooks = {}
        hooks["items"] = []

        for app in self.apps["items"]:
            if appFilter:
                if app["name"] != appFilter and app["id"] != appFilter:
                    continue
            endpoint = f"k8s/v1/apps/{app['id']}/executionHooks"
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
                if results is None:
                    continue
                for item in results["items"]:
                    hooks["items"].append(item)
                if not self.quiet and self.verbose:
                    print(f"Execution hooks for {app['id']}")
                    if self.output == "json":
                        print(json.dumps(results))
                    elif self.output == "yaml":
                        print(yaml.dump(results))
                    elif self.output == "table":
                        print(
                            self.basicTable(
                                ["hookName", "hookID", "matchingImages"],
                                ["name", "id", "matchingImages"],
                                results,
                            )
                        )
                        print()
            else:
                continue
        if self.output == "json":
            dataReturn = hooks
        elif self.output == "yaml":
            dataReturn = yaml.dump(hooks)
        elif self.output == "table":
            dataReturn = self.basicTable(
                ["appID", "hookName", "hookID", "matchingImages"],
                ["appID", "name", "id", "matchingImages"],
                hooks,
            )

        if not self.quiet:
            print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
        return dataReturn


class createHook(SDKCommon):
    """Create an execution hook"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-executionHook+json"
        self.headers["Content-Type"] = "application/astra-executionHook+json"

    def main(
        self,
        appID,
        name,
        scriptID,
        stage,
        action,
        arguments,
        matchingCriteria=[],
        containerRegex=None,
        description=None,
    ):

        endpoint = f"k8s/v1/apps/{appID}/executionHooks"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-executionHook",
            "version": "1.2",
            "name": name,
            "hookType": "custom",
            "action": action,
            "stage": stage,
            "hookSourceID": scriptID,
            "arguments": arguments,
            "appID": appID,
            "matchingCriteria": matchingCriteria,
            "enabled": "true",
        }
        if description:
            data["description"] = description
        # For backwards compatibility, recommend instead using matchingCriteria argument directly
        if containerRegex:
            data["matchingCriteria"].append({"type": "containerImage", "value": containerRegex})

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


class destroyHook(SDKCommon):
    """Given an appID and hookID destroy the hook.  Note that this doesn't unmanage
    a hook, it actively destroys it. There is no coming back from this."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-executionHook+json"
        self.headers["Content-Type"] = "application/astra-executionHook+json"

    def main(self, appID, hookID):

        # endpoint = f"k8s/v1/apps/{appID}/executionHooks/{hookID}"
        endpoint = f"core/v1/executionHooks/{hookID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-hookSource",
            "version": "1.0",
            "appID": appID,  # Not strictly required at this time
        }

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
