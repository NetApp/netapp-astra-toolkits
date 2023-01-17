# Extending GitOps Patterns to Application Data Protection with NetApp Astra Control

* [Prerequisites](#prerequisites)
* [Argo CD Deployment](#argo-cd-deployment)
* [GitHub Repository Setup](#github-repository-setup)
* [Repository Contents](#repository-contents)
* [Secret Creation](#secret-creation)
* [Argo CD Application Creation](#argo-cd-application-creation)
* [Application Configuration](#application-configuration)
* [Breaking Change](#breaking-change)
* [Application Restoration](#application-restoration)
* [Application Verification](#application-verification)
* [Conclusion](#conclusion)

Many organizations have been extremely successful extending the DevOps operational framework to cover application infrastructure by utilizing git as the single source of truth.  This process has been coined “GitOps” and has a wide array of benefits, including increased productivity, improved security and compliance, increased reliability, and a built-in audit trail.

[Argo CD](https://argoproj.github.io/cd/) is a very popular GitOps tool in the market today, is entirely open source and currently a [CNCF incubating project](https://landscape.cncf.io/?selected=argo).  Argo CD is extremely easy to set up, has a robust built-in GUI, and is great at abstracting the complexities of Kubernetes.  Developers only need to commit code to their git repository, and Argo CD picks up on those changes and automatically syncs them to the relevant infrastructure.

Regardless of where your organization is on their DevOps and GitOps journey, your Kubernetes applications require robust application-aware data protection and disaster recovery like your traditional applications.  [NetApp® Astra™ Control](https://cloud.netapp.com/astra) provides application-aware data protection, mobility, and disaster recovery for any workload running on any Kubernetes distribution. It’s available both as a fully managed service (Astra Control Service) and as self-managed software (Astra Control Center). It enables administrators to easily protect, back up, migrate, and create working clones of Kubernetes applications, through either its UI or robust APIs.

![alt_text](images/00-about-astra.png "NetApp Astra Portfolio")
_NetApp Astra Portfolio_

However manually creating protection policies for these applications after deployment, or manually snapshotting prior to application changes is the antithesis of GitOps.  These policies should instead be defined in our single source of truth, the git repository.  Thankfully with Argo CD and [actoolkit](https://pypi.org/project/actoolkit/) (a python package of the open source [NetApp Astra Toolkits](https://github.com/NetApp/netapp-astra-toolkits)), defining these policies in your git repository is a very simple process.  Read on to find out how!

## Prerequisites

This blog will make use of Argo CD [Resource Hooks](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/) to automatically manage and protect your GitOps-defined applications.  If you’ll be following along step-by-step the following resources are required:

* An [Astra Control Center](https://docs.netapp.com/us-en/astra-control-center/index.html) (ACC; self-managed) or [Astra Control Service](https://docs.netapp.com/us-en/astra-control-service/index.html) (ACS; NetApp-managed service) instance
* Your Astra Control account ID, an [API authorization token](https://docs.netapp.com/us-en/astra-automation/get-started/get_api_token.html#create-an-astra-api-token), and project name (ACS) or FQDN (ACC)
* A [supported](https://docs.netapp.com/us-en/astra-control-service/get-started/supported-deployments.html) Kubernetes cluster (we’ll be using a GKE private cluster in this walkthrough) managed by Astra Control
* A workstation with **git** and **kubectl** installed, kubectl configured to utilize the above Kubernetes cluster, and a GitHub account

If you’re instead just looking for example Argo CD resource hooks that interact with Astra Control, please skip ahead to the [Repository Contents](#repository-contents) section.

## Argo CD Deployment

We’ll be making use of the [getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/) page to deploy Argo CD onto our Kubernetes cluster, but if you already have Argo CD deployed in your environment, skip to the next section.  On your workstation CLI, run the following commands.

```text
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```

These commands should produce a decent amount of output as they create the **argocd** namespace, apply the Argo CD Kubernetes **manifest**, and finally patch the **argocd-server** service type to be a **LoadBalancer** for external access.

After a few moments, we’re ready to grab our access information for Argo CD.  In this blog we’ll be making use of Argo CD’s GUI to concisely present information and to minimize the number of installation dependencies.  However, in production workflows you may want to use [Argo CD's CLI](https://github.com/argoproj/argo-cd/releases/latest).

```text
$ kubectl -n argocd get svc argocd-server
NAME            TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)                      AGE
argocd-server   LoadBalancer   172.17.51.56   34.67.62.165   80:30529/TCP,443:30593/TCP   7m8s
$ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
lXMAleZ95RDhMtpo
```

Copy the **external IP** value from the output of the first command and paste it into your web browser.  Then **sign in** with the username **admin** and the password copied from the output of the second command.

![alt_text](images/01-argocd-signin.png "Argo CD Sign In")
_Argo CD Sign In_

Now that we have Argo CD installed, it’s time to set up our demo GitHub repository.

## GitHub Repository Setup

Rather than following the (stateless) example application within the [getting started page](https://argo-cd.readthedocs.io/en/stable/getting_started/#6-create-an-application-from-a-git-repository) of the Argo CD documentation, we’ll be utilizing a stateful WordPress application, based on the classic [kubernetes.io example](https://kubernetes.io/docs/tutorials/stateful-application/mysql-wordpress-persistent-volume/).  We’ll be making several changes to the Kubernetes YAML through git commits, so we’ll use a [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) to provide write access.

In your web browser, navigate to the [MichaelHaigh/argocd-astra-demo](https://github.com/MichaelHaigh/argocd-astra-demo) repository on GitHub, and then click the **fork** button in the upper right corner.

![alt_text](images/02-fork-repo-button.png "Argo CD Astra Control Demo Repository")
_Argo CD Astra Control Demo Repository_

Select your **username** as the **owner**, leave the repository name as **argocd-astra-demo**, optionally leave the description as-is, and then click **create fork**.

![alt_text](images/03-fork-repo.png "Create New Fork")
_Create New Fork_

In your workstation CLI, clone the repository (be sure to update the username) and change into the new directory.

```text
git clone https://github.com/<YourUsername>/argocd-astra-demo.git
cd argocd-astra-demo
```

Now that our git repository is up and running, let’s investigate the YAML files within the repo.

## Repository Contents

Within the **wordpress/** directory of our repo, you’ll find four Kubernetes YAML files.  The first two files define a demo Kubernetes Wordpress application, and the second two files define Argo CD resource hooks which automate protection policies with Astra Control:

* **wordpress.yaml**: this file contains the frontend of the Wordpress application, including:
  * A **service** of type **LoadBalancer**
  * A **persistent volume claim** with an access mode of **ReadWriteMany**
  * A **deployment** with 2 replicas of the wordpress:4.8-apache container image
* **mysql.yaml**: this file contains the backend of the Wordpress application, including:
  * A **service** of type **ClusterIP**
  * A **persistent volume claim** with an access mode of **ReadWriteOnce**
  * A **deployment** with 2 replicas of the mysql:5.6 container image
* **postsync-hook.yaml**: a Kubernetes **Job** which defines an [Argo CD resource hook](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/), and is run _a single time after_ the application _initially_ syncs
* **presync-hook.yaml**: a Kubernetes **Job** which defines another resource hook, and runs _every time prior_ to the application syncing

The Wordpress and MySQL definitions should be quite straightforward, but let’s investigate the Argo CD resource hooks in greater detail.  Here’s the entire contents of the PostSync hook for posterity:

```text
apiVersion: batch/v1
kind: Job
metadata:
  name: astra-manage-app
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookFailed
spec:
  template:
    spec:
      volumes:
        - name: astra-control-config
          secret:
            secretName: astra-control-config
      containers:
      - name: alpine-actoolkit
        image: alpine:latest
        command: ["/bin/sh"]
        args:
        - -c
        - >
          APPNAME=wordpress-argocd &&
          NAMESPACE=wordpress &&
          apk add py3-pip jq &&
          python3 -m pip install --upgrade pip &&
          python3 -m pip install actoolkit==2.4.0 &&
          for i in `actoolkit -o json list namespaces -m 120 -f $NAMESPACE | jq -r '.items[].clusterID'`;
          do
            echo actoolkit: managing app $APPNAME in namespace $NAMESPACE on cluster $i;
            actoolkit manage app $APPNAME $NAMESPACE $i;
            sleep 5;
          done &&
          for j in `actoolkit -o json list apps -f $APPNAME | jq -r '.items[].id'`;
          do
            echo actoolkit: creating protection policy for $APPNAME / $j;
            actoolkit create protection $j -g hourly  -m 0      -b 1 -s 1;
            actoolkit create protection $j -g daily   -H 0      -b 2 -s 2;
            actoolkit create protection $j -g weekly  -H 0 -W 1 -b 2 -s 2;
            actoolkit create protection $j -g monthly -H 0 -M 1 -b 2 -s 2;
          done
        volumeMounts:
          - mountPath: /etc/astra-toolkits
            name: astra-control-config
            readOnly: true
      restartPolicy: Never
  backoffLimit: 1
```

Let’s dive into this hook in greater detail.  The beginning of the file defines the kind and metadata:

```text
kind: Job
metadata:
  name: astra-manage-app
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookFailed
```

Argo CD resource hooks can be _any_ type of Kubernetes resource; however they typically are either pods, jobs, or Argo Workflows.  Both our hooks are Kubernetes [jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/).  The metadata section has three key components:

* A **[name](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/#generate-name)** is defined, rather than **generateName**, which in conjunction with the delete policy means the hook will only run a single time if successful
* It’s a **[PostSync](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/#usage)** hook, meaning it runs after the application completes a sync, and all resource are in a healthy state
* The [delete policy](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/#hook-deletion-policies) is **HookFailed**, which means the hook is only deleted in the event of a failure, and in conjunction with the name definition means it’ll only run a single time

At the beginning and the end of the **spec** definition there are volume and volume mount definitions:

```text
spec:
  template:
    spec:
      volumes:
        - name: astra-control-config
          secret:
            secretName: astra-control-config
      containers:
      ...
        volumeMounts:
          - mountPath: /etc/astra-toolkits
            name: astra-control-config
            readOnly: true
```

This references a Kubernetes secret that we’ll be creating momentarily, which contains the account ID, API token, and name/FQDN of your Astra Control instance mentioned in the prerequisites section.  It mounts the secret to **/etc/astra-toolkits** which is [one of the directories](../../docs/astrasdk/common#getconfig) that the [Astra Control toolkit](https://github.com/NetApp/netapp-astra-toolkits) reads from.

Finally, we have the main container definition:

```text
     containers:
      - name: alpine-actoolkit
        image: alpine:latest
        command: ["/bin/sh"]
        args:
        - -c
        - >
          APPNAME=wordpress-argocd &&
          NAMESPACE=wordpress &&
          apk add py3-pip jq &&
          python3 -m pip install --upgrade pip &&
          python3 -m pip install actoolkit==2.4.0 &&
          for i in `actoolkit -o json list namespaces -m 120 -f $NAMESPACE | jq -r '.items[].clusterID'`;
          do
            echo actoolkit: managing app $APPNAME in namespace $NAMESPACE on cluster $i;
            actoolkit manage app $APPNAME $NAMESPACE $i;
            sleep 5;
          done &&
          for j in `actoolkit -o json list apps -f $APPNAME | jq -r '.items[].id'`;
          do
            echo actoolkit: creating protection policy for $APPNAME / $j;
            actoolkit create protection $j -g hourly  -m 0      -b 1 -s 1;
            actoolkit create protection $j -g daily   -H 0      -b 2 -s 2;
            actoolkit create protection $j -g weekly  -H 0 -W 1 -b 2 -s 2;
            actoolkit create protection $j -g monthly -H 0 -M 1 -b 2 -s 2;
          done
```

* Prints the app name, namespace name, and cluster ID that’s about to be managed to standard out for easy confirmation when viewing container logs
* Runs a [manage app](https://github.com/NetApp/netapp-astra-toolkits/tree/main/docs/toolkit/manage#app) command with actoolkit
* Sleeps for 5 seconds
* Instantiates a for loop based on the UUID gathered from a list apps command that has a filter to only view apps with the name $APPNAME (wordpress-argocd)
* Prints a notification about the protection policy being created
* Runs four [create protection](https://github.com/NetApp/netapp-astra-toolkits/tree/main/docs/toolkit/create#protection) commands with actoolkit to create an hourly, daily, weekly, and monthly protection policy

In summary, our PostSync hook only runs a single time after the initial application sync and utilizes the Astra Control toolkit to manage and create a protection policy for the freshly deployed application.

Next up we have our PreSync resource hook:

```text
apiVersion: batch/v1
kind: Job
metadata:
  generateName: presync-astra-snapshot-
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  template:
    spec:
      volumes:
        - name: astra-control-config
          secret:
            secretName: astra-control-config
      containers:
      - name: alpine-actoolkit
        image: alpine:latest
        command: ["/bin/sh"]
        args:
        - -c
        - >
          APPNAME=wordpress-argocd &&
          apk add py3-pip jq &&
          python3 -m pip install --upgrade pip &&
          python3 -m pip install actoolkit==2.4.0 &&
          for i in `actoolkit -o json list apps -f $APPNAME | jq -r '.items[].id'`;
          do
            echo actoolkit: snapshotting app $APPNAME / $i;
            actoolkit create snapshot $i argo-presync-`date "+%Y%m%d%H%M%S"`;
          done
        volumeMounts:
          - mountPath: /etc/astra-toolkits
            name: astra-control-config
            readOnly: true
      restartPolicy: Never
  backoffLimit: 1
```

The PreSync hook is very similar to the PostSync hook, with a couple of key differences.  First, the metadata section:

```text
metadata:
  generateName: presync-astra-snapshot-
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
```

* A **generateName** field is used, which means the hook will run each time the application syncs
* It’s a PreSync hook, which means the hook will run _prior_ to any other action during an application sync
* The delete policy is **BeforeHookCreation**, which means the previous hook will only be deleted just before next hook is ran, which means it will stay present in the application history until the next sync

The command section is also very similar, but a couple of key differences:

```text
          for i in `actoolkit -o json list apps -f $APPNAME | jq -r '.items[].id'`;
          do
            echo actoolkit: snapshotting app $APPNAME / $i;
            actoolkit create snapshot $i argo-presync-`date "+%Y%m%d%H%M%S"`;
          done
```

* There is only a single for loop that iterates over the app UUID returned from a list apps command with a filter based on the name $APPNAME (wordpress-argocd)
* A snapshot is created with a name that starts with **argo-presync-** and then ends with a timestamp

In summary, our PreSync hook runs every time prior to an application sync, and snapshots the application.  In conjunction with the PostSync hook, our application will be automatically managed by Astra Control, and snapshotted prior to every change, enabling easy application restores in the event of a destructive change.

## Secret Creation

Argo CD is [unopinionated](https://argo-cd.readthedocs.io/en/stable/operator-manual/secret-management/) on secret management, enabling administrators to utilize the secret manager of their choice through a wide range of integrations.  If you’re using Argo CD in production, it is **highly recommended** to make use of one of the supported secret management tools.

Since this demo is focused on resource hooks and automatic application data protection, we’re going to sidestep requiring setup and configuration of a secret manager.  However, it’s a bad practice to put secrets into a git repository (production or not), so we’ll manually define our secrets outside of Argo CD and apply them through **kubectl**.

We’ll first create our Astra Control API config file as described earlier.  Run the following commands, but be sure to substitute in your Astra Control account ID, [API authorization token](https://docs.netapp.com/us-en/astra-automation/get-started/get_api_token.html#create-an-astra-api-token), and project name.  If you’re not sure of these values, additional information can be found in the [authentication section of the main readme](../../README.md##authentication) page on GitHub.

```text
API_TOKEN=NL1bSP5712pFCUvoBUOi2JX4xUKVVtHpW6fJMo0bRa8=
ACCOUNT_ID=12345678-abcd-4efg-1234-567890abcdef
ASTRA_PROJECT=astra.netapp.io
cat <<EOF > config.yaml
headers:
  Authorization: Bearer $API_TOKEN
uid: $ACCOUNT_ID
astra_project: $ASTRA_PROJECT
EOF
```

If done correctly, your config.yaml file should look like this:

```text
$ cat config.yaml 
headers:
  Authorization: Bearer NL1bSP5712pFCUvoBUOi2JX4xUKVVtHpW6fJMo0bRa8=
uid: 12345678-abcd-4efg-1234-567890abcdef
astra_project: astra.netapp.io
```

Next, we’re going to create our MySQL database password, which can be any value you desire.

```text
MYSQL_PASSWORD=$(echo -n "ChangeToAnythingYouWant" | base64)
cat <<EOF >mysql-password.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-password
  namespace: wordpress
  labels:
    app: wordpress
type: Opaque
data:
  password: $MYSQL_PASSWORD
EOF
```

Finally, we’ll create our Kubernetes namespace and apply the two secret files we just created.

```text
kubectl create namespace wordpress
kubectl -n wordpress create secret generic astra-control-config --from-file=config.yaml
kubectl -n wordpress apply -f mysql-password.yaml
```

Ensure that you receive responses about the namespace and the two secrets being created, and then move on to the next section where we define our Argo CD application.

## Argo CD Application Creation

Now that we have Argo CD, GitHub repository, and secrets created, we’re ready to deploy our demo wordpress application.  Head back to your browser and click the **create application** button in the middle of the Argo CD user interface.

![alt_text](images/04-create-application-button.png "Create Application")
_Create Application_

In the wizard panel that appears, click the **edit as YAML** button in the upper right, which will allow us to easily paste in our application definition.

![alt_text](images/05-edit-as-yaml.png "Edit as YAML")
_Edit as YAML_

Copy the following application definition and paste it into the browser text field.

```text
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: wordpress-demo
spec:
  destination:
    name: ''
    namespace: wordpress
    server: 'https://kubernetes.default.svc'
  source:
    path: wordpress
    repoURL: 'https://github.com/<YourUsername>/argocd-astra-demo'
    targetRevision: HEAD
  project: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Edit the **repoURL** to point at the GitHub repository you created earlier, and then click **save** in the upper right corner.

![alt_text](images/06-paste-in-yaml.png "Paste in YAML")
_Paste in YAML_

We can now verify that the fields within the application definition have been filled out via the YAML file, including our general info (name, project, sync options), the application source info (repo URL, branch information, and folder / path information), and destination info (the same Kubernetes cluster that’s running Argo CD).  After verification, click **create** at the top.

![alt_text](images/07-app-definition.png "Application Definition")
_Application Definition_

Argo CD will now have a **wordpress-demo** tile on the main application page.  **Click on the tile** to view the application in detail.

![alt_text](images/08-application-tile.png "wordpress-demo Application Tile")
_wordpress-demo Application Tile_

We should see our application status as **OutofSync** and in a **Syncing** state.  Since we have a PreSync hook defined, this will be the first thing that is run.  However as detailed earlier, the for loop within the PreSync hook is only looking for managed applications, and since our app is not managed yet this hook will not take any real action this first time.

![alt_text](images/09-initial-presync-hook.png "Initial PreSync Hook")
_Initial PreSync Hook_

After a few more moments, the PreSync hook will “complete,” and the rest of the application will begin deployment.  The status of most objects should turn green, with the Wordpress and MySQL pods taking the longest.

![alt_text](images/10-app-deployment.png "Application Deployment")
_Application Deployment_

After a couple of minutes, all the Wordpress Kubernetes resources should be in a healthy state, and the **astra-manage-app** PostSync hook should appear.  Click on the **pod tile** that’s associated with the **astra-manage-app** job to expand the info.

![alt_text](images/11-manage-app-hook.png "Manage App PostSync Hook")
_Manage App PostSync Hook_

In the pod summary panel that appears, click on the **logs** tab.

![alt_text](images/12-postsync-summary-panel.png "PostSync Pod Summary Panel")
_PostSync Pod Summary Panel_

Click the **follow** button to “tail” the pod logs and **wrap lines** so we do not need to scroll to the right.

![alt_text](images/13-follow-logs.png "Follow Logs and Wrap Lines")
_Follow Logs and Wrap Lines_

Scroll down to the bottom of the log output, and after a few moments you should see the output from the PostSync script stating that the application is being managed, and the protection policies being created.

![alt_text](images/14-app-managed.png "App Successfully Managed")
_App Successfully Managed_

Close out the pod detail panel, and you should see the application is in a **healthy**, **synced**, and **sync ok** state.  At this point there are no further actions for Argo CD to take, other than monitoring the git repository for any future changes.

![alt_text](images/15-app-health-synced.png "App Healthy and Synced")
_App Healthy and Synced_

Head over to your terminal, and we can see our Wordpress pods are in a **running** state, and the two hook pods are in a **completed** state, as expected.

```text
$ kubectl -n wordpress get pods
NAME                                                      READY   STATUS      RESTARTS   AGE
astra-manage-app-pqzwv                                    0/1     Completed   0          2m27s
presync-astra-snapshot-bb0f857-presync-1657045438-x68tc   0/1     Completed   0          6m54s
wordpress-7c8df9ddfd-vvt2b                                1/1     Running     2          6m15s
wordpress-7c8df9ddfd-z66lt                                1/1     Running     2          6m15s
wordpress-mysql-79b869cf9d-f4pss                          1/1     Running     0          6m15s
```

Now that our application has been deployed by Argo CD and managed by Astra Control, let’s proceed with the initial Wordpress setup.

## Application Configuration

The Wordpress application by Argo CD is unconfigured to start, so let’s go ahead and set it up.  We can access the site by getting the **external-IP** of the **Wordpress LoadBalancer** service via kubectl.

```text
$ kubectl -n wordpress get svc 
NAME              TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)        AGE
wordpress         LoadBalancer   172.17.214.39   34.71.14.151   80:30094/TCP   11m
wordpress-mysql   ClusterIP      None            <none>         3306/TCP       11m
```

Copy and paste that IP into your web browser, where you’ll be presented with a page allowing you to choose your preferred language.  Once you’ve made your selection, click **continue**.

![alt_text](images/16-wordpress-language.png "Wordpress Language Setup")
_Wordpress Language Setup_

Next, you’ll need to create a **site title** (we’re using **GitOps with Astra Control**), a **username**, **password**, and enter in your **email address**.  Click **install Wordpress** once complete.

 \
![alt_text](images/17-wordpress-information.png "Wordpress Installation Process")
_Wordpress Installation Process_

After a couple of minutes, Wordpress will have finished its setup, and you’ll be presented with the following page.

![alt_text](images/18-wordpress-setup-complete.png "Wordpress Setup Complete")
_Wordpress Setup Complete_

Feel free to log in and make any site modifications, if desired.  When complete, move on to the next section where we’ll see PreSync hooks in action after pushing a change to our git repository.

## Breaking Change

Our next step is to see the PreSync hook in action, which we’ll do by pushing a change to our git repository.  Argo CD will notice the change, run our PreSync hook, and then sync the application state.  Rather than a simple application update however, we’re going to introduce a breaking change by “accidentally” deleting the MySQL definition to see how Astra Control can easily recover from these situations.

Please note that in a production environment, these types of drastic changes are unlikely to make it past the review process, however smaller, harder-to-detect changes can still have drastic consequences where data protection is required to recover the application.

In your terminal, ensure you’re still in the **argocd-astra-demo** project root, then remove the **mysql.yaml** file from the **wordpress/** directory, and add the **wordpress** directory to our commit list.

```text
mv wordpress/mysql.yaml .
git add wordpress/
```

If done correctly, running a **git status** should show our deleted file ready to be committed, and several untracked files, which we will _not_ commit.

```text
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
    deleted:    wordpress/mysql.yaml

Untracked files:
  (use "git add <file>..." to include in what will be committed)
    config.yaml
    mysql.yaml
    mysql-password.yaml
```

Finally, we’ll **commit** and **push** our changes.

```text
git commit -m '"accidental" mysql delete'
git push
```

In your browser window, monitor the Argo CD application page for any changes.  By default, Argo CD polls the git repository every 3 minutes, so that’s the maximum amount of time you’ll need to wait.  You should eventually see a new **presync-astra-snapshot** job created with its underlying pod.  Click on the **pod tile** to open the detailed panel.

![alt_text](images/19-presync-snapshot.png "PreSync Hook Application Snapshot")
_PreSync Hook Application Snapshot_

Click on the **logs** tab and scroll to the bottom.  You should eventually see some output indicating that a **snapshot** of our **wordpress** application is starting, and then confirmation that the snapshot is **complete**.

![alt_text](images/20-snapshot-complete.png "Application Snapshot Complete")
_Application Snapshot Complete_

**Close out** the pod detail panel to view the main application page.  You should see the MySQL resources in the process of removal.

![alt_text](images/21-mysql-resource-removal.png "MySQL Resource Removal")
_MySQL Resource Removal_

After just a few more moments, all the MySQL resources should be gone.

![alt_text](images/22-mysql-resources-gone.png "MySQL Resources Removed")
_MySQL Resources Removed_

Head over to your **Wordpress** browser tab and **refresh** the page.  You should see a notification about the application being unable to establish a database connection.

![alt_text](images/23-database-error.png "Error Establishing Database Connection")
_Error Establishing Database Connection_

Now that we’ve pushed a breaking application change, it’s time to recover our application with Astra Control.

## Application Restoration

We’ve now deployed our application through Argo CD and pushed a change to our git repository which broke the application.  Thankfully our PreSync hook that ran prior to the MySQL resource removal created an application snapshot with Astra Control.  We’ll use this snapshot to restore our Wordpress application to a working state.

First, we’ll need to pause automatic application updates with Argo CD, otherwise it and Astra Control will interfere with one another.  Head back into the Argo CD user interface and click the **app details** button.

![alt_text](images/24-app-details.png "Argo CD App Details")
_Argo CD App Details_

Scroll down to the bottom of the details panel, and click the **disable auto-sync** button.

![alt_text](images/25-disable-autosync-button.png "Disable Auto-Sync Button")
_Disable Auto-Sync Button_

In the confirmation pop-up, click **ok** to disable auto-sync.

![alt_text](images/26-disable-autosync-confirmation.png "Disable Auto-Sync Confirmation")
_Disable Auto-Sync Confirmation_

Next, login to your **Astra Control** environment, and head over to the **applications** page.  You should see our wordpress application in the **managed** section due to the Argo CD PostSync resource hook.  Click on the **wordpress** link to open the detailed application page.

![alt_text](images/27-astra-applications.png "Astra Control Applications")
_Astra Control Applications_

Navigate to the **data protection** tab, and then the **snapshots** section.  Take note of the **argo-presync-20220706131228** snapshot that’s present due to our PreSync resource hook.

![alt_text](images/28-astra-presync-snapshot.png "Argo CD PreSync Hook Snapshot")
_Argo CD PreSync Hook Snapshot_

In the **actions** dropdown in the upper right corner, click the **restore** button.

![alt_text](images/29-astra-actions.png "Astra Control Application Actions")
_Astra Control Application Actions_

In the wizard that appears, **select** the **argo-presync-_timestamp_** snapshot from earlier, and then click **next**.

![alt_text](images/30-restore-app-step-1.png "Restore Application Step 1/2")
_Restore Application Step 1/2_

Take note of the warning that with an in-place restore, all existing application resources will be replaced.  Depending on your use case you may want to restore into a different namespace, however in our case an in-place restore is ideal.  Type **restore** in the confirmation text box and then click **restore**.

![alt_text](images/31-restore-app-step-2.png "Restore Application Step 2/2")
_Restore Application Step 2/2_

Back within the **applications** section of Astra Control, take note that our app is in a **restoring** state.

![alt_text](images/32-app-restoring.png "Application Restoring")
_Application Restoring_

While we’re waiting for the application to restore, let’s fix the issue within our git repository.  Run the following two commands to move the MySQL file back into our wordpress directory and add it to our commit list.

```text
mv mysql.yaml wordpress/.
git add wordpress/
```

 Running **git status** should show the following output.

```text
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
    new file:   wordpress/mysql.yaml

Untracked files:
  (use "git add <file>..." to include in what will be committed)
    config.yaml
    mysql-password.yaml
```

Finally, run the following two commands to create and push our commit to the git repository.

```text
git commit -m 'restoring mysql'
git push
```

Back in the Astra Control user interface, we see our application restore has completed, and it’s now in a **healthy** state.

![alt_text](images/33-app-healthy.png "Application Healthy")
_Application Healthy_

All that’s left to do is to verify we can access our restored Wordpress application, which we’ll do in the next section.

## Application Verification

As mentioned earlier, an in-place restore on Astra Control replaces all Kubernetes resources, so the Wordpress LoadBalancer may have a new IP address (in a production environment you would simply update DNS to point at a new IP).  Head over to your terminal to verify the IP address, and while we’re there we’ll also view the status of our pods and persistent volume claims.

```text
$ kubectl -n wordpress get svc
NAME              TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)        AGE
wordpress         LoadBalancer   172.17.174.187   34.72.191.21   80:31093/TCP   11m
wordpress-mysql   ClusterIP      None             <none>         3306/TCP       11m
$ kubectl -n wordpress get pods
NAME                                                      READY   STATUS      RESTARTS   AGE
astra-manage-app-pqzwv                                    0/1     Completed   0          11m
presync-astra-snapshot-eeca751-presync-1657113114-ql29z   0/1     Completed   0          11m
wordpress-69956d79d-4vrx2                                 1/1     Running     0          11m
wordpress-69956d79d-qrbv6                                 1/1     Running     0          11m
wordpress-mysql-79b869cf9d-hnnxk                          1/1     Running     0          11m
$ kubectl -n wordpress get pvc
NAME             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS               AGE
mysql-pv-claim   Bound    pvc-2fee9dc0-8b45-4dc6-945a-e932808a2cd0   100Gi      RWO            netapp-cvs-perf-standard   13m
wp-pv-claim      Bound    pvc-2ea31e6e-ecbb-4a15-89be-ed635b929676   100Gi      RWX            netapp-cvs-perf-standard   13m
```

We see our new volume claims are bound, our pods are running, and we have a new external IP address.  Paste that address into your browser window, and you should be greeted with our fully functional Wordpress application.  You can even log in with the credentials we created earlier if you append **/admin** to the IP address.

![alt_text](images/34-site-functional.png "Wordpress Application Running")
_Wordpress Application Running_

The only step we have remaining is to reenable auto-sync within Argo CD.  Head back into the Argo CD user interface, and click the **app details** button as before, and then in the panel click **enable auto-sync**.

![alt_text](images/35-enable-autosync.png "Reenable Auto-Sync")
_Reenable Auto-Sync_

In the confirmation pop-up, click **ok**.

![alt_text](images/36-verify-enable-autosync.png "Reenable Auto-Sync Confirmation")
_Reenable Auto-Sync Confirmation_

We’ll also want to reenable **prune resources** by clicking **enable** and then **ok** in the pop-up.

![alt_text](images/37-enable-prune-resources.png "Reenable Prune Resources")
_Reenable Prune Resources_

Repeat the same process for **self heal** by clicking **enable** and then **ok** in the pop-up.

![alt_text](images/38-enable-selfheal.png "Reenable Self Heal")
_Reenable Self Heal_

After a few moments, our Wordpress application should begin synchronizing within Argo CD.  Once complete, it’ll be in a **healthy** and **synced** state.

![alt_text](images/39-application-synched.png "Application Synced")
_Application Synced_

## Conclusion

Whether you’re currently exploring GitOps for its benefits with productivity, security, compliance, and reliability, or you’re a seasoned GitOps practitioner, you likely understand that enterprise-grade disaster recovery is vital regardless of the application’s deployment model.  You should also understand that it’s not necessary to sacrifice the benefits of GitOps to achieve these DR requirements.

NetApp Astra Control provides robust application-aware disaster recovery for all types of Kubernetes applications and can easily adhere to GitOps principles by storing application protection policies within the git repository.  In this blog we took the following actions to achieve GitOps-based application DR:

* Deployed Argo CD by utilizing their [getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/) page
* Cloned the [MichaelHaigh/argocd-astra-demo](https://github.com/MichaelHaigh/argocd-astra-demo/) repository
* Covered the contents of the application YAML and the Argo CD resource hooks
* Created our secrets outside of Argo CD (never put secrets in a git repo!)
* Deployed our Wordpress application via Argo CD
* Configured our application
* Committed a breaking change to our git repo
* Restored our Wordpress application from an automated PreSync hook snapshot
* Validated our restored application was fully functional

If you’re looking to make use of Argo CD resource hooks in conjunction with Astra Control for a unique use case, the most critical component to understand are the [PreSync](https://github.com/MichaelHaigh/argocd-astra-demo/blob/main/wordpress/presync-hook.yaml) and [PostSync](https://github.com/MichaelHaigh/argocd-astra-demo/blob/main/wordpress/postsync-hook.yaml) resource hooks, in particular the **for loops** within the **args** section of the container spec.  If you’re looking for more information on how to construct these commands, please see the [toolkit documentation](../../docs#toolkit-functions), specifically the [json section](https://github.com/NetApp/netapp-astra-toolkits/tree/main/docs/toolkit/optionalargs#json) in the optional arguments page.

Thanks for reading!
