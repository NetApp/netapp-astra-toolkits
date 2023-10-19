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

from .common import NeptuneCommon


class getResources(NeptuneCommon):
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(
        self,
        plural,
        version="v1alpha1",
        group="management.astra.netapp.io",
        keyFilter=None,
        valFilter=None,
    ):
        with kubernetes.client.ApiClient(self.configuration) as api_client:
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            try:
                resp = api_instance.list_cluster_custom_object(
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

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)
                raise SystemExit(e)


class getNamespaces(NeptuneCommon):
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(self):
        with kubernetes.client.ApiClient(self.configuration) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.list_namespace().to_dict()
                systemNS = [
                    "astra-connector-operator",
                    "kube-node-lease",
                    "kube-public",
                    "kube-system",
                    "neptune-system",
                    "trident",
                ]
                namespaces = copy.deepcopy(resp)
                for counter, ns in enumerate(namespaces.get("items")):
                    if ns.get("metadata").get("name") in systemNS:
                        resp["items"].remove(namespaces["items"][counter])

                if self.output == "yaml":
                    resp = yaml.dump(resp)

                if not self.quiet:
                    print(json.dumps(resp) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)
                raise SystemExit(e)


class getSecrets(NeptuneCommon):
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(self, namespace="neptune-system"):
        with kubernetes.client.ApiClient(self.configuration) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.list_namespaced_secret(namespace).to_dict()

                if self.output == "yaml":
                    resp = yaml.dump(resp)

                if not self.quiet:
                    print(json.dumps(resp) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)
                raise SystemExit(e)
