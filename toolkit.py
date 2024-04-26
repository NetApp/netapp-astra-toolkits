#!/usr/bin/env python3
"""
   Copyright 2022 NetApp, Inc

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

import sys

import tkSrc


def main(argv=sys.argv):
    # The various functions to populate the lists used for choices() in the options are
    # expensive. argparse provides no way to know what subcommand was selected prior to
    # parsing the options. By then it's too late to decide which functions to run to
    # populate the various choices the differing options for each subcommand needs. So
    # we just go around argparse's back and inspect sys.argv directly.
    acl = tkSrc.classes.ArgparseChoicesLists()
    ard = tkSrc.classes.AstraResourceDicts()
    plaidMode = False
    v3 = False
    v3_skip_tls_verify = False

    if len(argv) > 1:
        # global_args must manually be kept in sync with __init__() parser args in tkSrc/parser.py
        global_args = [
            "-v",
            "--verbose",
            "-o",
            "--output",
            "-q",
            "--quiet",
            "-f",
            "--fast",
            "--v3",
            "--dry-run",
            "--insecure-skip-tls-verify",
        ]
        # verbs must manually be kept in sync with top_level_commands() in tkSrc/parser.py
        verbs = {
            "deploy": False,
            "clone": False,
            "restore": False,
            "ipr": False,
            "list": False,
            "get": False,
            "create": False,
            "copy": False,
            "manage": False,
            "define": False,
            "destroy": False,
            "unmanage": False,
            "update": False,
        }

        firstverbfoundPosition = None
        verbPosition = None
        cookedlistofVerbs = [x for x in verbs]
        for verb in verbs:
            if verb not in argv:
                # no need to iterate over the arg list for a verb that isn't in there
                continue
            if verbPosition:
                # once we've found the first verb we can stop looking
                break
            for counter, item in enumerate(argv):
                if item == verb:
                    if firstverbfoundPosition is None:
                        # firstverbfoundPosition exists to prevent
                        # "toolkit.py create deploy create deploy" from deciding the second create
                        # is the first verb found
                        firstverbfoundPosition = counter
                    else:
                        if counter > firstverbfoundPosition:
                            continue
                        else:
                            firstverbfoundPosition = counter
                    # Why are we jumping through hoops here to remove the verb we found
                    # from the list of verbs?  Consider the input "toolkit.py deploy deploy"
                    # When we loop over the args we find the first "deploy"
                    # verb["deploy"] gets set to True, we loop over the slice of sys.argv
                    # previous to "deploy" and find no other verbs so verb["deploy"] remains True
                    # Then we find the second deploy.  We loop over the slice of sys.argv previous
                    # to *that* and sure enough, the first "deploy" is in verbs so
                    # verb["deploy"] gets set to False
                    try:
                        cookedlistofVerbs.remove(item)
                    except ValueError:
                        pass
                    verbs[verb] = True
                    verbPosition = counter
                    for item2 in argv[:(counter)]:
                        # argv[:(counter)] is a slice of sys.argv of all the items
                        # before the one we found
                        if item2 in cookedlistofVerbs:
                            # deploy wasn't the verb, it was a symbolic name of an object
                            verbs[verb] = False
                            verbPosition = None

        # Handle plaidMode (-f/--fast) and --v3 use-cases
        for counter, item in enumerate(argv):
            if verbPosition and counter < verbPosition and (item == "-f" or item == "--fast"):
                plaidMode = True
            if ((verbPosition and counter < verbPosition) or (verbPosition is None)) and (
                item == "--v3"
            ):
                v3 = True
                v3Position = counter
            if ((verbPosition and counter < verbPosition) or (verbPosition is None)) and (
                item == "--insecure-skip-tls-verify"
            ):
                v3_skip_tls_verify = True

        # Argparse cares about capitalization, kubectl does not, so transparently fix appvault
        if verbPosition and len(argv) - verbPosition >= 2 and argv[verbPosition + 1] == "appvault":
            argv[verbPosition + 1] = "appVault"
        if verbPosition and len(argv) - verbPosition >= 2 and argv[verbPosition + 1] == "appvaults":
            argv[verbPosition + 1] = "appVaults"

        # Transparently change "protectionpolicy" to "protection" for backwards compatibility
        if (
            verbPosition
            and len(argv) - verbPosition >= 2
            and argv[verbPosition + 1] == "protectionpolicy"
        ):
            argv[verbPosition + 1] = "protection"

        # If v3, build the context@kubeconfig choices list (we want this outside of
        # tkSrc.choices.main as it should be generated regardless of plaidMode)
        if v3:
            v3, verbPosition = tkSrc.choices.kube_config(
                argv, acl, verbPosition, v3Position, global_args
            )

        # Enabling comma separated listing of objects, like:
        # 'toolkit.py list apps,backups,snapshots'
        if (verbs["list"] or verbs["get"]) and len(argv) > (verbPosition + 1):
            if "," in argv[verbPosition + 1]:
                listTypeArray = argv[verbPosition + 1].split(",")
                for lt in listTypeArray:
                    argv[verbPosition + 1] = lt
                    main(argv=argv)
                sys.exit(0)

        # As long as we're not --fast/plaidMode, build the argparse choices lists
        if not plaidMode:
            tkSrc.choices.main(
                argv, verbs, verbPosition, ard, acl, v3, v3_skip_tls_verify=v3_skip_tls_verify
            )

    else:
        raise SystemExit(
            f"{argv[0]}: error: please specify a subcommand. Run '{argv[0]} -h' for "
            "parser information."
        )

    # Manually passing args into argparse via parse_args() shouldn't include the function name
    argv = argv[1:] if "toolkit" in argv[0] else argv
    tkParser = tkSrc.parser.ToolkitParser(acl, plaidMode=plaidMode, v3=v3)
    parser = tkParser.main()
    args = parser.parse_args(args=argv)
    if args.v3:
        v3_dict = {"deploy": ["acp", "chart"]}
        v3_dict.update(
            dict.fromkeys(
                ["create", "destroy"],
                [
                    "backup",
                    "exechok",
                    "hook",
                    "protection",
                    "schedule",
                    "snapshot",
                ],
            )
        )
        v3_dict["destroy"].extend(["credential", "secret"])
        v3_dict.update(dict.fromkeys(["clone", "ipr", "restore"], True))
        v3_dict.update(
            dict.fromkeys(
                ["define", "manage", "unmanage"],
                ["app", "application", "appVault", "bucket", "cluster"],
            )
        )
        v3_dict.update(
            dict.fromkeys(
                ["list", "get"],
                [
                    "apps",
                    "applications",
                    "appVaults",
                    "astraconnectors",
                    "backups",
                    "buckets",
                    "connectors",
                    "credentials",
                    "exechooks",
                    "exechooksruns",
                    "hooks",
                    "hooksruns",
                    "inplacerestores",
                    "iprs",
                    "namespaces",
                    "protections",
                    "restores",
                    "schedules",
                    "secrets",
                    "snapshots",
                ],
            )
        )
        tkSrc.helpers.checkv3Support(args, parser, v3_dict)
    if args.dry_run and not args.v3:
        parser.error("--dry-run can only be used in conjunction with --v3")
    elif args.skip_tls_verify and not args.v3:
        parser.error("--insecure-skip-tls-verify can only be used in conjunction with --v3")

    if args.subcommand == "deploy":
        tkSrc.deploy.main(args, parser, ard)
    elif args.subcommand == "clone" or args.subcommand == "restore":
        tkSrc.clone.main(args, parser, ard)
    elif args.subcommand == "ipr":
        tkSrc.ipr.main(args, parser, ard)
    elif args.subcommand == "list" or args.subcommand == "get":
        tkSrc.list.main(args)
    elif args.subcommand == "copy":
        tkSrc.copy.main(args)
    elif args.subcommand == "create":
        tkSrc.create.main(args, parser, ard)
    elif args.subcommand == "manage" or args.subcommand == "define":
        tkSrc.manage.main(args, parser, ard)
    elif args.subcommand == "destroy":
        tkSrc.destroy.main(args, parser, ard)
    elif args.subcommand == "unmanage":
        tkSrc.unmanage.main(args, parser, ard)
    elif args.subcommand == "update":
        tkSrc.update.main(args, parser, ard)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
