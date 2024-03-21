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

import astraSDK
from tkSrc import create, helpers


def manageV3App(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    appName,
    namespace,
    labelSelectors=None,
    additionalNamespace=None,
    clusterScopedResource=None,
):
    """Manage an application via a Kubernetes custom resource"""
    template = helpers.setupJinja("app")
    v3_dict = yaml.safe_load(
        template.render(
            appName=helpers.isRFC1123(appName),
            namespace=namespace,
            labelSelectors=(
                f"{labelSelectors.split('=')[0]}: {labelSelectors.split('=')[1]}"
                if labelSelectors
                else None
            ),
            addNamespaces=helpers.prependDump(additionalNamespace, prepend=4),
            clusterScopedResources=helpers.prependDump(clusterScopedResource, prepend=4),
        ),
    )
    if dry_run == "client":
        print(yaml.dump(v3_dict).rstrip("\n"))
    else:
        astraSDK.k8s.createResource(
            quiet=quiet,
            dry_run=dry_run,
            verbose=verbose,
            config_context=v3,
            skip_tls_verify=skip_tls_verify,
        ).main(
            f"{v3_dict['kind'].lower()}s",
            v3_dict["metadata"]["namespace"],
            v3_dict,
            version="v1",
            group="astra.netapp.io",
        )


def manageBucket(provider, bucketName, storageAccount, serverURL, credential, quiet, verbose):
    """Manage a bucket via an API call"""
    if provider == "azure":
        bucketParameters = {"azure": {"bucketName": bucketName, "storageAccount": storageAccount}}
    elif provider == "gcp":
        bucketParameters = {"gcp": {"bucketName": bucketName}}
    else:
        bucketParameters = {"s3": {"bucketName": bucketName, "serverURL": serverURL}}
    # Call manageBucket class
    rc = astraSDK.buckets.manageBucket(quiet=quiet, verbose=verbose).main(
        bucketName, credential, provider, bucketParameters
    )
    if rc:
        return rc
    raise SystemExit("astraSDK.buckets.manageBucket() failed")


def manageV3Bucket(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    bucketName,
    provider,
    storageAccount,
    serverURL,
    http,
    skipCertValidation,
    credential,
    ard,
    parser,
):
    """Manage a bucket via a Kubernetes custom resource"""
    # Create providerCredentials based on provider input
    if provider == "azure":
        keyNameList = ["accountKey"]
    elif provider == "gcp":
        keyNameList = ["credentials"]
    else:
        keyNameList = ["accessKeyID", "secretAccessKey"]
    template = helpers.setupJinja("appVault")
    v3_dict = yaml.safe_load(
        template.render(
            bucketName=helpers.isRFC1123(bucketName, parser=parser),
            providerType=provider,
            accountName=storageAccount,
            endpoint=serverURL,
            secure=("false" if http else None),
            skipCertValidation=("true" if skipCertValidation else None),
            providerCredentials=helpers.prependDump(
                helpers.createSecretKeyDict(keyNameList, credential, provider, ard, parser),
                prepend=4,
            ),
        )
    )
    if dry_run == "client":
        print(yaml.dump(v3_dict).rstrip("\n"))
    else:
        astraSDK.k8s.createResource(
            quiet=quiet,
            dry_run=dry_run,
            verbose=verbose,
            config_context=v3,
            skip_tls_verify=skip_tls_verify,
        ).main(
            f"{v3_dict['kind'].lower()}s",
            v3_dict["metadata"]["namespace"],
            v3_dict,
            version="v1",
            group="astra.netapp.io",
        )


