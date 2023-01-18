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
from termcolor import colored

from .common import SDKCommon


class getUsers(SDKCommon):
    """Get all the users in Astra Control"""

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

        endpoint = "core/v1/users"
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
            users = super().jsonifyResults(ret)
            # Add custom fullName entry
            for user in users["items"]:
                if not user.get("fullName"):
                    user["fullName"] = user.get("firstName") + " " + user.get("lastName")
            usersCooked = copy.deepcopy(users)
            if nameFilter:
                for counter, user in enumerate(users.get("items")):
                    if (
                        nameFilter.lower() not in user.get("firstName").lower()
                        and nameFilter.lower() not in user.get("lastName").lower()
                    ):
                        usersCooked["items"].remove(users["items"][counter])

            if self.output == "json":
                dataReturn = usersCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(usersCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["userID", "name", "email", "authProvider", "state"],
                    ["id", "fullName", "email", "authProvider", "state"],
                    usersCooked,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            return False


class createUser(SDKCommon):
    """Create a user within the Astra Control account.  This class does not do argument
    verification, please reference toolkit.py which has proper guardrails (primarily
    around the differences between Astra Control Center and Service)."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-user+json"
        self.headers["Content-Type"] = "application/astra-user+json"

    def main(
        self,
        email,
        firstName=None,
        lastName=None,
        companyName=None,
        phone=None,
    ):

        endpoint = "core/v1/users"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-user",
            "version": "1.2",
            "email": email,
        }
        if firstName:
            data["firstName"] = firstName
        if lastName:
            data["lastName"] = lastName
        if companyName:
            data["companyName"] = companyName
        if phone:
            data["phone"] = phone

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
