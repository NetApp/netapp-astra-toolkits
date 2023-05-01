#!/usr/bin/env python3
"""
   Copyright 2023 NetApp, Inc

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


class ArgparseChoicesLists:
    """This Class defines a set of Lists which are used in the "choices" section
    of the Argparse parser. An empty list is perfectly valid, so all possible
    lists are pre-defined. These lists are added to by toolkit.py, and then used
    in tkSrc/parser.py"""

    def __init__(self):
        resources = {
            "apps": [],
            "backups": [],
            "buckets": [],
            "charts": [],
            "clouds": [],
            "clusters": [],
            "credentials": [],
            "destClusters": [],
            "hooks": [],
            "labels": [],
            "namespaces": [],
            "protections": [],
            "replications": [],
            "scripts": [],
            "snapshots": [],
            "storageClasses": [],
            "users": [],
        }
        for key in resources:
            setattr(self, key, resources[key])


class AstraResourceDicts:
    """This Class defines a set of astraSDK resource Dictionaries. In the sys.argv
    inspection that happens in toolkit.py, many astraSDK "get" methods are called
    to generate various argparse options. Later when an actual action is carried out
    within tkSrc/callers.py, we do not want to have to make the same API call again,
    so an instantiation of this class is used to pass the data."""

    def __init__(self):
        pass

    def needsattr(self, name):
        if not getattr(self, name, False):
            return True

    def buildList(self, name, key, fKey=None, fVal=None):
        """Generates a list for use in argparse choices"""
        try:
            # return a list of resource values based on 'key'
            if not fKey or not fVal:
                return [x[key] for x in getattr(self, name)["items"]]
            # return a list of resource values based on 'key' only if some other 'fKey' == 'fVal'
            return [x[key] for x in (y for y in getattr(self, name)["items"] if y[fKey] == fVal)]
        except TypeError:
            return []