def manageV3Cluster(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    clusterName,
    operator_version,
    regCred,
    registry,
    cloudID,
    headless,
    ard,
    parser,
):
    helpers.isRFC1123(clusterName, parser=parser)
    create.createV3ConnectorOperator(v3, dry_run, skip_tls_verify, verbose, operator_version)
    # Create the astra API token secret
    if not headless:
        apiToken = astraSDK.k8s.createAstraApiToken(
            quiet=quiet,
            dry_run=dry_run,
            verbose=verbose,
            config_context=v3,
            skip_tls_verify=skip_tls_verify,
        ).main()
    # Handle the registry secret
    if not regCred:
        cred = astraSDK.k8s.createRegCred(
            quiet=quiet,
            dry_run=dry_run,
            verbose=verbose,
            config_context=v3,
            skip_tls_verify=skip_tls_verify,
        ).main(registry=registry, namespace="astra-connector")
        if not cred:
            raise SystemExit("astraSDK.k8s.createRegCred() failed")
        regCred = cred["metadata"]["name"]
    else:
        if ard.needsattr("credentials"):
            ard.credentials = astraSDK.k8s.getSecrets(
                config_context=v3, skip_tls_verify=skip_tls_verify
            ).main()
        cred = ard.getSingleDict("credentials", "metadata.name", regCred, parser)
    # Create the AstraConnector CR
    if headless:
        connector = astraSDK.k8s.createHeadlessConnector(
            quiet=quiet,
            dry_run=dry_run,
            verbose=verbose,
            config_context=v3,
            skip_tls_verify=skip_tls_verify,
        ).main(clusterName, regCred, registry)
    else:
        connector = astraSDK.k8s.createAstraConnector(
            quiet=quiet,
            dry_run=dry_run,
            verbose=verbose,
            config_context=v3,
            skip_tls_verify=skip_tls_verify,
        ).main(clusterName, cloudID, apiToken["metadata"]["name"], regCred, registry=registry)
    if not connector:
        raise SystemExit("astraSDK.k8s.createAstraConnector() failed")


def validateBucketArgs(args, parser):
    """Validate that user provided inputs for managing a bucket are valid"""
    # Validate serverURL and storageAccount args depending upon provider type
    if args.serverURL is None and args.provider in [
        "aws",
        "generic-s3",
        "ontap-s3",
        "storagegrid-s3",
    ]:
        parser.error(f"--serverURL must be provided for '{args.provider}' provider.")
    if args.storageAccount is None and args.provider == "azure":
        parser.error("--storageAccount must be provided for 'azure' provider.")
    # Error if credential was specified with any other argument
    if args.credential is not None:
        if args.json is not None or args.accessKey is not None or args.accessSecret is not None:
            parser.error(
                "if an existing credential is specified, no other credentialGroup arguments "
                "can be specified"
            )
    # Error if json was specified with accessKey/Secret
    elif args.json is not None:
        if args.accessKey is not None or args.accessSecret is not None:
            parser.error(
                "if a public cloud JSON credential file is specified, no other credentialGroup "
                "arguments can be specified"
            )
    # If neither credential or json was specified, make sure both accessKey/Secret were
    elif args.accessKey is None or args.accessSecret is None:
        parser.error(
            "either an (existing credential) OR (public cloud JSON credential) OR "
            "(accessKey AND accessSecret) must be specified"
        )
    # If json was specified, ensure provider is a public cloud
    if args.json is not None and args.provider not in ["aws", "azure", "gcp"]:
        parser.error("--json should only be specified for public cloud providers (aws, azure, gcp)")


