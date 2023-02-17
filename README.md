# NetApp Astra Control Python SDK

The NetApp Astra Control Python SDK is designed to provide guidance for working with the NetApp Astra Control API.

You can use the `astraSDK/` library out of the box, and as a set of example recommended code and processes, "cookbook" style. The `toolkit.py` script provides a command line interface to interact with Astra Control with built-in guardrails, and since it utilizes `astraSDK/` it can provide additional context around the requirements of the astraSDK classes.

![Astra SDK Component and Installation Diagram](/docs/install/img/components-install.png)

When using `toolkit.py`/`actoolkit` in automation, it is **highly** recommended to tie your workflows to a specific [tag](https://github.com/NetApp/netapp-astra-toolkits/tags) or [release](https://pypi.org/project/actoolkit/#history) (as functionality may change over time), and be sure to thoroughly test all workflows to ensure expected behavior.

> **Note**: Support for all components of the Astra Control Python SDK is exclusively handled in a best effort fashion by the **community** via [GitHub issues](https://github.com/NetApp/netapp-astra-toolkits/issues), and is **not** supported by NetApp Support. Use of this SDK is entirely at your own risk.

## Installation

The NetApp Astra Control SDK can be utilized three different ways, depending upon your use case:

1. **Administrator**: if you want to use the toolkit as quickly as possible without modifications, it is recommended to utilize the [prepared Docker image](#1-docker-installation), as it has all of the required dependencies and binaries configured and ready to go (including `actoolkit`).
1. **DevOps / GitOps**: if utilizing the toolkit in a software pipeline, the [python package](#2-python-package-installation) ([actoolkit](https://pypi.org/project/actoolkit/)) is *typically* the most straightforward method of consumption. A simple `pip install` command results in toolkit.py (as `actoolkit`) being available in the user's PATH and all python-related dependencies installed.  It also installs the `astraSDK/` library for use in custom scripts.
1. **Developer**: if you plan to modify the SDK for internal consumption, [manual installation](#3-manual-installation) is recommended by cloning (or forking) this repository and working in your local development environment. Ensure that all dependencies mentioned below are met.

This [Python SDK Installation video](https://www.youtube.com/watch?v=r6lBQ2I7O7M) walks through all three use cases / installation methods.

### Prerequisites

For the **administrator** use case with the [prepared Docker image](#1-docker-installation):

* Docker 20.10.7+

For the **DevOps / GitOps** use case with the [python package](#2-python-package-installation) ([actoolkit](https://pypi.org/project/actoolkit/)):

* Python 3.8+
* Pip 21.1.2+

For the **developer** use case or to [manually install](#3-manual-installation) the NetApp Astra Control SDK:

* Python 3.8+
* Pip 21.1.2+
* Virtualenv 20.4.7+
* Git 2.30.2+
* Kubectl 1.17+
* Azure CLI (`az`) 2.25.0+ or Google Cloud SDK (`gcloud`) 345.0.0+ or AWS CLI (`aws`) 1.22.0+
* Helm 3.2.1+

### Authentication

No matter the method of installation, the SDK authenticates by reading in the `config.yaml` file from the following locations (in order):

1. The directory that the executed function is located in
1. `~/.config/astra-toolkits/`
1. `/etc/astra-toolkits/`
1. The directory pointed to by the shell env var `ASTRATOOLKITS_CONF`

Again, no matter the method of installation, the `config.yaml` file should have the following syntax:

```text
headers:
  Authorization: Bearer <Bearer-Token-From-API-Access-Page>
uid: <Account-ID-From-API-Access-Page>
astra_project: <Shortname-or-FQDN>
verifySSL: <True-or-False>
```

This [Astra Control API Credentials](https://www.youtube.com/watch?v=o-q-q_41A5A) video walks through creating the `config.yaml` file, or follow the instructions below.

Create (if using `actoolkit`) or edit (if using the git repo) the `config.yaml` file in one of the above mentioned locations with your NetApp Astra Control account information:

* `Authorization: Bearer`: Your API token
* `uid`: Your Astra Control Account ID
* `astra_project`: Your Astra Control instance (shortnames get astra.netapp.io appended to them, FQDNs [anything with a `.`] are used unchanged)
* `verifySSL`: True or False, useful for self-signed certs (if this field isn't included it's treated as True)

You can find this information in your NetApp Astra Control account profile. Click the user icon in the upper right-hand corner, then choose **API Access** from the drop-down menu which appears.

![Locate your Astra Control profile](/docs/install/img/astra-profile.png)

Copy and paste your Astra Control account ID into the `config.yaml` file.

![Locate your Astra Control account ID](/docs/install/img/astra-account-info.png)

To get your API token, click **+ Generate API token**. Generate a new API token, then copy and paste the token into the `config.yaml`

When you are done, the `config.yaml` looks like:

```text
headers:
  Authorization: Bearer thisIsJustAnExample_token-replaceWithYours==
uid: 12345678-abcd-4efg-1234-567890abcdef
astra_project: astra.netapp.io
verifySSL: True
```

### 1. Docker Installation

Launch the prepared Docker image. Docker will automatically download the image if you don't already have it on your system.

```text
docker run -it netapp/astra-toolkits:2.6.1 /bin/bash
```

NOTE: From this point forward, you will be working in the Docker container you just launched.

Set up your kubeconfig to successfully run kubectl commands against your cluster with the appropriate command (e.g. `export KUBECONFIG=/path/to/kubeconfig`, `gcloud container clusters get-credentials`, `az aks get-credentials`, or `aws eks update-kubeconfig`).

Configure your `config.yaml` as detailed in the [authentication](#authentication) section.

Since the [actoolkit](https://pypi.org/project/actoolkit/) python package is bundled with the Docker image, you can immediately use it to interact with Astra Control:

```text
actoolkit list clusters
```

Alternatively, you can also follow the [manual installation](#3-manual-installation) steps to clone the git repo and optionally make modifications to the code base, all while not having to worry about software dependencies.

### 2. Python Package Installation

Install [actoolkit](https://pypi.org/project/actoolkit/) with the following command:

```text
python3 -m pip install actoolkit
```

Configure your `config.yaml` as detailed in the [authentication](#authentication) section.

You can now use `actoolkit` to invoke the NetApp Astra Control SDK. For example, [list](docs/toolkit/list/README.md#clusters) your Astra Control Kubernetes clusters with the command:

```text
actoolkit list clusters
```

Additionally, the `astraSDK/` library is available for import for use when creating custom scripts:

```text
>>> import astraSDK
>>> print(astraSDK.clusters.getClusters(output="table").main())
+----------------------+--------------------------------------+---------------+----------------+
| clusterName          | clusterID                            | clusterType   | managedState   |
+======================+======================================+===============+================+
| uscentral1-cluster   | 0412fd41-51b8-478a-b055-0bd50e34b1fe | gke           | managed        |
+----------------------+--------------------------------------+---------------+----------------+
| prod-cluster         | c69d8281-d4ea-4902-b03e-0c39c7da4543 | gke           | managed        |
+----------------------+--------------------------------------+---------------+----------------+
```

### 3. Manual Installation

Clone the NetApp Astra Control SDK repo.

```text
git clone https://github.com/NetApp/netapp-astra-toolkits.git
```

Move into the repo directory.

```text
cd netapp-astra-toolkits
```

Run the following commands to add the required Python elements:

```text
virtualenv toolkit
source toolkit/bin/activate
pip install -r requirements.txt
```

Configure your `config.yaml` as detailed in the [authentication](#authentication) section.

You can now use `./toolkit.py` to invoke the NetApp Astra Control SDK. For example, [list](docs/toolkit/list/README.md#clusters) your Astra Control Kubernetes clusters with the command:

```text
./toolkit.py list clusters
```

## Additional Resources

See [the documentation](/docs) for more information.
