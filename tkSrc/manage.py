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
import json
import yaml

import astraSDK
import tkSrc


def main(args, parser, ard):
    if args.objectType == "app":
        if args.additionalNamespace:
            args.additionalNamespace = tkSrc.helpers.createNamespaceList(
                args.additionalNamespace, v3=args.v3
            )
        if args.clusterScopedResource:
            if args.v3:
                # If we're running a v3 command, we don't have the clusterID arg populated by
                # the end user, so gather the Connector information which contains the cluster
                # name, which can be used in place of the cluster ID
                ard.connectors = astraSDK.k8s.getResources(config_context=args.v3).main(
                    "astraconnectors", version="v1", group="astra.netapp.io"
                )
                ard.getSingleDict(
                    "connectors",
                    "spec.astra.accountId",
                    astraSDK.common.getConfig().conf["uid"],
                    parser,
                )
                args.clusterID = ard.getSingleDict(
                    "connectors",
                    "spec.astra.accountId",
                    astraSDK.common.getConfig().conf["uid"],
                    None,
                )["spec"]["astra"]["clusterName"]
            ard.apiresources = astraSDK.apiresources.getApiResources().main(cluster=args.clusterID)
            # Validate input as argparse+choices is unable to only validate the first input
            for csr in args.clusterScopedResource:
                if csr[0] not in (apiRes := [a["kind"] for a in ard.apiresources["items"]]):
                    parser.error(
                        f"argument -c/--clusterScopedResource: invalid choice: '{csr[0]}' "
                        f"(choose from {', '.join(apiRes)})"
                    )
            args.clusterScopedResource = tkSrc.helpers.createCsrList(
                args.clusterScopedResource, ard.apiresources, v3=args.v3
            )
        if args.v3:
            template = tkSrc.helpers.setupJinja(args.objectType)
            v3_dict = yaml.safe_load(
                template.render(
                    appName=tkSrc.helpers.isRFC1123(args.appName),
                    namespace=args.namespace,
                    labelSelectors=(
                        f"{args.labelSelectors.split('=')[0]}: {args.labelSelectors.split('=')[1]}"
                        if args.labelSelectors
                        else None
                    ),
                    addNamespaces=tkSrc.helpers.prependDump(args.additionalNamespace, prepend=4),
                    clusterScopedResources=tkSrc.helpers.prependDump(
                        args.clusterScopedResource, prepend=4
                    ),
                ),
            )
            if args.dry_run == "client":
                print(yaml.dump(v3_dict).rstrip("\n"))
            else:
                astraSDK.k8s.createResource(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(
                    f"{v3_dict['kind'].lower()}s",
                    v3_dict["metadata"]["namespace"],
                    v3_dict,
                    version="v1",
                    group="astra.netapp.io",
                )
        else:
            rc = astraSDK.apps.manageApp(quiet=args.quiet, verbose=args.verbose).main(
                tkSrc.helpers.isRFC1123(args.appName),
                args.namespace,
                args.clusterID,
                args.labelSelectors,
                addNamespaces=args.additionalNamespace,
                clusterScopedResources=args.clusterScopedResource,
            )
            if rc is False:
                raise SystemExit("astraSDK.apps.manageApp() failed")

    elif args.objectType == "bucket" or args.objectType == "appVault":
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

        if args.v3:
            if ard.needsattr("credentials"):
                ard.credentials = astraSDK.k8s.getSecrets(config_context=args.v3).main()
            # Create providerCredentials based on args.provider input
            if args.provider == "azure":
                keyNameList = ["accountKey"]
            elif args.provider == "gcp":
                keyNameList = ["credentials"]
            else:
                keyNameList = ["accessKeyID", "secretAccessKey"]
            template = tkSrc.helpers.setupJinja(args.objectType)
            v3_dict = yaml.safe_load(
                template.render(
                    bucketName=tkSrc.helpers.isRFC1123(args.bucketName),
                    providerType=args.provider,
                    accountName=args.storageAccount,
                    endpoint=args.serverURL,
                    secure=("false" if args.http else None),
                    skipCertValidation=("true" if args.skipCertValidation else None),
                    providerCredentials=tkSrc.helpers.prependDump(
                        tkSrc.helpers.createSecretKeyDict(keyNameList, args, ard, parser), prepend=4
                    ),
                )
            )
            if args.dry_run == "client":
                print(yaml.dump(v3_dict).rstrip("\n"))
            else:
                astraSDK.k8s.createResource(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(
                    f"{v3_dict['kind'].lower()}s",
                    v3_dict["metadata"]["namespace"],
                    v3_dict,
                    version="v1",
                    group="astra.netapp.io",
                )

        else:
            # Validate that both credentialID and accessKey/accessSecret were not specified
            if args.credential is not None and (
                args.accessKey is not None or args.accessSecret is not None
            ):
                parser.error(
                    "if a credential is specified, neither accessKey nor accessSecret"
                    + " should be specified."
                )
            # Validate args and create credential if credential was not specified
            if args.credential is None:
                if args.accessKey is None or args.accessSecret is None:
                    parser.error(
                        "if a credential is not specified, both accessKey and "
                        + "accessSecret arguments must be provided."
                    )
                encodedKey = base64.b64encode(args.accessKey.encode("utf-8")).decode("utf-8")
                encodedSecret = base64.b64encode(args.accessSecret.encode("utf-8")).decode("utf-8")
                crc = astraSDK.credentials.createCredential(
                    quiet=args.quiet, verbose=args.verbose
                ).main(
                    args.bucketName,
                    "s3",
                    {"accessKey": encodedKey, "accessSecret": encodedSecret},
                    cloudName="s3",
                )
                if crc:
                    args.credential = crc["id"]
                else:
                    raise SystemExit("astraSDK.credentials.createCredential() failed")
            # Create bucket parameters based on provider and optional arguments
            if args.provider == "azure":
                bucketParameters = {
                    "azure": {"bucketName": args.bucketName, "storageAccount": args.storageAccount}
                }
            elif args.provider == "gcp":
                bucketParameters = {"gcp": {"bucketName": args.bucketName}}
            else:
                bucketParameters = {
                    "s3": {"bucketName": args.bucketName, "serverURL": args.serverURL}
                }
            # Call manageBucket class
            rc = astraSDK.buckets.manageBucket(quiet=args.quiet, verbose=args.verbose).main(
                args.bucketName, args.credential, args.provider, bucketParameters
            )
            if rc is False:
                raise SystemExit("astraSDK.buckets.manageBucket() failed")

    elif args.objectType == "cluster":
        if args.v3:
            # Install the operator
            config_file, context = tuple(args.v3.split(":"))
            tkSrc.helpers.run(
                f"kubectl --context={context} apply "
                f"--dry_run={args.dry_run if args.dry_run else 'none'} -f "
                f"{tkSrc.helpers.getOperatorURL(args.operator_version)}",
                env={"KUBECONFIG": config_file} if config_file != "None" else None,
            )
            # Create the astra API token secret
            apiToken = astraSDK.k8s.createAstraApiToken(
                quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
            ).main()
            # Handle the registry secret
            if not args.regCred:
                cred = astraSDK.k8s.createRegCred(
                    quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
                ).main(registry=args.registry, namespace="astra-connector")
                if not cred:
                    raise SystemExit("astraSDK.k8s.createRegCred() failed")
                args.regCred = cred["metadata"]["name"]
            else:
                if ard.needsattr("credentials"):
                    ard.credentials = astraSDK.k8s.getSecrets(config_context=args.v3).main()
                cred = ard.getSingleDict("credentials", "metadata.name", args.regCred, parser)
            # Create the AstraConnector CR
            connector = astraSDK.k8s.createAstraConnector(
                quiet=args.quiet, dry_run=args.dry_run, config_context=args.v3
            ).main(
                args.clusterName,
                args.cloudID,
                apiToken["metadata"]["name"],
                args.regCred,
                registry=args.registry,
            )
            if not connector:
                raise SystemExit("astraSDK.k8s.createAstraConnector() failed")
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
            with open(args.credentialPath, encoding="utf8") as f:
                try:
                    credDict = json.loads(f.read().rstrip())
                except json.decoder.JSONDecodeError:
                    parser.error(f"{args.credentialPath} does not seem to be valid JSON")
            encodedStr = base64.b64encode(json.dumps(credDict).encode("utf-8")).decode("utf-8")
            rc = astraSDK.credentials.createCredential(quiet=args.quiet, verbose=args.verbose).main(
                "astra-sa@" + args.cloudName,
                "service-account",
                {"base64": encodedStr},
                args.cloudType,
            )
            if rc:
                credentialID = rc["id"]
            else:
                raise SystemExit("astraSDK.credentials.createCredential() failed")
        # Next manage the cloud
        rc = astraSDK.clouds.manageCloud(quiet=args.quiet, verbose=args.verbose).main(
            args.cloudName,
            args.cloudType,
            credentialID=credentialID,
            defaultBucketID=args.defaultBucketID,
        )
        if rc is False:
            raise SystemExit("astraSDK.clouds.manageCloud() failed")
