import sys
import astraSDK
import getopt

# Define HelpText
helpTextInfo = """
For information on the arguments to be used, use -h or --help.
NetApp DevOps Toolkit file: createBackup.py

createBackup creates the backup of the application managed by Astra Control.

This script requires -a/--application, -c/--cluster and -b/--backup-name parameters to be specified.

Required/Allowed Arguments:
\t-a, --application \t Name of the application whose backup is to be captured.
\t-c, --cluster \t Name of the cluster the application belongs to.
\t-b, --backup-name \t Name of the backup.

Examples:
\t python3 createBackup.py -c cluster-a -a app-a -b backup-10
\t python3 createBackup.py --cluster cluster-1 --application app-1 --backup-name backup-1
"""

argumentList = sys.argv[1:]
options = "ha:c:b:"
long_options = ["help", "application=", "cluster=", "backup-name="]

try:
    arguments, values = getopt.getopt(argumentList, options, long_options)
except getopt.error:
    print("\n--------------------------------------------")
    print("Error: Invalid arguments")
    print("--------------------------------------------")
    print(helpTextInfo)
    sys.exit(0)

print(arguments)
print(values)

for arg, val in arguments:
    if arg in ("-h", "--help"):
        print(helpTextInfo)
        sys.exit(0)
    elif arg in ("-a", "--application"):
        application_name = val
    elif arg in ("-c", "--cluster"):
        cluster_name = val
    elif arg in ("-b", "--backup-name"):
        backup_name = val

try:
    print(application_name + "-" + cluster_name + "-" + backup_name)
except NameError:
    print("\n--------------------------------------------")
    print("Error: All required arguments are not passed")
    print("--------------------------------------------")
    print(helpTextInfo)
    sys.exit(0)

try:
    appGet = astraSDK.getApps().main(cluster=cluster_name, namespace=application_name)

    for i in appGet:
        if appGet[i][0] == application_name:
            print(i)
            appId = i

    backupId = astraSDK.takeBackup().main(appID=appId, backupName=backup_name)
except Exception:
    print("\n----Error----")
    print("Possible Issues: ")
    print("\t1. Astra Control API is not reachable")
    print("\t2. The specified cluster is not managed by Astra Control")
    print("\t3. The specified application is not managed by Astra Control")
    print("\t4. The specified backup name is violating the naming convention")
