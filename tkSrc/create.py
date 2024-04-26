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
import os
import sys
import time
import yaml

import astraSDK
from tkSrc import helpers


def monitorProtectionTask(protectionID, protectionType, appID, background, pollTimer, parser):
    """Ensure backup/snapshot task was created successfully, then monitor"""
    if protectionID is False:
        return False
    if protectionType == "backup":
        protection_class = astraSDK.backups.getBackups()
    elif protectionType == "snapshot":
        protection_class = astraSDK.snapshots.getSnaps()
    else:
        parser.error(f"unknown protection type: {protectionType}")

    print(f"Starting {protectionType} of {appID}")
    if background:
        print(
            f"Background {protectionType} flag selected, run 'list {protectionType}s' to get status"
        )
        return True

    print(f"Waiting for {protectionType} to complete.", end="")
    sys.stdout.flush()
    err_counter = []
    while len(err_counter) < 3:
        try:
            objects = protection_class.main(appFilter=appID)
            if not objects:
                raise Exception(f"astraSDK.{protectionType}s.get{protectionType}s().main() failed")
            protection_found = False
            for obj in objects["items"]:
                if obj["id"] == protectionID:
                    protection_found = True
                    if obj["state"] == "completed":
                        print("complete!")
                        sys.stdout.flush()
                        return protectionID
                    elif obj["state"] == "failed":
                        print(f"{protectionType} job failed")
                        return False
            if not protection_found:
                raise Exception(f"Protection ID {protectionID} not found")
            time.sleep(pollTimer)
            print(".", end="")
            sys.stdout.flush()
        except Exception as err:
            err_counter.append(err)
    for err in set([str(e) for e in err_counter]):
        protection_class.printError(err + "\n")
    return False


def monitorV3ProtectionTask(protection, pollTimer, parser, v3, skip_tls_verify):
    name = protection["metadata"]["name"]
    singular = protection["kind"].lower()
    resource_class = astraSDK.k8s.getResources(config_context=v3, skip_tls_verify=skip_tls_verify)
    print(f"Waiting for {singular} to complete.", end="")
    sys.stdout.flush()
    err_counter = []
    while len(err_counter) < 3:
        try:
            resources = resource_class.main(
                f"{singular}s", filters=[{"keyFilter": "metadata.name", "valFilter": name}]
            )
            if not resources:
                raise Exception("astraSDK.k8s.getResources().main() failed")
            elif not resources["items"]:
                raise Exception(f"{singular} {name} not found")
            elif len(resources["items"]) > 1:
                raise Exception(f"Multiple {singular}s found with name {name}")
            resource = resources["items"][0]
            if resource["status"]["state"] == "Completed":
                print("complete!")
                sys.stdout.flush()
                return resource
            elif resource["status"]["state"] == "Failed" or resource["status"]["state"] == "Error":
                print(f"{singular} failed")
                return False
            time.sleep(pollTimer)
            print(".", end="")
            sys.stdout.flush()
        except Exception as err:
            err_counter.append(err)
    for err in set([str(e) for e in err_counter]):
        resource_class.printError(err + "\n")
    return False


def createV3ConnectorOperator(v3, dry_run, skip_tls_verify, verbose, operator_version):
    """Creates the Arch 3.0 Astra Connector Operator"""
    context, config_file = tuple(v3.split("@"))
    helpers.run(
        f"kubectl --insecure-skip-tls-verify={skip_tls_verify} --context={context} "
        f"-v={6 if verbose else 0} apply --dry_run={dry_run if dry_run else 'none'} -f "
        f"{helpers.getOperatorURL(operator_version)}",
        env={"KUBECONFIG": os.path.expanduser(config_file)} if config_file != "None" else None,
    )


def createCloudCredential(quiet, verbose, path, name, cloudType, parser):
    """Create a public cloud (AWS/Azure/GCP) credential via the API"""
    credDict = helpers.openJson(path, parser)
    encodedStr = base64.b64encode(json.dumps(credDict).encode("utf-8")).decode("utf-8")
    rc = astraSDK.credentials.createCredential(quiet=quiet, verbose=verbose).main(
        "astra-sa@" + name,
        "service-account",
        {"base64": encodedStr},
        cloudType,
    )
    if rc:
        return rc
    raise SystemExit("astraSDK.credentials.createCredential() failed")


