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


YELLOW = "\033[33m"
ENDC = "\033[0m"


class getGroups(SDKCommon):
    """Get all the groups in Astra Control"""

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
        endpoint = "core/v1/groups"
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
            groups = super().jsonifyResults(ret)

            if self.output == "json":
                dataReturn = groups
            elif self.output == "yaml":
                dataReturn = yaml.dump(groups)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["groupID", "name", "authID", "authProvider"],
                    ["id", "name", "authID", "authProvider"],
                    groups,
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                super().printError(ret)
            return False


class createGroup(SDKCommon):
    """Create a group within the Astra Control account.  This class does not do argument
    verification, please reference toolkit.py which has proper guardrails"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-group+json"
        self.headers["Content-Type"] = "application/astra-group+json"

    def main(
        self,
        authID,
        authProvider="ldap",
    ):
        endpoint = "core/v1/groups"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-group",
            "version": "1.1",
            "authID": authID,
            "authProvider": authProvider,
        }

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
            if not self.quiet:
                super().printError(ret)
            return False


class destroyGroup(SDKCommon):
    """Destroys a group"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-group+json"
        self.headers["Content-Type"] = "application/astra-group+json"

    def main(self, groupID):
        endpoint = f"core/v1/groups/{groupID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-group",
            "version": "1.1",
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

        if ret.ok:
            return True
        else:
            if not self.quiet:
                super().printError(ret)
            return False


class getLdapGroups(SDKCommon):
    """Query LDAP for a list of groups"""

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

    def main(
        self,
        cnFilter=None,
        dnFilter=None,
        limit=25,
        cont=None,
        matchType="in",
    ):
        if matchType != "in" and matchType != "eq":
            raise SystemError("matchType must be one of: in, eq")
        endpoint = "core/v1/ldapGroups"
        url = self.base + endpoint

        data = {}
        params = {}
        if cnFilter or dnFilter:
            params["filter"] = []
            # Group filters are non-intuitive with 'eq', so do 'in' and apply filters post-call
            if cnFilter:
                params["filter"].append(f"cn in '{cnFilter}'")
            if dnFilter:
                params["filter"].append(f"dn in '{dnFilter}'")
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
            self.verifySSL,
            quiet=self.quiet,
            verbose=self.verbose,
        )

        if ret.ok:
            groups = super().jsonifyResults(ret)
            if matchType == "eq":
                groupsCopy = copy.deepcopy(groups)
                for counter, g in enumerate(groupsCopy.get("items")):
                    if cnFilter and cnFilter != g["cn"]:
                        groups["items"].remove(groupsCopy["items"][counter])
                    elif dnFilter and dnFilter != g["dn"]:
                        groups["items"].remove(groupsCopy["items"][counter])

            if self.output == "json":
                dataReturn = groups
            elif self.output == "yaml":
                dataReturn = yaml.dump(groups)
            elif self.output == "table":
                contStr = ""
                if groups["metadata"].get("continue"):
                    contStr = f"\n{YELLOW}continue-token: {groups['metadata']['continue']}{ENDC}"
                dataReturn = (
                    self.basicTable(["ldapGroupID", "cn", "dn"], ["id", "cn", "dn"], groups)
                    + contStr
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            if not self.quiet:
                super().printError(ret)
            return False
