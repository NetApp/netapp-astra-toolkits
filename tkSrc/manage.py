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

import astraSDK
import tkSrc


def main(args, parser):
    if args.objectType == "app":
        if args.additionalNamespace:
            args.additionalNamespace = tkSrc.helpers.createNamespaceList(args.additionalNamespace)
        if args.clusterScopedResource:
            apiResourcesDict = astraSDK.apiresources.getApiResources().main(cluster=args.clusterID)
            # Validate input as argparse+choices is unable to only validate the first input
            for csr in args.clusterScopedResource:
                if csr[0] not in (apiRes := [a["kind"] for a in apiResourcesDict["items"]]):
                    parser.error(
                        f"argument -c/--clusterScopedResource: invalid choice: '{csr[0]}' "
                        f"(choose from {', '.join(apiRes)})"
                    )
            args.clusterScopedResource = tkSrc.helpers.createCsrList(
                args.clusterScopedResource, apiResourcesDict
            )
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
    elif args.objectType == "bucket":
        # Validate that both credentialID and accessKey/accessSecret were not specified
        if args.credentialID is not None and (
            args.accessKey is not None or args.accessSecret is not None
        ):
            parser.error(
                "if a credentialID is specified, neither accessKey nor accessSecret"
                + " should be specified."
            )
        # Validate args and create credential if credentialID was not specified
        if args.credentialID is None:
            if args.accessKey is None or args.accessSecret is None:
                parser.error(
                    "if a credentialID is not specified, both accessKey and "
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
                args.credentialID = crc["id"]
            else:
                raise SystemExit("astraSDK.credentials.createCredential() failed")
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
        # Create bucket parameters based on provider and optional arguments
        if args.provider == "azure":
            bucketParameters = {
                "azure": {"bucketName": args.bucketName, "storageAccount": args.storageAccount}
            }
        elif args.provider == "gcp":
            bucketParameters = {"gcp": {"bucketName": args.bucketName}}
        else:
            bucketParameters = {"s3": {"bucketName": args.bucketName, "serverURL": args.serverURL}}
        # Call manageBucket class
        rc = astraSDK.buckets.manageBucket(quiet=args.quiet, verbose=args.verbose).main(
            args.bucketName, args.credentialID, args.provider, bucketParameters
        )
        if rc is False:
            raise SystemExit("astraSDK.buckets.manageBucket() failed")
    elif args.objectType == "cluster":
        rc = astraSDK.clusters.manageCluster(quiet=args.quiet, verbose=args.verbose).main(
            args.clusterID, args.defaultStorageClassID
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
