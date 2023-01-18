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


class getRolebindings(SDKCommon):
    """Get all the role bindings in Astra Control"""

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

    def main(self, idFilter=None):

        endpoint = "core/v1/roleBindings"
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
            rbindings = super().jsonifyResults(ret)
            rbindingsCooked = copy.deepcopy(rbindings)
            for counter, binding in enumerate(rbindings.get("items")):
                if idFilter and idFilter != binding["userID"] and idFilter != binding["groupID"]:
                    rbindingsCooked["items"].remove(rbindings["items"][counter])

            if self.output == "json":
                dataReturn = rbindingsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(rbindingsCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["roleBindingID", "principalType", "userID", "role", "roleConstraints"],
                    ["id", "principalType", "userID", "role", "roleConstraints"],
                    rbindingsCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            return False


class createRolebinding(SDKCommon):
    """Create a role binding within the Astra Control account."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-roleBinding+json"
        self.headers["Content-Type"] = "application/astra-roleBinding+json"

    def main(
        self,
        role,
        userID=None,
        groupID=None,
        roleConstraints=None,
    ):

        endpoint = f"core/v1/roleBindings"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-roleBinding",
            "version": "1.1",
            "accountID": self.base.split("/")[4],
            "role": role,
        }
        if userID:
            data["userID"] = userID
        elif groupID:  # 'elif' as only userID OR groupID can be used
            data["groupID"] = groupID
        if roleConstraints:
            data["roleConstraints"] = roleConstraints

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


class destroyRolebinding(SDKCommon):
    """This class destroys a roleBinding.  Use with caution, there's no going back.

    Deleting the last role-binding associated with a user with authProvider as 'local',
    or 'cloud-central' triggers the deletion of the user."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-roleBinding+json"
        self.headers["Content-Type"] = "application/astra-roleBinding+json"

    def main(self, roleBindingID):

        endpoint = f"core/v1/roleBindings/{roleBindingID}"
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

        return True if ret.ok else False
