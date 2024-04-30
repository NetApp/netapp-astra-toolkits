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

import yaml
import json
import copy

from .common import SDKCommon


YELLOW = "\033[33m"
ENDC = "\033[0m"


class getUsers(SDKCommon):
    """Get all the users in Astra Control"""

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
            if not self.quiet:
                super().printError(ret)
            return False


class createUser(SDKCommon):
    """Create a user within the Astra Control account.  This class does not do argument
    verification, please reference toolkit.py which has proper guardrails (primarily
    around the differences between Astra Control Center and Service)."""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
        self.headers["accept"] = "application/astra-user+json"
        self.headers["Content-Type"] = "application/astra-user+json"

    def main(
        self,
        email,
        firstName=None,
        lastName=None,
        companyName=None,
        phone=None,
        authProvider=None,
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
        if authProvider:
            data["authProvider"] = authProvider

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
                super().printError(ret)
            return False


class destroyUser(SDKCommon):
    """Destroys a users (this class is only required to be called for LDAP-based users)"""

    def __init__(self, quiet=True, verbose=False, config=None):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        config: optionally provide a pre-populated common.getConfig().main() object"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__(config=config)
        self.headers["accept"] = "application/astra-user+json"
        self.headers["Content-Type"] = "application/astra-user+json"

    def main(self, userID):
        endpoint = f"core/v1/users/{userID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-user",
            "version": "1.2",
        }

        ret = super().apicall(
            "delete",
            url,
            data,
            self.headers,
            params,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            return True
        else:
            if not self.quiet:
                super().printError(ret)
            return False


class getLdapUsers(SDKCommon):
    """Query LDAP for a list of users"""

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

    def main(
        self,
        emailFilter=None,
        firstNameFilter=None,
        lastNameFilter=None,
        cnFilter=None,
        limit=25,
        cont=None,
        matchType="in",
    ):
        endpoint = "core/v1/ldapUsers"
        url = self.base + endpoint

        data = {}
        params = {}
        if emailFilter or firstNameFilter or lastNameFilter or cnFilter:
            params["filter"] = []
            if emailFilter:
                params["filter"].append(f"email {matchType} '{emailFilter}'")
            if firstNameFilter:
                params["filter"].append(f"firstName {matchType} '{firstNameFilter}'")
            if lastNameFilter:
                params["filter"].append(f"lastName {matchType} '{lastNameFilter}'")
            if cnFilter:
                params["filter"].append(f"cn {matchType} '{cnFilter}'")
        if limit and int(limit) != 0:
            params["limit"] = limit
        if cont:
            params["continue"] = cont

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
            users = super().jsonifyResults(ret)

            if self.output == "json":
                dataReturn = users
            elif self.output == "yaml":
                dataReturn = yaml.dump(users)
            elif self.output == "table":
                contStr = ""
                if users["metadata"].get("continue"):
                    contStr = f"\n{YELLOW}continue-token: {users['metadata']['continue']}{ENDC}"
                dataReturn = (
                    self.basicTable(
                        ["ldapUserID", "email", "firstName", "lastName", "cn", "dn"],
                        ["id", "email", "firstName", "lastName", "cn", "dn"],
                        users,
                    )
                    + contStr
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                super().printError(ret)
            return False
