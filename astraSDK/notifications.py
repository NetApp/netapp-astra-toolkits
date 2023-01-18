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
from datetime import datetime, timedelta

from .common import SDKCommon


class getNotifications(SDKCommon):
    """Get all of the notifications in Astra Control"""

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

    def main(self, limit=None, skip=None, minuteFilter=None, severityFilter=None):

        endpoint = "core/v1/notifications"
        url = self.base + endpoint

        data = {}
        params = {"orderBy": "eventTime desc", "count": "true"}
        if limit and int(limit) != 0:
            params["limit"] = limit
        if skip:
            params["skip"] = skip

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
            notifications = super().jsonifyResults(ret)
            notificationsCooked = copy.deepcopy(notifications)
            for counter, notification in enumerate(notifications.get("items")):
                if minuteFilter and (
                    datetime.utcnow()
                    - datetime.strptime(notification.get("eventTime"), "%Y-%m-%dT%H:%M:%SZ")
                    > timedelta(minutes=minuteFilter)
                ):
                    notificationsCooked["items"].remove(notifications["items"][counter])
                elif severityFilter and severityFilter != notification.get("severity"):
                    notificationsCooked["items"].remove(notifications["items"][counter])

            if self.output == "json":
                dataReturn = notificationsCooked
            elif self.output == "yaml":
                dataReturn = yaml.dump(notificationsCooked)
            elif self.output == "table":
                dataReturn = self.basicTable(
                    ["notificationID", "summary", "severity", "eventTime"],
                    ["id", "summary", "severity", "eventTime"],
                    notificationsCooked,
                ) + colored(
                    f"\npre-filtered count: {notificationsCooked['metadata']['count']}", "yellow"
                )
            if not self.quiet:
                print(json.dumps(dataReturn) if type(dataReturn) is dict else dataReturn)
            return dataReturn

        else:
            return False
