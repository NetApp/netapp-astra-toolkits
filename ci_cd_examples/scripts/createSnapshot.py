import sys
import astraSDK
import getopt

# Define HelpText
helpTextInfo = """
For information on the arguments to be used, use -h or --help.
NetApp DevOps Toolkit file: createSnapshot.py

createSnapshot creates the Snapshot of the application managed by Astra Control.

This script requires -a/--application, -c/--cluster & -s/--snapshot-name parameters to be specified.

Required/Allowed Arguments:
\t-a, --application \t Name of the application whose Snapshot is to be captured.
\t-c, --cluster \t Name of the cluster the application belongs to.
\t-s, --snapshot-name \t Name of the Snapshot.

Examples:
\t python3 createSnapshot.py -c cluster-a -a app-a -s snap-10
\t python3 createSnapshot.py --cluster cluster-1 --application app-1 --snapshot-name snap-1
"""

argumentList = sys.argv[1:]
options = "hacs"
long_options = ["help", "application", "cluster", "snapshot-name"]

try:
    arguments, values = getopt.getopt(argumentList, options, long_options)
except getopt.error:
    print("\n--------------------------------------------")
    print("Error: Invalid arguments")
    print("--------------------------------------------")
    print(helpTextInfo)
    sys.exit(0)

for arg, val in arguments:
    if arg in ("-h", "--help"):
        print(helpTextInfo)
        sys.exit(0)
    elif arg in ("-a", "--application"):
        application_name = val
    elif arg in ("-c", "--cluster"):
        cluster_name = val
    elif arg in ("-s", "--snapshot-name"):
        snapshot_name = val

try:
    print(application_name + "-" + cluster_name + "-" + snapshot_name)
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

    snapId = astraSDK.takeSnap().main(appID=appId, snapName=snapshot_name)
except Exception:
    print("\n----Error----")
    print("Possible Issues: ")
    print("\t1. Astra Control API is not reachable")
    print("\t2. The specified cluster is not managed by Astra Control")
    print("\t3. The specified application is not managed by Astra Control")
    print("\t4. The specified Snapshot name is violating the naming convention")
