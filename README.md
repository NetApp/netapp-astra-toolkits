# NetApp Astra SDK

Brief introduction to the NetApp Astra SDK, including an overview of how it works and who it's intended to help. No more than 2 paragraphs.

## Installation

Overview of the install process.

### Prerequisites

* Docker and Python installed on your local computer (versions?)
* All the compute clusters exist and are being managed by Astra.

### Install

Set up your kubeconfig to successfully run kubectl commands against your cluster with a command like:

```Shell
export KUBECONFIG=/path/to/kubeconfig
```

Launch the prepared Docker image. Docker will automatically download the image if you don't already have it on your system.

```Shell
sudo docker run -it jpaetzel0614/k8scloudcontrol:1.0 /bin/bash
```
NOTE: From this point forward, you will be working in the Docker container which you just launched. Anything you do from here on will not be saved after you exit Docker. Be sure to take notes and save copies of files elsewhere if necessary.

Clone the NetApp Astra SDK repo.

```Shell
git clone https://github.com/NetApp/netapp-astra-toolkits.git
```
Move into the repo directory.

```Shell
cd netapp-astra-toolkits
```

Edit the `config.yaml` file to reflect your account information.

```Shell
headers:
  Authorization: Bearer [API token]
uid: [Your Astra Account ID]
astra_project: preview
```
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
