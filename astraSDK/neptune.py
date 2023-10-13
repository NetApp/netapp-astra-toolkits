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

import copy
import json
import kubernetes
import yaml


class getResources:
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def recursiveGet(self, k, item):
        """Recursion function which is just a wrapper around dict.get(key), to handle cases
        where there's a dict within a dict. A '.' in the key name ('metadata.name')
        is used for identification purposes."""
        if len(k.split(".")) > 1:
            return self.recursiveGet(k.split(".", 1)[1], item[k.split(".")[0]])
        else:
            return item.get(k)

    def main(
        self,
        plural,
        version="v1alpha1",
        group="management.astra.netapp.io",
        keyFilter=None,
        valFilter=None,
    ):
        kubernetes.config.load_kube_config()
        resp = kubernetes.client.CustomObjectsApi().list_cluster_custom_object(
            group=group,
            version=version,
            plural=plural,
        )

        if keyFilter and valFilter:
            filterCopy = copy.deepcopy(resp)
            for counter, r in enumerate(filterCopy.get("items")):
                if self.recursiveGet(keyFilter, r) != valFilter:
                    resp["items"].remove(filterCopy["items"][counter])

        if self.output == "yaml":
            resp = yaml.dump(resp)

        if not self.quiet:
            print(json.dumps(resp) if type(resp) is dict else resp)
        return resp


class getNamespaces:
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(self):
        kubernetes.config.load_kube_config()
        resp = kubernetes.client.CoreV1Api().list_namespace().to_dict()

        systemNS = [
            "astra-connector-operator",
            "kube-node-lease",
            "kube-public",
            "kube-system",
            "neptune-system",
            "trident",
        ]
        namespaces = copy.deepcopy(resp)
        for counter, ns in enumerate(resp.get("items")):
            if ns.get("metadata").get("name") in systemNS:
                namespaces["items"].remove(resp["items"][counter])

        if self.output == "yaml":
            namespaces = yaml.dump(namespaces)

        if not self.quiet:
            print(json.dumps(namespaces) if type(namespaces) is dict else namespaces)
        return namespaces
