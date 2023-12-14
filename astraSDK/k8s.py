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


class getResources(KubeCommon):
    """Get all namespace scoped resources of a specific CRD"""

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
        namespace="neptune-system",
        version="v1alpha1",
        group="management.astra.netapp.io",
        keyFilter=None,
        valFilter=None,
    ):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            try:
                resp = api_instance.list_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
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


class getClusterResources(KubeCommon):
    """Get all cluster scoped resources of a specific CRD"""

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


class createResource(KubeCommon):
    """Creates a cluster scoped Custom Resource"""

    def __init__(self, quiet=True, dry_run=False):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource"""
        self.quiet = quiet
        self.dry_run = dry_run
        super().__init__()

    def main(
        self,
        plural,
        namespace,
        body,
        version="v1alpha1",
        group="management.astra.netapp.io",
    ):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            try:
                resp = api_instance.create_namespaced_custom_object(
                    group,
                    version,
                    namespace,
                    plural,
                    body,
                    dry_run=("All" if self.dry_run else None),
                )

                if not self.quiet:
                    print(json.dumps(resp) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class destroyResource(KubeCommon):
    """Destroys a cluster scoped Custom Resource"""

    def __init__(self, quiet=True, dry_run=False):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource"""
        self.quiet = quiet
        self.dry_run = dry_run
        super().__init__()

    def main(
        self,
        plural,
        name,
        namespace="neptune-system",
        version="v1alpha1",
        group="management.astra.netapp.io",
    ):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CustomObjectsApi(api_client)
            try:
                resp = api_instance.delete_namespaced_custom_object(
                    group,
                    version,
                    namespace,
                    plural,
                    name,
                    dry_run=("All" if self.dry_run else None),
                )

                if not self.quiet:
                    print(json.dumps(resp) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class updateClusterResource(KubeCommon):
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

    def main(self, systemNS=None):
        """Default behavior (systemNS=None) is to remove typical system namespaces from the
        response. However for certain workflows, you may want to return ALL namespaces (pass an
        empty list: systemNS=[]), or remove a custom list (systemNS=["ns1-to-ignore",
        "ns2-to-ignore", "ns3-to-ignore"])."""
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.list_namespace().to_dict()
                if type(systemNS) is not list:
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
    """Gets all kubernetes secrets in a specific namespace"""

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


class destroySecret(KubeCommon):
    """Destroys a kubernetes secret in a specific namespace"""

    def __init__(self, quiet=True, dry_run=False):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource"""
        self.quiet = quiet
        self.dry_run = dry_run
        super().__init__()

    def main(self, name, namespace="neptune-system"):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.delete_namespaced_secret(
                    name,
                    namespace,
                    dry_run=("All" if self.dry_run else None),
                ).to_dict()
                if not self.quiet:
                    print(json.dumps(resp) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class getStorageClasses(KubeCommon):
    def __init__(self, quiet=True, output="json"):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml"""
        self.quiet = quiet
        self.output = output
        super().__init__()

    def main(self):
        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.StorageV1Api(api_client)
            try:
                resp = api_instance.list_storage_class().to_dict()

                if self.output == "yaml":
                    resp = yaml.dump(resp)

                if not self.quiet:
                    print(json.dumps(resp, default=str) if type(resp) is dict else resp)
                return resp

            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class createRegCred(KubeCommon, SDKCommon):
    """Creates a docker registry credential. By default it uses fields from config.yaml,
    however any of these fields can be overridden by custom values."""

    def __init__(self, quiet=True, dry_run=False):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource"""
        self.quiet = quiet
        self.dry_run = dry_run
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
                    dry_run=("All" if self.dry_run else None),
                ).to_dict()
                if not self.quiet:
                    print(json.dumps(resp, default=str) if type(resp) is dict else resp)
                return resp
            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class createAstraApiToken(KubeCommon, SDKCommon):
    """Creates an astra-api-token secret based on the contents of config.yaml"""

    def __init__(self, quiet=True, dry_run=False):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource"""
        self.quiet = quiet
        self.dry_run = dry_run
        super().__init__()

    def main(self, name=None, namespace="neptune-system"):
        token = self.conf["headers"].get("Authorization").split(" ")[-1]
        secret = kubernetes.client.V1Secret(
            metadata=(
                kubernetes.client.V1ObjectMeta(name=name)
                if name
                else kubernetes.client.V1ObjectMeta(generate_name="astra-api-token-")
            ),
            type="Opaque",
            data={"apiToken": base64.b64encode(token.encode("utf-8")).decode("utf-8")},
        )

        with kubernetes.client.ApiClient(self.kube_config) as api_client:
            api_instance = kubernetes.client.CoreV1Api(api_client)
            try:
                resp = api_instance.create_namespaced_secret(
                    namespace=namespace,
                    body=secret,
                    dry_run=("All" if self.dry_run else None),
                ).to_dict()
                if not self.quiet:
                    print(json.dumps(resp, default=str) if type(resp) is dict else resp)
                return resp
            except kubernetes.client.rest.ApiException as e:
                self.printError(e)


class createAstraConnector(SDKCommon):
    """Creates an AstraConnector custom resource"""

    def __init__(self, quiet=True, dry_run=False):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource"""
        self.quiet = quiet
        self.dry_run = dry_run
        super().__init__()

    def main(
        self,
        clusterName,
        cloudID,
        apiToken,
        regCred,
        registry=None,
        name="astra-connector",
        namespace="neptune-system",
    ):
        body = {
            "apiVersion": "astra.netapp.io/v1",
            "kind": "AstraConnector",
            "metadata": {"name": name, "namespace": namespace},
            "spec": {
                "astra": {
                    "accountId": self.conf["account_id"],
                    "cloudId": cloudID,
                    "clusterName": clusterName,
                    "skipTLSValidation": not self.conf["verifySSL"],
                    "tokenRef": apiToken,
                },
                "natsSyncClient": {"cloudBridgeURL": f"https://{self.conf['domain']}"},
                "imageRegistry": {
                    "name": registry if registry else f"cr.{self.conf['domain']}",
                    "secret": regCred,
                },
            },
        }
        return createResource(quiet=self.quiet, dry_run=self.dry_run).main(
            body["kind"].lower() + "s",
            namespace,
            body,
            version=body["apiVersion"].split("/")[1],
            group=body["apiVersion"].split("/")[0],
        )
