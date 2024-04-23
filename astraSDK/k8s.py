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

import base64
import copy
import json
import kubernetes
import sys
import urllib3
import yaml
from datetime import datetime, timedelta, timezone

from .common import BaseCommon, KubeCommon, SDKCommon


class getResources(KubeCommon):
    """Get all namespace scoped resources of a specific CRD"""

    def __init__(
        self, quiet=True, output="json", verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.output = output
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(
        self,
        plural,
        namespace="astra-connector",
        version="v1",
        group="astra.netapp.io",
        filters=None,
    ):
        """filters must be of format (logical AND if specifying multiple filters, set
        inMatch to True to use "in" comparison instead of "=="): [
          {"keyFilter": "keyname1", "valFilter": "value1", inMatch=True},
          {"keyFilter": "keyname2", "valFilter": "value2"}
        ]"""
        api_instance = kubernetes.client.CustomObjectsApi(self.api_client)
        try:
            if self.verbose:
                self.verbose_log = self.WriteVerbose()
                sys.stdout = self.verbose_log
            resp = api_instance.list_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
            )
            if isinstance(filters, list):
                for f in filters:
                    filterCopy = copy.deepcopy(resp)
                    if f["keyFilter"] and f["valFilter"]:
                        for counter, r in enumerate(filterCopy.get("items")):
                            if f.get("inMatch"):
                                if f["valFilter"] not in self.recursiveGet(f["keyFilter"], r):
                                    resp["items"].remove(filterCopy["items"][counter])
                            else:
                                if self.recursiveGet(f["keyFilter"], r) != f["valFilter"]:
                                    resp["items"].remove(filterCopy["items"][counter])
            self.formatPrint(resp, plural)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            if hasattr(e, "status") and e.status == 404 and e.reason == "Not Found":
                self.notInstalled(f"/apis/{group}/{version}/namespaces/{namespace}/{plural}")
            self.printKubeError(e)

    def formatPrint(self, resp, plural, quiet=None, output=None, verbose=None):
        if quiet is None:
            quiet = self.quiet
        if output is None:
            output = self.output
        if verbose is None:
            verbose = self.verbose
        if output == "yaml":
            resp = yaml.dump(resp).rstrip()
        elif output == "table":
            resp = self.basicTable(
                self.getTableInfo(plural, headers=True),
                self.getTableInfo(plural),
                resp,
                tablefmt="grid",
            )
        if verbose:
            print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
            sys.stdout = sys.__stdout__
            self.verbose_log.print()
        if not quiet:
            print(json.dumps(resp) if type(resp) is dict else resp)

    def getTableInfo(self, plural, headers=False):
        if plural == "applications":
            if headers:
                return ["name", "namespaces", "labelSelectors", "state"]
            return [
                "metadata.name",
                "spec.includedNamespaces[].namespace",
                "spec.includedNamespaces[].labelSelector.matchLabels",
                "status.conditions[].type",
            ]
        elif plural == "appvaults":
            if headers:
                return ["name", "credential", "provider", "state"]
            return [
                "metadata.name",
                "spec.providerCredentials.*.valueFromSecret.name",
                "spec.providerType",
                "status.state",
            ]
        elif plural == "astraconnectors":
            if headers:
                return [
                    "astraControlInstance",
                    "registered",
                    "astraClusterID",
                    "astraConnectorID",
                    "status",
                ]
            return [
                "spec.natsSyncClient.cloudBridgeURL",
                "status.natsSyncClient.registered",
                "status.natsSyncClient.astraClusterID",
                "status.natsSyncClient.astraConnectorID",
                "status.natsSyncClient.status",
            ]
        elif plural == "backups":
            if headers:
                return [
                    "applicationRef",
                    "backupName",
                    "appVaultRef",
                    "backupState",
                    "creationTimestamp",
                ]
            return [
                "spec.applicationRef",
                "metadata.name",
                "spec.appVaultRef",
                "status.state",
                "metadata.creationTimestamp",
            ]
        elif plural == "exechooks":
            if headers:
                return [
                    "applicationRef",
                    "name",
                    "stage",
                    "action",
                    "arguments",
                    "matchingCriteriaType",
                    "matchingCriteriaValue",
                ]
            return [
                "spec.applicationRef",
                "metadata.name",
                "spec.stage",
                "spec.action",
                "spec.arguments",
                "spec.matchingCriteria[].type",
                "spec.matchingCriteria[].value",
            ]
        elif plural == "exechooksruns":
            if headers:
                return [
                    "applicationRef",
                    "name",
                    "state",
                    "matchingPods",
                    "creationTimestamp",
                ]
            return [
                "spec.applicationRef",
                "metadata.name",
                "status.state",
                "status.matchingContainers[].podName",
                "metadata.creationTimestamp",
            ]
        elif plural == "inplacerestores":
            if headers:
                return ["name", "applicationRef", "state", "creationTimestamp"]
            return [
                "metadata.name",
                "metadata.app.metadata.name",
                "status.state",
                "metadata.creationTimestamp",
            ]
        elif plural == "restores":
            if headers:
                return [
                    "name",
                    "sourceNamespace",
                    "destinationNamespace",
                    "state",
                    "creationTimestamp",
                ]
            return [
                "metadata.name",
                "spec.namespaceMapping[].source",
                "spec.namespaceMapping[].destination",
                "status.state",
                "metadata.creationTimestamp",
            ]
        elif plural == "schedules":
            if headers:
                return [
                    "applicationRef",
                    "name",
                    "granularity",
                    "minute",
                    "hour",
                    "dayOfWeek",
                    "dayOfMonth",
                    "snapRetention",
                    "backupRetention",
                    "appVaultRef",
                ]
            return [
                "spec.applicationRef",
                "metadata.name",
                "spec.granularity",
                "spec.minute",
                "spec.hour",
                "spec.dayOfWeek",
                "spec.dayOfMonth",
                "spec.snapshotRetention",
                "spec.backupRetention",
                "spec.appVaultRef",
            ]
        elif plural == "snapshots":
            if headers:
                return [
                    "applicationRef",
                    "snapshotName",
                    "appVaultRef",
                    "snapshotState",
                    "creationTimestamp",
                ]
            return [
                "spec.applicationRef",
                "metadata.name",
                "spec.appVaultRef",
                "status.state",
                "metadata.creationTimestamp",
            ]


