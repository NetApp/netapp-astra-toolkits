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

from .common import SDKCommon


class getSettings(SDKCommon):
    """List the Astra Control settings, which contain UUIDs which are needed to modify any
    of the settings."""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()

    def main(self):
        endpoint = "core/v1/settings"
        params = {}
        url = self.base + endpoint
        data = {}
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
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            return False


class manageLdap(SDKCommon):
    """Class to manage an LDAP(S) server"""

    def __init__(self, quiet=True, verbose=False):
        """quiet: Will there be CLI output or just return (datastructure)
        verbose: Print all of the ReST call info: URL, Method, Headers, Request Body
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.verbose = verbose
        super().__init__()
        self.headers["accept"] = "application/astra-setting+json"
        self.headers["Content-Type"] = "application/astra-setting+json"

    def main(
        self,
        settingID,
        host,
        port,
        credentialID,
        userBaseDN,
        userSearchFilter,
        userLoginAttribute,
        groupBaseDN,
        groupSearchFilter=None,
        secureMode=False,
    ):
        endpoint = f"core/v1/settings/{settingID}"
        url = self.base + endpoint
        params = {}
        data = {
            "type": "application/astra-setting",
            "version": "1.1.",
            "desiredConfig": {
                "connectionHost": host,
                "credentialId": credentialID,
                "groupBaseDN": groupBaseDN,
                "isEnabled": "true",
                "loginAttribute": userLoginAttribute,
                "port": port,
                "secureMode": "LDAPS" if secureMode else "LDAP",
                "userBaseDN": userBaseDN,
                "userSearchFilter": userSearchFilter,
                "vendor": "Active Directory",
            },
        }
        if groupSearchFilter:
            data["desiredConfig"]["groupSearchCustomFilter"] = groupSearchFilter

        ret = super().apicall(
            "put",
            url,
            data,
            self.headers,
            params,
            self.verifySSL,
            quiet=self.quiet,
            verbose=self.verbose,
        )
        if ret.ok:
            # the settings/ endpoint doesn't return a dict for PUTs, so calling getSettings
            results = next(x for x in getSettings().main()["items"] if x["id"] == settingID)
            if not self.quiet:
                print(json.dumps(results))
            return results
        else:
            print(ret.text)
            print(ret.reason)
            return False
