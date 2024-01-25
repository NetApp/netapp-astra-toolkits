# astra-labelbased-backup

This is an example on how to automatically protect any namespace on an Astra Control-managed Kubernetes cluster which contains a specific metadata label. It requires Astra Control 24.02 or greater, and the Kubernetes cluster must be managed through Architecture 3.0. It consists of the following files:

* `components.yaml`: consists of 1) a Kubernetes service account, cluster role, and cluster role binding which gives the necessary privileges to view and manage Astra Control custom resources, and 2) a Kubernetes cron job which runs the `protectCluster.py` script
* `protectCluster.py`: a python script which finds all namespaces not currently protected, and have a metadata label with a key matching the `PROTECTION_LABEL_KEY` environment variable and a corresponding value matching one of the `GOLD_LABEL`, `SILVER_LABEL`, or `BRONZE_LABEL` environment variables, and then brings them under management (with hourly, daily, weekly, and monthly protection policies) through Astra Control custom resources

## Setup

Open up `components.yaml` and optionally modify the following fields:

* `schedule`: change to your desired CronJob schedule for how frequently you want non-protected namespaces protected (default is every evening at 11pm)
* `ACTOOLKIT_VERSION`: the [actoolkit](https://pypi.org/project/actoolkit/#history) version (must be >=3.0.0) to utilize
* `BUCKET`: optionally specify the bucket to store the backups and snapshots (if one isn't specified, the first `available` non-`GOLD_BUCKET` bucket/appVault is used)
* `GOLD_BUCKET`: optionally change the bucket to store the `GOLD_LABEL` backups and snapshots (if one isn't specified, the first `available` non-`BUCKET` bucket/appVault is used)
* `PROTECTION_LABEL_KEY`: optionally change the metadata label key that is used to specify which namespaces should be protected
* `GOLD_LABEL`: optionally change the metadata label value that is used to specify the highest level of protection
* `SILVER_LABEL`: optionally change the metadata label value that is used to specify the middle level of protection
* `BRONZE_LABEL`: optionally change the metadata label value that is used to specify the lowest level of protection
* `args`: if modifying `protectCluster.py` (see below), then the `curl` command must be updated to point at your forked repository or local file server storing `protectCluster.py`

Open up `protectCluster.py` and optionally modify the global `PROTECTION_LEVELS` variable to specify the desired protection levels and date/times for each granularity.  **Note**: if making this modification, then the `curl` command within the `args` section of `components.py` must be updated to point at your forked repository or local file server storing `protectCluster.py`.

## Installation

```text
kubectl -n astra-connector apply -f components.yaml
```

## Verification

First, verify it was created correctly:

```text
$ kubectl -n astra-connector get cronjob
NAME                SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE   AGE
astra-labelbackup   0 23 * * *   False     0        <none>          15s
```

Next, wait the allotted amount of time per the schedule defined in `components.yaml` (the default is 11pm). Then, verify "last schedule" has been populated:

```text
kubectl -n astra-connector get cronjob
NAME                SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE   AGE
astra-labelbackup   0 23 * * *   False     0        48s             2m44s
```

And optionally view the logs of the cronjob pod:

```text
$ kubectl -n astra-connector logs `kubectl -n astra-connector get pods | grep astra-labelbackup | awk '{print $1}' | head -1`
fetch https://dl-cdn.alpinelinux.org/alpine/v3.19/main/x86_64/APKINDEX.tar.gz
fetch https://dl-cdn.alpinelinux.org/alpine/v3.19/community/x86_64/APKINDEX.tar.gz
(1/7) Installing brotli-libs (1.1.0-r1)
(2/7) Installing c-ares (1.24.0-r1)
(3/7) Installing libunistring (1.1-r2)
(4/7) Installing libidn2 (2.3.4-r4)
(5/7) Installing nghttp2-libs (1.58.0-r0)
(6/7) Installing libcurl (8.5.0-r0)
(7/7) Installing curl (8.5.0-r0)
Executing busybox-1.36.1-r15.trigger
OK: 20 MiB in 45 packages
Requirement already satisfied: pip in /usr/local/lib/python3.10/site-packages (23.0.1)
Collecting pip
  Downloading pip-23.3.2-py3-none-any.whl (2.1 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 4.6 MB/s eta 0:00:00
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 23.0.1
    Uninstalling pip-23.0.1:
      Successfully uninstalled pip-23.0.1
Successfully installed pip-23.3.2
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
Collecting actoolkit==3.0.0a12
  Downloading actoolkit-3.0.0a12-py3-none-any.whl.metadata (9.2 kB)
Collecting Jinja2>=3.1.2 (from actoolkit==3.0.0a12)
  Downloading Jinja2-3.1.3-py3-none-any.whl.metadata (3.3 kB)
Collecting kubernetes<=27.2.0,>=24.2.0 (from actoolkit==3.0.0a12)
  Downloading kubernetes-27.2.0-py2.py3-none-any.whl.metadata (1.5 kB)
Collecting PyYAML<=6.0.1,>=6.0.0 (from actoolkit==3.0.0a12)
  Downloading PyYAML-6.0.1-cp310-cp310-musllinux_1_1_x86_64.whl.metadata (2.1 kB)
Collecting requests==2.31.0 (from actoolkit==3.0.0a12)
  Downloading requests-2.31.0-py3-none-any.whl.metadata (4.6 kB)
Collecting tabulate<=0.9.0,>=0.8.9 (from actoolkit==3.0.0a12)
  Downloading tabulate-0.9.0-py3-none-any.whl (35 kB)
Collecting termcolor<3.0 (from actoolkit==3.0.0a12)
  Downloading termcolor-2.4.0-py3-none-any.whl.metadata (6.1 kB)
Collecting urllib3<=2.1.0,>=1.26.8 (from actoolkit==3.0.0a12)
  Downloading urllib3-2.1.0-py3-none-any.whl.metadata (6.4 kB)
Collecting charset-normalizer<4,>=2 (from requests==2.31.0->actoolkit==3.0.0a12)
  Downloading charset_normalizer-3.3.2-cp310-cp310-musllinux_1_1_x86_64.whl.metadata (33 kB)
Collecting idna<4,>=2.5 (from requests==2.31.0->actoolkit==3.0.0a12)
  Downloading idna-3.6-py3-none-any.whl.metadata (9.9 kB)
Collecting certifi>=2017.4.17 (from requests==2.31.0->actoolkit==3.0.0a12)
  Downloading certifi-2023.11.17-py3-none-any.whl.metadata (2.2 kB)
Collecting MarkupSafe>=2.0 (from Jinja2>=3.1.2->actoolkit==3.0.0a12)
  Downloading MarkupSafe-2.1.4-cp310-cp310-musllinux_1_1_x86_64.whl.metadata (3.0 kB)
Collecting six>=1.9.0 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading six-1.16.0-py2.py3-none-any.whl (11 kB)
Collecting python-dateutil>=2.5.3 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading python_dateutil-2.8.2-py2.py3-none-any.whl (247 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 247.7/247.7 kB 1.6 MB/s eta 0:00:00
Collecting google-auth>=1.0.1 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading google_auth-2.27.0-py2.py3-none-any.whl.metadata (4.7 kB)
Collecting websocket-client!=0.40.0,!=0.41.*,!=0.42.*,>=0.32.0 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading websocket_client-1.7.0-py3-none-any.whl.metadata (7.9 kB)
Collecting requests-oauthlib (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading requests_oauthlib-1.3.1-py2.py3-none-any.whl (23 kB)
Collecting oauthlib>=3.2.2 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading oauthlib-3.2.2-py3-none-any.whl (151 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 151.7/151.7 kB 7.4 MB/s eta 0:00:00
Collecting cachetools<6.0,>=2.0.0 (from google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading cachetools-5.3.2-py3-none-any.whl.metadata (5.2 kB)
Collecting pyasn1-modules>=0.2.1 (from google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading pyasn1_modules-0.3.0-py2.py3-none-any.whl (181 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 181.3/181.3 kB 4.8 MB/s eta 0:00:00
Collecting rsa<5,>=3.1.4 (from google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading rsa-4.9-py3-none-any.whl (34 kB)
Collecting pyasn1<0.6.0,>=0.4.6 (from pyasn1-modules>=0.2.1->google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a12)
  Downloading pyasn1-0.5.1-py2.py3-none-any.whl.metadata (8.6 kB)
Downloading actoolkit-3.0.0a12-py3-none-any.whl (107 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 107.0/107.0 kB 7.9 MB/s eta 0:00:00
Downloading requests-2.31.0-py3-none-any.whl (62 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 62.6/62.6 kB 7.3 MB/s eta 0:00:00
Downloading Jinja2-3.1.3-py3-none-any.whl (133 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 133.2/133.2 kB 7.7 MB/s eta 0:00:00
Downloading kubernetes-27.2.0-py2.py3-none-any.whl (1.5 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.5/1.5 MB 9.1 MB/s eta 0:00:00
Downloading PyYAML-6.0.1-cp310-cp310-musllinux_1_1_x86_64.whl (707 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 707.5/707.5 kB 8.8 MB/s eta 0:00:00
Downloading termcolor-2.4.0-py3-none-any.whl (7.7 kB)
Downloading urllib3-2.1.0-py3-none-any.whl (104 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 104.6/104.6 kB 15.2 MB/s eta 0:00:00
Downloading certifi-2023.11.17-py3-none-any.whl (162 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 162.5/162.5 kB 17.6 MB/s eta 0:00:00
Downloading charset_normalizer-3.3.2-cp310-cp310-musllinux_1_1_x86_64.whl (142 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 142.6/142.6 kB 11.4 MB/s eta 0:00:00
Downloading google_auth-2.27.0-py2.py3-none-any.whl (186 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 186.8/186.8 kB 9.9 MB/s eta 0:00:00
Downloading idna-3.6-py3-none-any.whl (61 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 61.6/61.6 kB 8.7 MB/s eta 0:00:00
Downloading MarkupSafe-2.1.4-cp310-cp310-musllinux_1_1_x86_64.whl (30 kB)
Downloading websocket_client-1.7.0-py3-none-any.whl (58 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.5/58.5 kB 9.2 MB/s eta 0:00:00
Downloading cachetools-5.3.2-py3-none-any.whl (9.3 kB)
Downloading pyasn1-0.5.1-py2.py3-none-any.whl (84 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 84.9/84.9 kB 11.6 MB/s eta 0:00:00
Installing collected packages: websocket-client, urllib3, termcolor, tabulate, six, PyYAML, pyasn1, oauthlib, MarkupSafe, idna, charset-normalizer, certifi, cachetools, rsa, requests, python-dateutil, pyasn1-modules, Jinja2, requests-oauthlib, google-auth, kubernetes, actoolkit
Successfully installed Jinja2-3.1.3 MarkupSafe-2.1.4 PyYAML-6.0.1 actoolkit-3.0.0a12 cachetools-5.3.2 certifi-2023.11.17 charset-normalizer-3.3.2 google-auth-2.27.0 idna-3.6 kubernetes-27.2.0 oauthlib-3.2.2 pyasn1-0.5.1 pyasn1-modules-0.3.0 python-dateutil-2.8.2 requests-2.31.0 requests-oauthlib-1.3.1 rsa-4.9 six-1.16.0 tabulate-0.9.0 termcolor-2.4.0 urllib3-2.1.0 websocket-client-1.7.0
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
--> managing namespace wordpress
{"apiVersion": "astra.netapp.io/v1", "kind": "Application", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:spec": {".": {}, "f:includedNamespaces": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress", "namespace": "astra-connector", "resourceVersion": "79866624", "uid": "49396225-d942-42bd-9afc-bc25910c3853"}, "spec": {"includedNamespaces": [{"namespace": "wordpress"}]}}
    --> creating hourly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress-hourly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress-hourly-s2fjm", "namespace": "astra-connector", "resourceVersion": "79866628", "uid": "ac11e473-9125-4b31-98c5-672947dc6abd"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "3", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "hourly", "hour": "", "minute": "26", "replicate": false, "snapshotRetention": "3"}}
    --> creating daily   protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress-daily-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress-daily-jlkpq", "namespace": "astra-connector", "resourceVersion": "79866634", "uid": "2f44d5a2-8dad-4d99-8a16-9f06195a2d5d"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "3", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "daily", "hour": "1", "minute": "59", "replicate": false, "snapshotRetention": "3"}}
    --> creating weekly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress-weekly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress-weekly-p6pl6", "namespace": "astra-connector", "resourceVersion": "79866647", "uid": "7d823b8a-ed80-4821-8f50-56a2c0f3d764"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "3", "dayOfMonth": "", "dayOfWeek": "1", "enabled": true, "granularity": "weekly", "hour": "2", "minute": "5", "replicate": false, "snapshotRetention": "3"}}
    --> creating monthly protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress-monthly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress-monthly-cp92f", "namespace": "astra-connector", "resourceVersion": "79866652", "uid": "a85c7888-632b-4f6a-93ef-512b6369a482"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "3", "dayOfMonth": "1", "dayOfWeek": "", "enabled": true, "granularity": "monthly", "hour": "3", "minute": "55", "replicate": false, "snapshotRetention": "3"}}
--> managing namespace wordpress1
{"apiVersion": "astra.netapp.io/v1", "kind": "Application", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:spec": {".": {}, "f:includedNamespaces": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress1", "namespace": "astra-connector", "resourceVersion": "79866661", "uid": "4b1cdcd2-1515-4493-916a-c78d0422a046"}, "spec": {"includedNamespaces": [{"namespace": "wordpress1"}]}}
    --> creating hourly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress1-hourly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress1-hourly-7r76f", "namespace": "astra-connector", "resourceVersion": "79866666", "uid": "497911ec-2fd1-4c7f-a16f-ebd0bfa1769d"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress1", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "hourly", "hour": "", "minute": "33", "replicate": false, "snapshotRetention": "1"}}
    --> creating daily   protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress1-daily-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress1-daily-8rcss", "namespace": "astra-connector", "resourceVersion": "79866669", "uid": "cd9fd9eb-2959-49d0-a36c-132ea048502a"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress1", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "daily", "hour": "1", "minute": "23", "replicate": false, "snapshotRetention": "1"}}
    --> creating weekly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress1-weekly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress1-weekly-plvjp", "namespace": "astra-connector", "resourceVersion": "79866671", "uid": "b4082989-d1e8-4798-9f60-780d58ef0d45"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress1", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "1", "enabled": true, "granularity": "weekly", "hour": "2", "minute": "22", "replicate": false, "snapshotRetention": "1"}}
    --> creating monthly protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress1-monthly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress1-monthly-kfh9g", "namespace": "astra-connector", "resourceVersion": "79866673", "uid": "a8308f94-e803-4b48-bce7-b3b4b49d2090"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress1", "backupRetention": "1", "dayOfMonth": "1", "dayOfWeek": "", "enabled": true, "granularity": "monthly", "hour": "3", "minute": "7", "replicate": false, "snapshotRetention": "1"}}
--> managing namespace wordpress2
{"apiVersion": "astra.netapp.io/v1", "kind": "Application", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:spec": {".": {}, "f:includedNamespaces": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress2", "namespace": "astra-connector", "resourceVersion": "79866675", "uid": "40daf4e6-a8ab-4bda-9868-756ddb3e0a10"}, "spec": {"includedNamespaces": [{"namespace": "wordpress2"}]}}
    --> creating hourly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress2-hourly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress2-hourly-7729l", "namespace": "astra-connector", "resourceVersion": "79866679", "uid": "9079b925-524a-42b6-90c9-ce253059f99a"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress2", "backupRetention": "0", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "hourly", "hour": "", "minute": "34", "replicate": false, "snapshotRetention": "1"}}
    --> creating daily   protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress2-daily-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress2-daily-dmmch", "namespace": "astra-connector", "resourceVersion": "79866682", "uid": "34e29173-5d77-4877-8efe-506e5c291801"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress2", "backupRetention": "0", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "daily", "hour": "1", "minute": "19", "replicate": false, "snapshotRetention": "1"}}
    --> creating weekly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress2-weekly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress2-weekly-r65qd", "namespace": "astra-connector", "resourceVersion": "79866684", "uid": "761aab16-9aa0-4896-a8e6-1a3e2b1e8db1"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress2", "backupRetention": "0", "dayOfMonth": "", "dayOfWeek": "1", "enabled": true, "granularity": "weekly", "hour": "2", "minute": "30", "replicate": false, "snapshotRetention": "1"}}
    --> creating monthly protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-25T16:20:19Z", "generateName": "wordpress2-monthly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-25T16:20:19Z"}], "name": "wordpress2-monthly-57rp7", "namespace": "astra-connector", "resourceVersion": "79866686", "uid": "bca18cbb-02c3-4447-8e76-62840292127c"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket7", "applicationRef": "wordpress2", "backupRetention": "0", "dayOfMonth": "1", "dayOfWeek": "", "enabled": true, "granularity": "monthly", "hour": "3", "minute": "18", "replicate": false, "snapshotRetention": "1"}}
```