class getClusterResources(KubeCommon):
    """Get all cluster scoped resources of a specific CRD"""

    def __init__(
        self, quiet=True, output="json", verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.output = output
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(
        self,
        plural,
        version="v1",
        group="trident.netapp.io",
        keyFilter=None,
        valFilter=None,
    ):
        api_instance = kubernetes.client.CustomObjectsApi(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
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

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            if hasattr(e, "status") and e.status == 404 and e.reason == "Not Found":
                self.notInstalled(f"/apis/{group}/{version}/{plural}")
            self.printKubeError(e)


class createResource(KubeCommon):
    """Creates a namespace scoped Custom Resource"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(
        self,
        plural,
        namespace,
        body,
        version="v1",
        group="astra.netapp.io",
    ):
        api_instance = kubernetes.client.CustomObjectsApi(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.create_namespaced_custom_object(
                group,
                version,
                namespace,
                plural,
                body,
                dry_run=("All" if self.dry_run else None),
            )

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            if hasattr(e, "status") and e.status == 404 and e.reason == "Not Found":
                self.notInstalled(f"/apis/{group}/{version}/namespaces/{namespace}/{plural}")
            self.printKubeError(e)


class destroyResource(KubeCommon):
    """Destroys a namespace scoped Custom Resource"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(
        self,
        plural,
        name,
        namespace="astra-connector",
        version="v1",
        group="astra.netapp.io",
    ):
        api_instance = kubernetes.client.CustomObjectsApi(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.delete_namespaced_custom_object(
                group,
                version,
                namespace,
                plural,
                name,
                dry_run=("All" if self.dry_run else None),
            )

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            if hasattr(e, "status") and e.status == 404 and e.reason == "Not Found":
                self.notInstalled(f"/apis/{group}/{version}/namespaces/{namespace}/{plural}")
            self.printKubeError(e)


class updateClusterResource(KubeCommon):
    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(
        self,
        plural,
        name,
        body,
        version="v1",
        group="trident.netapp.io",
    ):
        api_instance = kubernetes.client.CustomObjectsApi(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.patch_cluster_custom_object(
                group, version, plural, name, body, dry_run=("All" if self.dry_run else None)
            )

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            if hasattr(e, "status") and e.status == 404 and e.reason == "Not Found":
                self.notInstalled(f"/apis/{group}/{version}/{plural}")
            self.printKubeError(e)


class getNamespaces(KubeCommon):
    def __init__(
        self, quiet=True, output="json", verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.output = output
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(self, systemNS=None, nameFilter=None, unassociated=False, minuteFilter=False):
        """Default behavior (systemNS=None) is to remove typical system namespaces from the
        response. However for certain workflows, you may want to return ALL namespaces (pass an
        empty list: systemNS=[]), or remove a custom list (systemNS=["ns1-to-ignore",
        "ns2-to-ignore", "ns3-to-ignore"]).
        nameFilter: partial match against metadata.name
        unassociated: only return namespaces which do not contain the "managed-by-astra-application"
                      annotation
        minuteFilter: only return namespaces created within the last X minutes"""
        api_instance = kubernetes.client.CoreV1Api(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.list_namespace().to_dict()
            if type(systemNS) is not list:
                systemNS = [
                    "astra-connector-operator",
                    "astra-connector",
                    "kube-node-lease",
                    "kube-public",
                    "kube-system",
                    "trident",
                ]
            namespaces = copy.deepcopy(resp)
            for counter, ns in enumerate(namespaces.get("items")):
                if ns.get("metadata").get("name") in systemNS:
                    resp["items"].remove(namespaces["items"][counter])
                elif nameFilter and nameFilter not in ns["metadata"].get("name"):
                    resp["items"].remove(namespaces["items"][counter])
                elif (
                    unassociated
                    and "managed-by-astra-application" in ns["metadata"].get("annotations").keys()
                ):
                    resp["items"].remove(namespaces["items"][counter])
                elif minuteFilter and (
                    datetime.now(timezone.utc) - ns["metadata"].get("creation_timestamp")
                    > timedelta(minutes=minuteFilter)
                ):
                    resp["items"].remove(namespaces["items"][counter])

            if self.output == "yaml":
                resp = yaml.dump(resp)
            elif self.output == "table":
                resp = self.basicTable(
                    ["name", "status", "managed-by-astra-application", "creationTimestamp"],
                    [
                        "metadata.name",
                        "status.phase",
                        "metadata.annotations.managed-by-astra-application",
                        "metadata.creation_timestamp",
                    ],
                    resp,
                    tablefmt="grid",
                )

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp, default=str) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            self.printKubeError(e)


class getSecrets(KubeCommon):
    """Gets all kubernetes secrets in a specific namespace"""

    def __init__(
        self, quiet=True, output="json", verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        output: table: pretty print the data
                json: (default) output in JSON
                yaml: output in yaml
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.output = output
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(self, namespace="astra-connector"):
        api_instance = kubernetes.client.CoreV1Api(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.list_namespaced_secret(namespace).to_dict()

            if self.output == "yaml":
                resp = yaml.dump(resp)
            elif self.output == "table":
                resp = self.basicTable(
                    ["name", "type", "dataKeys", "creationTimestamp"],
                    ["metadata.name", "type", "data.KEYS", "metadata.creation_timestamp"],
                    resp,
                    tablefmt="grid",
                )

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp, default=str) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            self.printKubeError(e)


class destroySecret(KubeCommon):
    """Destroys a kubernetes secret in a specific namespace"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(self, name, namespace="astra-connector"):
        api_instance = kubernetes.client.CoreV1Api(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.delete_namespaced_secret(
                name,
                namespace,
                dry_run=("All" if self.dry_run else None),
            ).to_dict()

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            self.printKubeError(e)


class getStorageClasses(KubeCommon):
    def __init__(
        self, quiet=True, output="json", verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        output: json: (default) output in JSON
                yaml: output in yaml
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.output = output
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(self):
        api_instance = kubernetes.client.StorageV1Api(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.list_storage_class().to_dict()

            if self.output == "yaml":
                resp = yaml.dump(resp)

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp, default=str) if type(resp) is dict else resp)
            return resp

        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            self.printKubeError(e)


class createV1Secret(KubeCommon):
    """Creates a Kubernetes V1 Secret"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.skip_tls_verify = skip_tls_verify
        self.conf = kubernetes.client.Configuration()
        self.conf.debug = self.verbose
        self.conf.verify_ssl = not self.skip_tls_verify
        super().__init__(config_context=config_context, client_configuration=self.conf)

    def main(self, v1SecretObj, namespace="astra-connector"):
        api_instance = kubernetes.client.CoreV1Api(self.api_client)
        try:
            if self.verbose:
                verbose_log = self.WriteVerbose()
                sys.stdout = verbose_log
            resp = api_instance.create_namespaced_secret(
                namespace=namespace,
                body=v1SecretObj,
                dry_run=("All" if self.dry_run else None),
            ).to_dict()

            if self.verbose:
                print(f"verify_ssl: {self.api_client.configuration.verify_ssl}")
                sys.stdout = sys.__stdout__
                verbose_log.print()
            if not self.quiet:
                print(json.dumps(resp, default=str) if type(resp) is dict else resp)
            return resp
        except (kubernetes.client.rest.ApiException, urllib3.exceptions.MaxRetryError) as e:
            sys.stdout = sys.__stdout__
            self.printKubeError(e)


class createRegCred(KubeCommon, SDKCommon):
    """Creates a docker registry credential. By default it uses fields from config.yaml,
    however any of these fields can be overridden by custom values."""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.config_context = config_context
        self.skip_tls_verify = skip_tls_verify
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
        return createV1Secret(
            quiet=self.quiet,
            dry_run=self.dry_run,
            verbose=self.verbose,
            config_context=self.config_context,
            skip_tls_verify=self.skip_tls_verify,
        ).main(regCredSecret, namespace=namespace)


class createAstraApiToken(KubeCommon, SDKCommon):
    """Creates an astra-api-token secret based on the contents of config.yaml"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.config_context = config_context
        self.skip_tls_verify = skip_tls_verify
        super().__init__()

    def main(self, name=None, namespace="astra-connector"):
        # Handle case sensitivity
        authorization = (
            self.conf["headers"].get("Authorization")
            if self.conf["headers"].get("Authorization")
            else self.conf["headers"].get("authorization")
        )
        token = authorization.split(" ")[-1]
        secret = kubernetes.client.V1Secret(
            metadata=(
                kubernetes.client.V1ObjectMeta(name=name)
                if name
                else kubernetes.client.V1ObjectMeta(generate_name="astra-api-token-")
            ),
            type="Opaque",
            data={"apiToken": base64.b64encode(token.encode("utf-8")).decode("utf-8")},
        )
        return createV1Secret(
            quiet=self.quiet,
            dry_run=self.dry_run,
            verbose=self.verbose,
            config_context=self.config_context,
            skip_tls_verify=self.skip_tls_verify,
        ).main(secret, namespace=namespace)


class createGenericSecret(KubeCommon):
    """Creates a basic Kubernetes secret, the passed data must already be base64 encoded"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.config_context = config_context
        self.skip_tls_verify = skip_tls_verify
        super().__init__()

    def main(self, name, data, generateName=False, namespace="astra-connector"):
        secret = kubernetes.client.V1Secret(
            metadata=(
                kubernetes.client.V1ObjectMeta(generate_name=name)
                if generateName
                else kubernetes.client.V1ObjectMeta(name=name)
            ),
            type="Opaque",
            data=data,
        )
        return createV1Secret(
            quiet=self.quiet,
            dry_run=self.dry_run,
            verbose=self.verbose,
            config_context=self.config_context,
            skip_tls_verify=self.skip_tls_verify,
        ).main(secret, namespace=namespace)


class createAstraConnector(SDKCommon):
    """Creates an AstraConnector custom resource"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.config_context = config_context
        self.skip_tls_verify = skip_tls_verify
        super().__init__()

    def main(
        self,
        clusterName,
        cloudID,
        apiToken,
        regCred,
        registry=None,
        name="astra-connector",
        namespace="astra-connector",
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
        return createResource(
            quiet=self.quiet,
            dry_run=self.dry_run,
            verbose=self.verbose,
            config_context=self.config_context,
            skip_tls_verify=self.skip_tls_verify,
        ).main(
            body["kind"].lower() + "s",
            namespace,
            body,
            version=body["apiVersion"].split("/")[1],
            group=body["apiVersion"].split("/")[0],
        )


class createHeadlessConnector(BaseCommon):
    """Creates an AstraConnector custom resource without registering to Astra Control"""

    def __init__(
        self, quiet=True, dry_run=False, verbose=False, config_context=None, skip_tls_verify=False
    ):
        """quiet: Will there be CLI output or just return (datastructure)
        dry-run: False (default):       submit and persist the resource
                 True or non-empty str: submit request without persisting the resource
        verbose: Print all of the rest call info: URL, Method, Headers, Request Body
        config_context: the kubeconfig:context mapping to execute against
                        None: use system defaults
                        str "None:<context>": use default kubeconfig w/ specified context
                        str "<config_file>:<context>": use specified file and context
        skip_tls_verify: Whether to skip TLS/SSL verification"""
        self.quiet = quiet
        self.dry_run = dry_run
        self.verbose = verbose
        self.config_context = config_context
        self.skip_tls_verify = skip_tls_verify
        super().__init__()

    def main(
        self, clusterName, regCred, registry, name="astra-connector", namespace="astra-connector"
    ):
        body = {
            "apiVersion": "astra.netapp.io/v1",
            "kind": "AstraConnector",
            "metadata": {"name": name, "namespace": namespace},
            "spec": {
                "astra": {"clusterName": clusterName},
                "natsSyncClient": {"cloudBridgeURL": "127.0.0.1"},
                "imageRegistry": {"name": registry, "secret": regCred},
            },
        }
        return createResource(
            quiet=self.quiet,
            dry_run=self.dry_run,
            verbose=self.verbose,
            config_context=self.config_context,
            skip_tls_verify=self.skip_tls_verify,
        ).main(
            body["kind"].lower() + "s",
            namespace,
            body,
            version=body["apiVersion"].split("/")[1],
            group=body["apiVersion"].split("/")[0],
        )
