# NetApp Astra SDK

Brief introduction to the NetApp Astra SDK, including an overview of how it works and who it's intended to help. No more than 2 paragraphs.

## Installation

The NetApp Astra Toolkit runs in a Docker container. This makes it easy for you to launch and use the Toolkit, because the prepared Docker image has all the dependencies and requirements configured and ready to go.

The Docker container is effectively independent from your desktop computer. This means:

1. You will need to independently authenticate with any relevant services. For example, even if you have authenticated with Google on your desktop computer, you will need to re-authenticate from the Toolkit container in order to use `gcloud` commands.
2. Anything you do on the Toolkit container will not be saved after you exit Docker. Take notes and save copies of files elsewhere if you want to reference them later.

### Prerequisites

* Docker and Python installed on your local computer (versions?)
* All the compute clusters exist and are being managed by Astra.

### Install

Launch the prepared Docker image. Docker will automatically download the image if you don't already have it on your system.

```Shell
sudo docker run -it jpaetzel0614/k8scloudcontrol:1.0 /bin/bash
```

NOTE: From this point forward, you will be working in the Docker container you just launched.

Clone the NetApp Astra SDK repo.

```Shell
git clone https://github.com/NetApp/netapp-astra-toolkits.git
```

Move into the repo directory.

```Shell
cd netapp-astra-toolkits
```

Set up your kubeconfig to successfully run kubectl commands against your cluster with the appropriate command (e.g. `export KUBECONFIG=/path/to/kubeconfig`, `gcloud container clusters get-credentials`, or `az aks get-credentials`).

Edit the `config.yaml` file to add your NetApp Astra account information.

* `Authorization: Bearer`: Your API token
* `uid`: Your Astra Account ID
* `astra_project`: Your Astra instance (`preview` or `demo`)

You can find this information in your NetApp Astra account profile. Click the user icon in the upper right-hand corner, then choose **API Access** from the drop-down menu which appears.

![Locate your Astra profile](./docs/img/astra-profile.png)

Copy and paste your Astra account ID into the `config.yaml` file.

![Locate your Astra account ID](./docs/img/astra-account-info.png)

To get your API token, click **+ Generate API token**. Generate a new API token, then copy and paste the token into the `config.yaml`

When you are done, the `config.yaml` looks like:

```Shell
headers:
  Authorization: Bearer ABCDEFGHI0123456789
uid: 123456789-1234-123456789
astra_project: preview
```

Save and exit the file.

Run the following commands to add the required Python elements:

```Shell
virtualenv toolkit
source toolkit/bin/activate
pip install -r requirements.txt
```

You can now use `./toolkit.py` to invoke the NetApp Astra SDK. For example, list your Astra clusters with the command:

```Shell
./toolkit.py list clusters
```

See [the documentation](./docs) for more info.
