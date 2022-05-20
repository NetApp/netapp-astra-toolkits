# Deploy

The {{deploy}} command has the following command syntax:

```bash
./toolkit.py deploy <chartname> <appname> <namespacename>
```

This command will carry out the following operations on your *current kubeconfig context*:

1. Installs the bitnami, gitlab, and cloudbees helm repositories if they're not already installed
1. Updates all the helm repositories (the three listed in step 1, and any user-defined repos)
1. Checks to ensure that \<namespacename\> does not currently exist on the Kubernetes cluster
1. Creates the \<namespacename\> namespace on the Kubernetes cluster
1. Sets the kubeconfig context to utilize the \<namespacename\>
1. Runs a {{helm install}} command deploying \<chartname\> with the name of \<appname\>
1. Waits for Astra Control to discover the newly deployed \<appname\>
1. Has Astra Control manage the newly discovered \<appname\>
1. Creates a basic protection policy for the newly managed \<appname\>

Sample output:

```bash
$ ./toolkit.py deploy artifactory-jcr jfrogcr jfrogcr
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "jfrog" chart repository
...Successfully got an update from the "bitnami" chart repository
...Successfully got an update from the "gitlab" chart repository
...Successfully got an update from the "cloudbees" chart repository
Update Complete. ⎈Happy Helming!⎈
namespace/jfrogcr created
Context "gke_astracontroltoolkitdev_us-west1-b_uswest1-cluster" modified.
NAME: jfrogcr
LAST DEPLOYED: Fri May 20 11:58:49 2022
NAMESPACE: jfrogcr
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Congratulations. You have just deployed JFrog Container Registry!
Waiting for Astra to discover apps..............Discovery complete!
Managing: jfrogcr........Success.
Setting hourly protection policy on cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0
Setting daily protection policy on cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0
Setting weekly protection policy on cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0
Setting monthly protection policy on cbffb71a-a96b-4c13-9d36-e1fbeac8aaa0
```