def createV3CloudCredential(v3, dry_run, skip_tls_verify, quiet, verbose, path, name, parser):
    """Create a public cloud (AWS/Azure/GCP) credential via a Kubernetes secret"""
    credDict = helpers.openJson(path, parser)
    encodedStr = base64.b64encode(json.dumps(credDict).encode("utf-8")).decode("utf-8")
    data = {"credentials.json": encodedStr}
    namespace = "astra-connector"
    if dry_run == "client":
        secret_dict = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": name, "namespace": namespace},
            "data": data,
            "type": "Opaque",
        }
        print(yaml.dump(secret_dict).rstrip("\n"))
        print("---")
        return secret_dict
    return astraSDK.k8s.createGenericSecret(
        quiet=quiet,
        dry_run=dry_run,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main(f"{name}-", data, generateName=True, namespace=namespace)


def createLdapCredential(quiet, verbose, username, password, parser):
    """Create an LDAP bind credential via the API"""
    bindDn = base64.b64encode(username.encode("utf-8")).decode("utf-8")
    enpass = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    rc = astraSDK.credentials.createCredential(quiet=quiet, verbose=verbose).main(
        "ldapBindCredential-" + username.split("@")[0],
        "generic",
        {"bindDn": bindDn, "password": enpass},
    )
    if rc:
        return rc
    raise SystemExit("astraSDK.credentials.createCredential() failed")


def createS3Credential(quiet, verbose, accessKey, accessSecret, name):
    """Create an S3 (accessKey and accessSecret) bucket credential via the API"""
    encodedKey = base64.b64encode(accessKey.encode("utf-8")).decode("utf-8")
    encodedSecret = base64.b64encode(accessSecret.encode("utf-8")).decode("utf-8")
    rc = astraSDK.credentials.createCredential(quiet=quiet, verbose=verbose).main(
        name, "s3", {"accessKey": encodedKey, "accessSecret": encodedSecret}, cloudName="s3"
    )
    if rc:
        return rc
    else:
        raise SystemExit("astraSDK.credentials.createCredential() failed")


def createV3S3Credential(
    v3, dry_run, skip_tls_verify, quiet, verbose, accessKey, accessSecret, name
):
    """Create a public cloud (AWS/Azure/GCP) credential via a Kubernetes secret"""
    encodedKey = base64.b64encode(accessKey.encode("utf-8")).decode("utf-8")
    encodedSecret = base64.b64encode(accessSecret.encode("utf-8")).decode("utf-8")
    data = {"accessKeyID": encodedKey, "secretAccessKey": encodedSecret}
    namespace = "astra-connector"
    if dry_run == "client":
        secret_dict = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": name, "namespace": namespace},
            "data": data,
            "type": "Opaque",
        }
        print(yaml.dump(secret_dict).rstrip("\n"))
        print("---")
        return secret_dict
    return astraSDK.k8s.createGenericSecret(
        quiet=quiet,
        dry_run=dry_run,
        verbose=verbose,
        config_context=v3,
        skip_tls_verify=skip_tls_verify,
    ).main(f"{name}-", data, generateName=True, namespace=namespace)


