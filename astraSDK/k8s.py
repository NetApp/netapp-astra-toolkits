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

import base64
import copy
import json
import kubernetes
import yaml

from .common import KubeCommon, SDKCommon


class getClusterResources(KubeCommon):
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
        version="v1",
        group="trident.netapp.io",
        keyFilter=None,
        valFilter=None,
    ):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
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


class updateResource(KubeCommon):
    def __init__(self, quiet=True):
        """quiet: Will there be CLI output or just return (datastructure)"""
        self.quiet = quiet
        super().__init__()

    def main(
        self,
        plural,
        name,
        body,
        version="v1",
        group="trident.netapp.io",
    ):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            try:
                resp = api_instance.patch_cluster_custom_object(group, version, plural, name, body)

                if not self.quiet:
                    print(json.dumps(resp) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class getNamespaces(KubeCommon):
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(self):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
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
                    print(json.dumps(resp, default=str) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class getSecrets(KubeCommon):
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(self, namespace="trident"):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.list_namespaced_secret(namespace).to_dict()

                if self.output == "yaml":
                    resp = yaml.dump(resp)

                if not self.quiet:
                    print(json.dumps(resp, default=str) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class createRegCred(KubeCommon, SDKCommon):
    def __init__(self, quiet=True):
        """quiet: Will there be CLI output or just return (datastructure)"""
        self.quiet = quiet
        super().__init__()

    def main(self, name=None, registry=None, username=None, password=None, namespace="trident"):
        if (not username and password) or (username and not password):
            raise SystemExit(
                "Either both or neither of (username and password) should be specified"
            )
        if not registry:
            registry = f"cr.{self.conf['domain']}"
        if not username and not password:
            username = self.conf["account_id"]
            password = self.conf["headers"].get("Authorization").split(" ")[-1]

        regCred = {
            "auths": {
                registry: {
                    "username": username,
                    "password": password,
                    "auth": base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
                        "utf-8"
                    ),
                }
            }
        }
        regCredSecret = kubernetes.client.V1Secret(
            metadata=(
                kubernetes.client.V1ObjectMeta(name=name)
                if name
                else kubernetes.client.V1ObjectMeta(
                    generate_name="-".join(registry.split(".")) + "-"
                )
            ),
            type="kubernetes.io/dockerconfigjson",
            data={
                ".dockerconfigjson": base64.b64encode(json.dumps(regCred).encode("utf-8")).decode(
                    "utf-8"
                )
            },
        )

        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.create_namespaced_secret(
                    namespace=namespace,
                    body=regCredSecret,
                ).to_dict()
                if not self.quiet:
                    print(json.dumps(resp, default=str) if type(resp) is dict else resp)
                return resp
            except kubernetes.client.rest.ApiException as e:
                self.printError(e)
