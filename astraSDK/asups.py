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


class getAsups(SDKCommon):
    """This class gets all Astra Control auto-support bundles via the core/v1/asups endpoint.
    This functionality is currently only supported with ACC."""

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

    def main(self, triggerTypeFilter=None, uploadFilter=None):
        endpoint = "core/v1/asups"
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
            if triggerTypeFilter or uploadFilter:
                asupsCopy = copy.deepcopy(results)
                for counter, asup in enumerate(asupsCopy.get("items")):
                    if triggerTypeFilter and triggerTypeFilter != asup["triggerType"]:
                        results["items"].remove(asupsCopy["items"][counter])
                    elif uploadFilter and uploadFilter != asup["upload"]:
                        results["items"].remove(asupsCopy["items"][counter])
            if self.output == "json":
                dataReturn = results
            elif self.output == "yaml":
                dataReturn = yaml.dump(results)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    [
                        "asupID",
                        "state",
                        "upload",
                        "uploadState",
                        "triggerType",
                        "dataWindowStart",
                        "dataWindowEnd",
                    ],
                    [
                        "id",
                        "creationState",
                        "upload",
                        "uploadState",
                        "triggerType",
                        "dataWindowStart",
                        "dataWindowEnd",
                    ],
                    results,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                if ret.status_code == 500:
                    super().printError("Error: the core/v1/asups API is only supported on ACC.\n")
                else:
                    super().printError(ret)
            return False


class downloadAsup(SDKCommon):
    """This class downloads an Astra Control auto-support bundles via the core/v1/asups endpoint.
    This functionality is currently only supported with ACC."""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
        self.headers["accept"] = "application/gzip"
        self.headers["Content-Type"] = "application/gzip"

    def main(self, asupID):
        endpoint = f"core/v1/asups/{asupID}"
        url = self.base + endpoint

        data = {}
        params = {}

        ret, filename = super().downloadFile(
            url, data, self.headers, params, quiet=self.quiet, verbose=self.verbose
        )

        if ret.ok:
            if not self.quiet:
                print(f"'{filename}' downloaded to current directory successfully.")
            return filename

        else:
            if not self.quiet:
                if ret.status_code == 500:
                    super().printError("Error: the core/v1/asups API is only supported on ACC.\n")
                else:
                    super().printError(ret)
            return False


class createAsup(SDKCommon):
    """This class creates an Astra Control auto-support bundle via the core/v1/asups endpoint.

    upload: should be one of "true" or "false" (str, not bool).
    dataWindowStart: JSON string containing a timestamp indicating the start time of the ASUP.
        Defaults to 24 hours before dataWindowEnd, must occur before dataWindowEnd, max is 7 days
        before the current time.
    dataWindowEnd: JSON string containing a timestamp indicating the end time of the ASUP.
        Defaults to the current time of the request.
    dataWindowStart and dataWindowEnd must conform to the ISO-8601 Date Time Schema.

    There is no validation of this input, that instead is left to the calling method."""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
        self.headers["accept"] = "application/astra-asup+json"
        self.headers["Content-Type"] = "application/astra-asup+json"

    def main(
        self,
        upload,
        dataWindowStart=None,
        dataWindowEnd=None,
    ):
        endpoint = "core/v1/asups"
        url = self.base + endpoint
        params = {}
        data = {
            "upload": upload,
            "type": "application/astra-asup",
            "version": "1.0",
        }
        if dataWindowStart:
            data["dataWindowStart"] = dataWindowStart
        if dataWindowEnd:
            data["dataWindowEnd"] = dataWindowEnd

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
                if ret.status_code == 404:
                    super().printError("Error: the core/v1/asups API is only supported on ACC.\n")
                else:
                    super().printError(ret)
            return False