def createV3Backup(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    name,
    app,
    appVault,
    snapshot=None,
    reclaimPolicy=None,
    generateName=None,
):
    """Create an app backup via a Kubernetes custom resource"""
    template = helpers.setupJinja("backup")
    v3_dict = yaml.safe_load(
        template.render(
            name=(helpers.isRFC1123(name) if name else name),
            appName=app,
            appVaultName=appVault,
            snapshotName=snapshot,
            reclaimPolicy=reclaimPolicy,
            generateName=generateName,
        )
    )
    if dry_run == "client":
        print(yaml.dump(v3_dict).rstrip("\n"))
        return v3_dict
    else:
        return astraSDK.k8s.createResource(
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


def createV3Hook(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    parser,
    app,
    name,
    filePath,
    operation,
    hookArguments=None,
    containerImage=None,
    namespace=None,
    podName=None,
    label=None,
    containerName=None,
):
    """Creates an exec hook via a Kubernetes custom resource"""
    encodedStr = helpers.openScript(filePath, parser)
    template = helpers.setupJinja("hook")
    v3_dict = yaml.safe_load(
        template.render(
            name=helpers.isRFC1123(name, parser=parser),
            action=operation.split("-")[1],
            appName=app,
            arguments=helpers.prependDump(helpers.createHookList(hookArguments), prepend=4),
            hookSource=encodedStr,
            matchingCriteria=helpers.prependDump(
                helpers.createCriteriaList(
                    containerImage if containerImage else [],
                    namespace if namespace else [],
                    podName if podName else [],
                    label if label else [],
                    containerName if containerName else [],
                ),
                prepend=4,
            ),
            stage=operation.split("-")[0],
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


def createV3Protection(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    app,
    bucket,
    granularity,
    backupRetention,
    snapshotRetention,
    minute,
    hour,
    dayOfWeek,
    dayOfMonth,
):
    """Create a protection policy via a Kubernetes custom resource"""
    template = helpers.setupJinja("protection")
    v3_dict = yaml.safe_load(
        template.render(
            name=helpers.isRFC1123(f"{granularity}-{app}", ignore_length=True) + "-",
            appName=app,
            appVaultName=bucket,
            backupRetention=backupRetention,
            dayOfMonth=dayOfMonth,
            dayOfWeek=dayOfWeek,
            granularity=granularity,
            hour=hour,
            minute=minute,
            snapshotRetention=snapshotRetention,
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


def createV3Snapshot(
    v3,
    dry_run,
    skip_tls_verify,
    quiet,
    verbose,
    name,
    app,
    appVault,
    reclaimPolicy=None,
    createdTimeout=None,
    readyToUseTimeout=None,
    generateName=None,
):
    """Create an app snapshot via a Kubernetes custom resource"""
    template = helpers.setupJinja("snapshot")
    v3_dict = yaml.safe_load(
        template.render(
            name=(helpers.isRFC1123(name) if name else name),
            appName=app,
            appVaultName=appVault,
            reclaimPolicy=reclaimPolicy,
            createdTimeout=(None if not createdTimeout else str(createdTimeout)),
            readyToUseTimeout=(None if not readyToUseTimeout else str(readyToUseTimeout)),
            generateName=generateName,
        )
    )
    if dry_run == "client":
        print(yaml.dump(v3_dict).rstrip("\n"))
        return v3_dict
    else:
        return astraSDK.k8s.createResource(
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


def main(args, parser, ard):
    if args.objectType == "backup":
        if args.v3:
            if ard.needsattr("buckets"):
                ard.buckets = astraSDK.k8s.getResources(
                    config_context=args.v3, skip_tls_verify=args.skip_tls_verify
                ).main("appvaults")
            if args.bucket is None:
                args.bucket = ard.getSingleDict("buckets", "status.state", "available", parser)[
                    "metadata"
                ]["name"]
            backup = createV3Backup(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                args.name,
                args.app,
                args.bucket,
                args.snapshot,
                args.reclaimPolicy,
            )
            if backup and not args.dry_run and not args.background:
                monitorV3ProtectionTask(
                    backup, args.pollTimer, parser, args.v3, args.skip_tls_verify
                )
        else:
            protectionID = astraSDK.backups.takeBackup(quiet=args.quiet, verbose=args.verbose).main(
                args.app,
                helpers.isRFC1123(args.name, parser=parser),
                bucketID=args.bucket,
                snapshotID=args.snapshot,
            )
            rc = monitorProtectionTask(
                protectionID,
                args.objectType,
                args.app,
                args.background,
                args.pollTimer,
                parser,
            )
            if rc is False:
                raise SystemExit("monitorProtectionTask() failed")
    elif args.objectType == "cluster":
        kubeconfigDict = helpers.openYaml(args.filePath, parser)
        encodedStr = base64.b64encode(json.dumps(kubeconfigDict).encode("utf-8")).decode("utf-8")
        rc = astraSDK.credentials.createCredential(quiet=args.quiet, verbose=args.verbose).main(
            kubeconfigDict["clusters"][0]["name"],
            "kubeconfig",
            {"base64": encodedStr},
            cloudName="private",
        )
        if rc:
            rc = astraSDK.clusters.addCluster(quiet=args.quiet, verbose=args.verbose).main(
                args.cloudID,
                rc["id"],
                privateRouteID=args.privateRouteID,
            )
            if rc is False:
                raise SystemExit("astraSDK.clusters.createCluster() failed")
        else:
            raise SystemExit("astraSDK.credentials.createCredential() failed")
    elif args.objectType == "group":
        ldapGroups = astraSDK.groups.getLdapGroups().main(dnFilter=args.dn, matchType="eq")
        if len(ldapGroups["items"]) == 0:
            parser.error(f"0 LDAP groups found with DN '{args.dn}'")
        elif len(ldapGroups["items"]) > 1:
            parser.error(f"multiple LDAP users found with DN '{args.dn}'")
        # First create the group
        grc = astraSDK.groups.createGroup(quiet=args.quiet, verbose=args.verbose).main(args.dn)
        if grc:
            # Next create the role binding
            if not astraSDK.rolebindings.createRolebinding(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.role,
                groupID=grc["id"],
                roleConstraints=helpers.createConstraintList(
                    args.namespaceConstraint, args.labelConstraint
                ),
            ):
                raise SystemExit("astraSDK.rolebindings.createRolebinding() failed")
        else:
            raise SystemExit("astraSDK.groups.createGroup() failed")
    elif args.objectType == "hook" or args.objectType == "exechook":
        if args.v3:
            createV3Hook(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                parser,
                args.app,
                args.name,
                args.filePath,
                args.operation,
                hookArguments=args.hookArguments,
                containerImage=args.containerImage,
                namespace=args.namespace,
                podName=args.podName,
                label=args.label,
                containerName=args.containerName,
            )
        else:
            rc = astraSDK.hooks.createHook(quiet=args.quiet, verbose=args.verbose).main(
                args.app,
                args.name,
                args.script,
                args.operation.split("-")[0],
                args.operation.split("-")[1],
                helpers.createHookList(args.hookArguments),
                matchingCriteria=helpers.createCriteriaList(
                    args.containerImage,
                    args.namespace,
                    args.podName,
                    args.label,
                    args.containerName,
                ),
            )
            if rc is False:
                raise SystemExit("astraSDK.hooks.createHook() failed")
    elif args.objectType == "ldap":
        credential = createLdapCredential(
            args.quiet, args.verbose, args.username, args.password, parser
        )
        ard.settings = astraSDK.settings.getSettings().main()
        ldapSetting = ard.getSingleDict("settings", "name", "astra.account.ldap", parser)
        rc = astraSDK.settings.createLdap(quiet=args.quiet, verbose=args.verbose).main(
            ldapSetting["id"],
            args.url,
            args.port,
            credential["id"],
            args.userBaseDN,
            args.userSearchFilter,
            args.userLoginAttribute,
            args.groupBaseDN,
            groupSearchFilter=args.groupSearchFilter,
            secureMode=args.secure,
        )
        if rc is False:
            raise SystemExit("astraSDK.settings.createLdap() failed")
    elif args.objectType == "protection" or args.objectType == "schedule":
        naStr = "" if args.v3 else "*"
        if args.granularity == "hourly":
            if args.hour:
                parser.error("'hourly' granularity must not specify -H / --hour")
            args.hour = naStr
            args.dayOfWeek = naStr
            args.dayOfMonth = naStr
        elif args.granularity == "daily":
            if not isinstance(args.hour, int) and not args.hour:
                parser.error("'daily' granularity requires -H / --hour")
            args.dayOfWeek = naStr
            args.dayOfMonth = naStr
        elif args.granularity == "weekly":
            if not isinstance(args.hour, int) and not args.hour:
                parser.error("'weekly' granularity requires -H / --hour")
            if not isinstance(args.dayOfWeek, int) and not args.dayOfWeek:
                parser.error("'weekly' granularity requires -W / --dayOfWeek")
            args.dayOfMonth = naStr
        elif args.granularity == "monthly":
            if not isinstance(args.hour, int) and not args.hour:
                parser.error("'monthly' granularity requires -H / --hour")
            if args.dayOfWeek:
                parser.error("'monthly' granularity must not specify -W / --dayOfWeek")
            if not args.dayOfMonth:
                parser.error("'monthly' granularity requires -M / --dayOfMonth")
            args.dayOfWeek = naStr
        if args.v3:
            if ard.needsattr("buckets"):
                ard.buckets = astraSDK.k8s.getResources(
                    config_context=args.v3, skip_tls_verify=args.skip_tls_verify
                ).main("appvaults")
            if args.bucket is None:
                args.bucket = ard.getSingleDict("buckets", "status.state", "available", parser)[
                    "metadata"
                ]["name"]
            createV3Protection(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                args.app,
                args.bucket,
                args.granularity,
                args.backupRetention,
                args.snapshotRetention,
                args.minute,
                args.hour,
                args.dayOfWeek,
                args.dayOfMonth,
            )
        else:
            rc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.granularity,
                str(args.backupRetention),
                str(args.snapshotRetention),
                str(args.dayOfWeek),
                str(args.dayOfMonth),
                str(args.hour),
                str(args.minute),
                args.app,
                bucketID=args.bucket,
            )
            if rc is False:
                raise SystemExit("astraSDK.protections.createProtectionpolicy() failed")
    elif args.objectType == "replication":
        # Validate offset values and create DTSTART string
        if ":" in args.offset:
            hours = args.offset.split(":")[0].zfill(2)
            minutes = args.offset.split(":")[1].zfill(2)
        else:
            hours = "00"
            minutes = args.offset.zfill(2)
        if int(hours) < 0 or int(hours) > 23:
            parser.error(f"offset {args.offset} hours must be between 0 and 23, inclusive")
        elif int(minutes) < 0 or int(minutes) > 59:
            parser.error(f"offset '{args.offset}' minutes must be between 0 and 59, inclusive")
        dtstart = "DTSTART:20220101T" + hours + minutes + "00Z\n"
        # Create RRULE string
        rrule = "RRULE:FREQ=MINUTELY;INTERVAL="
        if "m" in args.replicationFrequency:
            rrule += args.replicationFrequency.strip("m")
        else:
            rrule += str(int(args.replicationFrequency.strip("h")) * 60)
        # Get Source ClusterID
        if ard.needsattr("apps"):
            ard.apps = astraSDK.apps.getApps().main()
        for app in ard.apps["items"]:
            if app["id"] == args.appID:
                sourceClusterID = app["clusterID"]
                sourceNamespaces = app["namespaces"]
        nsMapping = [
            {"clusterID": sourceClusterID, "namespaces": sourceNamespaces},
            {"clusterID": args.destClusterID, "namespaces": [args.destNamespace]},
        ]
        if args.destStorageClass:
            args.destStorageClass = [
                {"storageClassName": args.destStorageClass, "clusterID": args.destClusterID}
            ]
        rc = astraSDK.replications.createReplicationpolicy(
            quiet=args.quiet, verbose=args.verbose
        ).main(
            args.appID,
            args.destClusterID,
            nsMapping,
            destinationStorageClass=args.destStorageClass,
        )
        if rc:
            prc = astraSDK.protections.createProtectionpolicy(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                "custom",
                "0",
                "0",
                None,
                None,
                None,
                None,
                args.appID,
                dtstart + rrule,
            )
            if prc is False:
                raise SystemExit("astraSDK.protections.createProtectionpolicy() failed")
        else:
            raise SystemExit("astraSDK.replications.createReplicationpolicy() failed")
    elif args.objectType == "script":
        encodedStr = helpers.openScript(args.filePath, parser)
        rc = astraSDK.scripts.createScript(quiet=args.quiet, verbose=args.verbose).main(
            name=args.name, source=encodedStr, description=args.description
        )
        if rc is False:
            raise SystemExit("astraSDK.scripts.createScript() failed")
    elif args.objectType == "snapshot":
        if args.v3:
            if ard.needsattr("buckets"):
                ard.buckets = astraSDK.k8s.getResources(
                    config_context=args.v3, skip_tls_verify=args.skip_tls_verify
                ).main("appvaults")
            if args.bucket is None:
                args.bucket = ard.getSingleDict("buckets", "status.state", "available", parser)[
                    "metadata"
                ]["name"]
            snapshot = createV3Snapshot(
                args.v3,
                args.dry_run,
                args.skip_tls_verify,
                args.quiet,
                args.verbose,
                args.name,
                args.app,
                args.bucket,
                reclaimPolicy=args.reclaimPolicy,
                createdTimeout=args.createdTimeout,
                readyToUseTimeout=args.readyToUseTimeout,
            )
            if snapshot and not args.dry_run and not args.background:
                monitorV3ProtectionTask(
                    snapshot, args.pollTimer, parser, args.v3, args.skip_tls_verify
                )
        else:
            protectionID = astraSDK.snapshots.takeSnap(quiet=args.quiet, verbose=args.verbose).main(
                args.app,
                helpers.isRFC1123(args.name, parser=parser),
            )
            rc = monitorProtectionTask(
                protectionID,
                args.objectType,
                args.app,
                args.background,
                args.pollTimer,
                parser,
            )
            if rc is False:
                raise SystemExit("monitorProtectionTask() failed")
    elif args.objectType == "user":
        # Handle LDAP use cases
        if args.ldap:
            ldapUsers = astraSDK.users.getLdapUsers().main(emailFilter=args.email, matchType="eq")
            if len(ldapUsers["items"]) == 0:
                parser.error(f"0 LDAP users found with email '{args.email}'")
            elif len(ldapUsers["items"]) > 1:
                parser.error(f"multiple LDAP users found with email '{args.email}'")
            args.firstName = ldapUsers["items"][0]["firstName"]
            args.lastName = ldapUsers["items"][0]["lastName"]
            args.ldap = "ldap"
        # First create the user
        urc = astraSDK.users.createUser(quiet=args.quiet, verbose=args.verbose).main(
            args.email, firstName=args.firstName, lastName=args.lastName, authProvider=args.ldap
        )
        if urc:
            # Next create the role binding
            rrc = astraSDK.rolebindings.createRolebinding(
                quiet=args.quiet, verbose=args.verbose
            ).main(
                args.role,
                userID=urc["id"],
                roleConstraints=helpers.createConstraintList(
                    args.namespaceConstraint, args.labelConstraint
                ),
            )
            if rrc:
                # Delete+error "local" users where a tempPassword wasn't provided
                if urc["authProvider"] == "local" and not args.tempPassword:
                    drc = astraSDK.rolebindings.destroyRolebinding(quiet=True).main(rrc["id"])
                    if not drc:
                        raise SystemExit("astraSDK.rolebindings.destroyRolebinding() failed")
                    raise SystemExit("Error: --tempPassword is required for ACC+localAuth")
                # Finally, create the credential if local user
                if urc["authProvider"] == "local":
                    crc = astraSDK.credentials.createCredential(
                        quiet=args.quiet, verbose=args.verbose
                    ).main(
                        urc["id"],
                        "passwordHash",
                        {
                            "cleartext": base64.b64encode(args.tempPassword.encode("utf-8")).decode(
                                "utf-8"
                            ),
                            "change": base64.b64encode("true".encode("utf-8")).decode("utf-8"),
                        },
                    )
                    if not crc:
                        raise SystemExit("astraSDK.credentials.createCredential() failed")
            else:
                raise SystemExit("astraSDK.rolebindings.createRolebinding() failed")
        else:
            raise SystemExit("astraSDK.users.createUser() failed")
