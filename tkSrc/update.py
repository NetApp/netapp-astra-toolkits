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
import json
import yaml

from tkSrc import helpers
import astraSDK


def main(args, ard, config=None):
    if args.objectType == "bucket":
        # Validate that both credentialID and accessKey/accessSecret were not specified
        if args.credentialID is not None and (
            args.accessKey is not None or args.accessSecret is not None
        ):
            helpers.parserError(
                "if a credentialID is specified, neither accessKey nor accessSecret"
                + " should be specified."
            )
        # Validate args and create credential if credentialID was not specified
        if args.credentialID is None:
            if args.accessKey is None or args.accessSecret is None:
                helpers.parserError(
                    "if a credentialID is not specified, both accessKey and "
                    + "accessSecret arguments must be provided."
                )
            if ard.needsattr("buckets"):
                ard.buckets = astraSDK.buckets.getBuckets(config=config).main()
            encodedKey = base64.b64encode(args.accessKey.encode("utf-8")).decode("utf-8")
            encodedSecret = base64.b64encode(args.accessSecret.encode("utf-8")).decode("utf-8")
            try:
                crc = astraSDK.credentials.createCredential(
                    quiet=args.quiet, verbose=args.verbose, config=config
                ).main(
                    next(b for b in ard.buckets["items"] if b["id"] == args.bucketID)["name"],
                    "s3",
                    {"accessKey": encodedKey, "accessSecret": encodedSecret},
                    cloudName="s3",
                )
            except StopIteration:
                helpers.parserError(f"{args.bucketID} does not seem to be a valid bucketID")
            if crc:
                args.credentialID = crc["id"]
            else:
                raise SystemExit("astraSDK.credentials.createCredential() failed")
        # Call updateBucket class
        rc = astraSDK.buckets.updateBucket(
            quiet=args.quiet, verbose=args.verbose, config=config
        ).main(args.bucketID, credentialID=args.credentialID)
        if rc is False:
            raise SystemExit("astraSDK.buckets.updateBucket() failed")
    elif args.objectType == "cloud":
        if args.credentialPath:
            with open(args.credentialPath, encoding="utf8") as f:
                try:
                    credDict = json.loads(f.read().rstrip())
                except json.decoder.JSONDecodeError:
                    helpers.parserError(f"{args.credentialPath} does not seem to be valid JSON")
            encodedStr = base64.b64encode(json.dumps(credDict).encode("utf-8")).decode("utf-8")
            if ard.needsattr("clouds"):
                ard.clouds = astraSDK.clouds.getClouds(config=config).main()
            try:
                cloud = next(c for c in ard.clouds["items"] if c["id"] == args.cloudID)
            except StopIteration:
                helpers.parserError(f"{args.cloudID} does not seem to be a valid cloudID")
            rc = astraSDK.credentials.createCredential(
                quiet=args.quiet, verbose=args.verbose, config=config
            ).main(
                "astra-sa@" + cloud["name"],
                "service-account",
                {"base64": encodedStr},
                cloud["cloudType"],
            )
            if rc:
                args.credentialID = rc["id"]
            else:
                raise SystemExit("astraSDK.credentials.createCredential() failed")
        # Next update the cloud
        rc = astraSDK.clouds.updateCloud(
            quiet=args.quiet, verbose=args.verbose, config=config
        ).main(
            args.cloudID,
            credentialID=args.credentialID,
            defaultBucketID=args.defaultBucketID,
        )
        if rc is False:
            raise SystemExit("astraSDK.clouds.updateCloud() failed")
    elif args.objectType == "cluster":
        # Get the cluster information based on the clusterID input
        if ard.needsattr("clusters"):
            ard.clusters = astraSDK.clusters.getClusters(config=config).main()
        cluster = ard.getSingleDict("clusters", "id", args.clusterID)
        # Currently this is required to be True, but this will not always be the case
        if args.credentialPath:
            with open(args.credentialPath, encoding="utf8") as f:
                kubeconfigDict = yaml.load(f.read().rstrip(), Loader=yaml.SafeLoader)
                encodedStr = base64.b64encode(json.dumps(kubeconfigDict).encode("utf-8")).decode(
                    "utf-8"
                )
            rc = astraSDK.credentials.updateCredential(
                quiet=args.quiet, verbose=args.verbose, config=config
            ).main(
                cluster.get("credentialID"),
                kubeconfigDict["clusters"][0]["name"],
                keyStore={"base64": encodedStr},
            )
            if rc is False:
                raise SystemExit("astraSDK.credentials.updateCredential() failed")
        if args.defaultBucketID:
            rc = astraSDK.clusters.updateCluster(
                quiet=args.quiet, verbose=args.verbose, config=config
            ).main(
                cluster.get("id"),
                defaultBucketID=args.defaultBucketID,
            )
            if rc is False:
                raise SystemExit("astraSDK.clusters.updateCluster() failed")
    elif args.objectType == "protection" or args.objectType == "schedule":
        if ard.needsattr("protections"):
            ard.protections = astraSDK.protections.getProtectionpolicies(config=config).main()
        protection = ard.getSingleDict("protections", "id", args.protection)
        granularity = protection["granularity"]
        if granularity == "hourly" and args.hour:
            helpers.parserError(f"{granularity} granularity must not specify -H / --hour")
        if granularity == "hourly" or granularity == "daily" or granularity == "monthly":
            if args.dayOfWeek:
                helpers.parserError(f"{granularity} granularity must not specify -W / --dayOfWeek")
        if granularity == "hourly" or granularity == "daily" or granularity == "weekly":
            if args.dayOfMonth:
                helpers.parserError(f"{granularity} granularity must not specify -M / --dayOfMonth")
        rc = astraSDK.protections.updateProtectionpolicy(
            quiet=args.quiet, verbose=args.verbose, config=config
        ).main(
            protection["appID"],
            protection["id"],
            protection["granularity"],
            str(args.backupRetention) if args.backupRetention else protection["backupRetention"],
            (
                str(args.snapshotRetention)
                if args.snapshotRetention
                else protection["snapshotRetention"]
            ),
            minute=str(args.minute) if args.minute else protection.get("minute"),
            hour=str(args.hour) if args.hour else protection.get("hour"),
            dayOfWeek=str(args.dayOfWeek) if args.dayOfWeek else protection.get("dayOfWeek"),
            dayOfMonth=str(args.dayOfMonth) if args.dayOfMonth else protection.get("dayOfMonth"),
            bucketID=args.bucket if args.bucket else protection.get("bucketID"),
        )
        if rc is False:
            raise SystemExit("astraSDK.protection.updateProtectionpolicy() failed")
    elif args.objectType == "replication":
        # Gather replication data
        if ard.needsattr("replications"):
            ard.replications = astraSDK.replications.getReplicationpolicies(config=config).main()
            if not ard.replications:  # Gracefully handle ACS env
                helpers.parserError("'replication' commands are currently only supported in ACC.")
        repl = None
        for replication in ard.replications["items"]:
            if args.replicationID == replication["id"]:
                repl = replication
        if not repl:
            helpers.parserError(f"replicationID {args.replicationID} not found")
        # Make call based on operation type
        if args.operation == "resync":
            if not args.dataSource:
                helpers.parserError("--dataSource must be provided for 'resync' operations")
            if repl["state"] != "failedOver":
                helpers.parserError(
                    "to resync a replication, it must be in a 'failedOver' state"
                    + f", not a(n) '{repl['state']}' state"
                )
            if args.dataSource in [repl["sourceAppID"], repl["sourceClusterID"]]:
                rc = astraSDK.replications.updateReplicationpolicy(
                    quiet=args.quiet, verbose=args.verbose, config=config
                ).main(
                    args.replicationID,
                    "established",
                    sourceAppID=repl["sourceAppID"],
                    sourceClusterID=repl["sourceClusterID"],
                    destinationAppID=repl["destinationAppID"],
                    destinationClusterID=repl["destinationClusterID"],
                )
            elif args.dataSource in [repl["destinationAppID"], repl["destinationClusterID"]]:
                rc = astraSDK.replications.updateReplicationpolicy(
                    quiet=args.quiet, verbose=args.verbose, config=config
                ).main(
                    args.replicationID,
                    "established",
                    sourceAppID=repl["destinationAppID"],
                    sourceClusterID=repl["destinationClusterID"],
                    destinationAppID=repl["sourceAppID"],
                    destinationClusterID=repl["sourceClusterID"],
                )
            else:
                helpers.parserError(
                    f"dataSource '{args.dataSource}' not one of:\n"
                    + f"\t{repl['sourceAppID']}\t(original sourceAppID)\n"
                    + f"\t{repl['sourceClusterID']}\t(original sourceClusterID)\n"
                    + f"\t{repl['destinationAppID']}\t(original destinationAppID)\n"
                    + f"\t{repl['destinationClusterID']}\t(original destinationClusterID)"
                )
        elif args.operation == "reverse":
            if repl["state"] != "established" and repl["state"] != "failedOver":
                helpers.parserError(
                    "to reverse a replication, it must be in an `established` or "
                    + f"'failedOver' state, not a(n) '{repl['state']}' state"
                )
            rc = astraSDK.replications.updateReplicationpolicy(
                quiet=args.quiet, verbose=args.verbose, config=config
            ).main(
                args.replicationID,
                "established",
                sourceAppID=repl["destinationAppID"],
                sourceClusterID=repl["destinationClusterID"],
                destinationAppID=repl["sourceAppID"],
                destinationClusterID=repl["sourceClusterID"],
            )
        else:  # failover
            if repl["state"] != "established":
                helpers.parserError(
                    "to failover a replication, it must be in an 'established' state"
                    + f", not a(n) '{repl['state']}' state"
                )
            rc = astraSDK.replications.updateReplicationpolicy(
                quiet=args.quiet, verbose=args.verbose, config=config
            ).main(args.replicationID, "failedOver")
        # Exit based on response
        if rc:
            print(f"Replication {args.operation} initiated")
        else:
            raise SystemExit("astraSDK.replications.updateReplicationpolicy() failed")
    elif args.objectType == "script":
        with open(args.filePath, encoding="utf8") as f:
            encodedStr = base64.b64encode(f.read().rstrip().encode("utf-8")).decode("utf-8")
        rc = astraSDK.scripts.updateScript(
            quiet=args.quiet, verbose=args.verbose, config=config
        ).main(args.scriptID, source=encodedStr)
        if rc is False:
            raise SystemExit("astraSDK.scripts.updateScript() failed")
