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

import astraSDK


def main(args, parser, ard):
    if args.objectType == "app":
        rc = astraSDK.apps.unmanageApp(quiet=args.quiet, verbose=args.verbose).main(args.appID)
        if rc is False:
            raise SystemExit("astraSDK.apps.unmanageApp() failed")
    elif args.objectType == "bucket":
        rc = astraSDK.buckets.unmanageBucket(quiet=args.quiet, verbose=args.verbose).main(
            args.bucketID
        )
        if rc is False:
            raise SystemExit("astraSDK.buckets.unmanageBucket() failed")
    elif args.objectType == "cluster":
        # If this is a neptune-managed cluster, we need to destroy the AstraConnector CR, however
        # we do not want to do that without first ensuring the clusterID the user inputted matches
        # the current kubeconfig context
        if args.neptune:
            # Ensure we have an AstraConnector CR installed
            if ard.needsattr("connectors"):
                ard.connectors = astraSDK.k8s.getResources(quiet=True).main(
                    "astraconnectors", version="v1", group="astra.netapp.io"
                )
            if ard.connectors is None or len(ard.connectors["items"]) == 0:
                parser.error("AstraConnector operator not found on current Kubernetes context")
            elif len(ard.connectors["items"]) > 1:
                parser.error(
                    "multiple AstraConnector operators found on current Kubernetes context"
                )
            connector = ard.connectors["items"][0]
            # Destroy the AstraConnector CR and api token secret (TODO: regcred destruction?)
            if astraSDK.k8s.destroyResource(quiet=args.quiet, dry_run=args.dry_run).main(
                "astraconnectors",
                connector["metadata"]["name"],
                version="v1",
                group="astra.netapp.io",
            ):
                if not astraSDK.k8s.destroySecret(quiet=args.quiet, dry_run=args.dry_run).main(
                    connector["spec"]["astra"]["tokenRef"],
                    namespace=connector["metadata"]["namespace"],
                ):
                    raise SystemExit("astraSDK.k8s.destroySecret() failed")
            else:
                raise SystemExit("astraSDK.k8s.destroyResource() failed")
        else:
            if astraSDK.clusters.unmanageCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.cluster
            ):
                # "Private" cloud clusters+credentials also should be deleted
                if ard.needsattr("clusters"):
                    ard.clusters = astraSDK.clusters.getClusters().main()
                for cluster in ard.clusters["items"]:
                    for label in cluster["metadata"]["labels"]:
                        if (
                            cluster["id"] == args.cluster
                            and label["name"] == "astra.netapp.io/labels/read-only/cloudName"
                            and label["value"] == "private"
                        ):
                            if astraSDK.clusters.deleteCluster(
                                quiet=args.quiet, verbose=args.verbose
                            ).main(args.cluster, cluster["cloudID"]):
                                if astraSDK.credentials.destroyCredential(
                                    quiet=args.quiet, verbose=args.verbose
                                ).main(cluster.get("credentialID")):
                                    print("Credential deleted")
                                else:
                                    raise SystemExit(
                                        "astraSDK.credentials.destroyCredential() failed"
                                    )
                            else:
                                raise SystemExit("astraSDK.clusters.deleteCluster() failed")
            else:
                raise SystemExit("astraSDK.clusters.unmanageCluster() failed")
    elif args.objectType == "cloud":
        if ard.needsattr("cloud"):
            ard.clouds = astraSDK.clouds.getClouds().main()
        rc = astraSDK.clouds.unmanageCloud(quiet=args.quiet, verbose=args.verbose).main(
            args.cloudID
        )
        if rc:
            # Cloud credentials also should be deleted
            for cloud in ard.clouds["items"]:
                if cloud["id"] == args.cloudID:
                    if cloud.get("credentialID"):
                        if astraSDK.credentials.destroyCredential(
                            quiet=args.quiet, verbose=args.verbose
                        ).main(cloud.get("credentialID")):
                            print("Credential deleted")
                        else:
                            raise SystemExit("astraSDK.credentials.destroyCredential() failed")
        else:
            raise SystemExit("astraSDK.clusters.unmanageCloud() failed")