def main(args, parser, ard):
    if args.objectType == "app" or args.objectType == "application":
        if args.additionalNamespace:
            args.additionalNamespace = helpers.createNamespaceList(
                args.additionalNamespace, v3=args.v3
            )
        if args.clusterScopedResource:
            if args.v3:
                # Hardcoding the api resources list to not require an API call to AC
                ard.apiresources = {
                    "items": [
                        {
                            "apiVersion": "rbac.authorization.k8s.io/v1",
                            "kind": "ClusterRole",
                        },
                        {
                            "apiVersion": "rbac.authorization.k8s.io/v1",
                            "kind": "ClusterRoleBinding",
                        },
                        {
                            "apiVersion": "apiextensions.k8s.io/v1",
                            "kind": "CustomResource",
                        },
                        {
                            "apiVersion": "apiextensions.k8s.io/v1",
                            "kind": "CustomResourceDefinition",
                        },
                        {
                            "apiVersion": "apiextensions.k8s.io/v1beta1",
                            "kind": "CustomResource",
                        },
                        {
                            "apiVersion": "apiextensions.k8s.io/v1beta1",
                            "kind": "CustomResourceDefinition",
                        },
                        {
                            "apiVersion": "admissionregistration.k8s.io/v1",
                            "kind": "MutatingWebhookConfiguration",
                        },
                        {
                            "apiVersion": "admissionregistration.k8s.io/v1",
                            "kind": "ValidatingWebhookConfiguration",
                        },
                    ]
                }
            else:
                ard.apiresources = astraSDK.apiresources.getApiResources().main(
                    cluster=args.clusterID
                )
            # Validate input as argparse+choices is unable to only validate the first input
            api_res_list = [f"{a['apiVersion']}/{a['kind']}" for a in ard.apiresources["items"]]
            for csr in args.clusterScopedResource:
                if csr[0] not in api_res_list:
                    parser.error(
                        f"argument -c/--clusterScopedResource: invalid choice: '{csr[0]}' "
                        f"(choose from {', '.join(api_res_list)})"
                    )
            args.clusterScopedResource = helpers.createCsrList(
                args.clusterScopedResource, ard.apiresources, v3=args.v3
            )
        if args.v3:
            manageV3App(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                args.appName,
                args.namespace,
                labelSelectors=args.labelSelectors,
                additionalNamespace=args.additionalNamespace,
                clusterScopedResource=args.clusterScopedResource,
            )
        else:
            rc = astraSDK.apps.manageApp(quiet=args.quiet, verbose=args.verbose).main(
                helpers.isRFC1123(args.appName, parser=parser),
                args.namespace,
                args.clusterID,
                args.labelSelectors,
                addNamespaces=args.additionalNamespace,
                clusterScopedResources=args.clusterScopedResource,
            )
            if rc is False:
                raise SystemExit("astraSDK.apps.manageApp() failed")

    elif args.objectType == "bucket" or args.objectType == "appVault":
        validateBucketArgs(args, parser)
        if ard.needsattr("credentials"):
            ard.credentials = astraSDK.k8s.getSecrets(
                config_context=args.v3, skip_tls_verify=args.skip_tls_verify
            ).main()
        if args.v3:
            if args.accessKey or (args.json and args.provider == "aws"):
                if args.json and args.provider == "aws":
                    args.accessKey, args.accessSecret = helpers.extractAwsKeys(args.json, parser)
                crc = create.createV3S3Credential(
                    args.v3,
                    args.dry_run,
                    args.skip_tls_verify,
                    args.quiet,
                    args.verbose,
                    args.accessKey,
                    args.accessSecret,
                    args.bucketName,
                )
            elif args.json:
                crc = create.createV3CloudCredential(
                    args.v3,
                    args.dry_run,
                    args.skip_tls_verify,
                    args.quiet,
                    args.verbose,
                    args.json,
                    args.bucketName,
                    parser,
                )
            if args.accessKey or args.json:
                args.credential = []
                for key in crc["data"].keys():
                    args.credential.append([crc["metadata"]["name"], key])
                ard.credentials["items"].append(crc)
            manageV3Bucket(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                args.bucketName,
                args.provider,
                args.storageAccount,
                args.serverURL,
                args.http,
                args.skipCertValidation,
                args.credential,
                ard,
                parser,
            )
        else:
            if args.accessKey:
                crc = create.createS3Credential(
                    args.quiet, args.verbose, args.accessKey, args.accessSecret, args.bucketName
                )
                args.credential = crc["id"]
            elif args.json:
                crc = create.createCloudCredential(
                    args.quiet,
                    args.verbose,
                    args.json,
                    args.bucketName,
                    args.provider,
                    parser,
                )
                args.credential = crc["id"]
            manageBucket(
                args.provider,
                args.bucketName,
                args.storageAccount,
                args.serverURL,
                args.credential,
                args.quiet,
                args.verbose,
            )

    elif args.objectType == "cluster":
        if args.v3:
            manageV3Cluster(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                args.clusterName,
                args.operator_version,
                args.regCred,
                args.registry,
                args.cloudID,
                args.headless,
                ard,
                parser,
            )
        else:
            rc = astraSDK.clusters.manageCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.cluster, args.defaultStorageClassID
            )
            if rc is False:
                raise SystemExit("astraSDK.clusters.manageCluster() failed")

    elif args.objectType == "cloud":
        credentialID = None
        # First create the credential
        if args.cloudType != "private":
            if args.credentialPath is None:
                parser.error(f"--credentialPath is required for cloudType of {args.cloudType}")
            rc = create.createCloudCredential(
                args.quiet,
                args.verbose,
                args.credentialPath,
                args.cloudName,
                args.cloudType,
                parser,
            )
            credentialID = rc["id"]
        # Next manage the cloud
        rc = astraSDK.clouds.manageCloud(quiet=args.quiet, verbose=args.verbose).main(
            args.cloudName,
            args.cloudType,
            credentialID=credentialID,
            defaultBucketID=args.defaultBucketID,
        )
        if rc is False:
            raise SystemExit("astraSDK.clouds.manageCloud() failed")
    elif args.objectType == "ldap":
        ard.settings = astraSDK.settings.getSettings().main()
        ldapSetting = ard.getSingleDict("settings", "name", "astra.account.ldap", parser)
        rc = astraSDK.settings.manageLdap(quiet=args.quiet, verbose=args.verbose).main(
            ldapSetting["id"], ldapSetting["currentConfig"]
        )
        if rc is False:
            raise SystemExit("astraSDK.settings.manageLdap() failed")
