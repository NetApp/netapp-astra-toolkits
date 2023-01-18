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

from .common import SDKCommon


class getScripts(SDKCommon):
    """Get all the scripts (aka hook sources) for the Astra Control account"""

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

    def main(self, nameFilter=None):

        endpoint = "core/v1/hookSources"
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
            scripts = super().jsonifyResults(ret)
            scriptsCooked = copy.deepcopy(scripts)
            for counter, script in enumerate(scripts.get("items")):
                if nameFilter and nameFilter not in script.get("name"):
                    scriptsCooked["items"].remove(scripts["items"][counter])

            if self.output == "json":
                dataReturn = scriptsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(scriptsCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["scriptName", "scriptID", "description"],
                    ["name", "id", "description"],
                    scriptsCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            return False


class createScript(SDKCommon):
    """Create a script (aka hook source)"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-hookSource+json"
        self.headers["Content-Type"] = "application/astra-hookSource+json"

    def main(
        self,
        name,
        source,
        description=None,
    ):

        endpoint = f"core/v1/hookSources"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-hookSource",
            "version": "1.0",
            "name": name,
            "source": source,
            "sourceType": "script",
        }
        if description:
            data["description"] = description

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


class destroyScript(SDKCommon):
    """Given a scriptID destroy the script.  Note that this doesn't unmanage
    a script, it actively destroys it. There is no coming back from this."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-hookSource+json"
        self.headers["Content-Type"] = "application/astra-hookSource+json"

    def main(self, scriptID):

        endpoint = f"core/v1/hookSources/{scriptID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-hookSource",
            "version": "1.0",
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
