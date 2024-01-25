# astra-fullcluster-backup

This is an example on how to protect every namespace on an Astra Control-managed Kubernetes cluster. It requires Astra Control 24.02 or greater, and the Kubernetes cluster must be managed through Architecture 3.0. It consists of the following files:

* `components.yaml`: consists of 1) a Kubernetes service account, cluster role, and cluster role binding which gives the necessary privileges to view and manage Astra Control custom resources, and 2) a Kubernetes cron job which runs the `protectCluster.py` script
* `protectCluster.py`: a python script which finds all namespaces not currently protected, and not part of the `IGNORE_NAMESPACES` environment variable, and then brings them under management (with hourly, daily, weekly, and monthly protection policies) through Astra Control custom resources

## Setup

Open up `components.yaml` and optionally modify the following fields:

* `schedule`: change to your desired CronJob schedule for how frequently you want non-protected namespaces protected (default is every evening at 11pm)
* `ACTOOLKIT_VERSION`: the [actoolkit](https://pypi.org/project/actoolkit/#history) version (must be >=3.0.0) to utilize
* `IGNORE_NAMESPACES`: the list of namespaces (system or otherwise) that should *not* be protected
* `BUCKET`: optionally specify the bucket to store the backups and snapshots (if one isn't specified, the first `available` bucket/appVault is used)
* `BACKUPS_TO_KEEP`: the number of backups to keep for each granularity
* `SNAPSHOTS_TO_KEEP`: the number of snapshots to keep for each granularity
* `HOUR`: the hour to create each backup and snapshot (daily, weekly, and monthly granularities)
* `DAY_OF_WEEK`: the day of the week to create each backup and snapshot (weekly granularity)
* `DAY_OF_MONTH`: the day of the month to create each backup and snapshot (monthly granularity)

## Installation

```text
kubectl -n astra-connector apply -f components.yaml
```

## Verification

First, verify it was created correctly:

```text
$ kubectl -n astra-connector get cronjob
NAME               SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE   AGE
astra-fullbackup   0 23 * * *   False     0        <none>          15s
```

Next, wait the allotted amount of time per the schedule defined in `components.yaml` (the default is 11pm). Then, verify "last schedule" has been populated:

```text
kubectl -n astra-connector get cronjob
NAME               SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE   AGE
astra-fullbackup   0 23 * * *   False     0        48s             2m44s
```

And optionally view the logs of the cronjob pod:

```text
$ kubectl -n astra-connector logs `kubectl -n astra-connector get pods | grep astra-fullbackup | awk '{print $1}' | head -1`
fetch https://dl-cdn.alpinelinux.org/alpine/v3.19/main/x86_64/APKINDEX.tar.gz
fetch https://dl-cdn.alpinelinux.org/alpine/v3.19/community/x86_64/APKINDEX.tar.gz
(1/7) Installing brotli-libs (1.1.0-r1)
(2/7) Installing c-ares (1.24.0-r0)
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
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 5.5 MB/s eta 0:00:00
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 23.0.1
    Uninstalling pip-23.0.1:
      Successfully uninstalled pip-23.0.1
Successfully installed pip-23.3.2
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
Collecting actoolkit==3.0.0a11
  Downloading actoolkit-3.0.0a11-py3-none-any.whl.metadata (9.2 kB)
Collecting Jinja2>=3.1.2 (from actoolkit==3.0.0a11)
  Downloading Jinja2-3.1.3-py3-none-any.whl.metadata (3.3 kB)
Collecting kubernetes<=27.2.0,>=24.2.0 (from actoolkit==3.0.0a11)
  Downloading kubernetes-27.2.0-py2.py3-none-any.whl.metadata (1.5 kB)
Collecting PyYAML<=6.0.1,>=6.0.0 (from actoolkit==3.0.0a11)
  Downloading PyYAML-6.0.1-cp310-cp310-musllinux_1_1_x86_64.whl.metadata (2.1 kB)
Collecting requests==2.31.0 (from actoolkit==3.0.0a11)
  Downloading requests-2.31.0-py3-none-any.whl.metadata (4.6 kB)
Collecting tabulate<=0.9.0,>=0.8.9 (from actoolkit==3.0.0a11)
  Downloading tabulate-0.9.0-py3-none-any.whl (35 kB)
Collecting termcolor<3.0 (from actoolkit==3.0.0a11)
  Downloading termcolor-2.4.0-py3-none-any.whl.metadata (6.1 kB)
Collecting urllib3<=2.1.0,>=1.26.8 (from actoolkit==3.0.0a11)
  Downloading urllib3-2.1.0-py3-none-any.whl.metadata (6.4 kB)
Collecting charset-normalizer<4,>=2 (from requests==2.31.0->actoolkit==3.0.0a11)
  Downloading charset_normalizer-3.3.2-cp310-cp310-musllinux_1_1_x86_64.whl.metadata (33 kB)
Collecting idna<4,>=2.5 (from requests==2.31.0->actoolkit==3.0.0a11)
  Downloading idna-3.6-py3-none-any.whl.metadata (9.9 kB)
Collecting certifi>=2017.4.17 (from requests==2.31.0->actoolkit==3.0.0a11)
  Downloading certifi-2023.11.17-py3-none-any.whl.metadata (2.2 kB)
Collecting MarkupSafe>=2.0 (from Jinja2>=3.1.2->actoolkit==3.0.0a11)
  Downloading MarkupSafe-2.1.3-cp310-cp310-musllinux_1_1_x86_64.whl.metadata (3.0 kB)
Collecting six>=1.9.0 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading six-1.16.0-py2.py3-none-any.whl (11 kB)
Collecting python-dateutil>=2.5.3 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading python_dateutil-2.8.2-py2.py3-none-any.whl (247 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 247.7/247.7 kB 1.5 MB/s eta 0:00:00
Collecting google-auth>=1.0.1 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading google_auth-2.26.2-py2.py3-none-any.whl.metadata (4.7 kB)
Collecting websocket-client!=0.40.0,!=0.41.*,!=0.42.*,>=0.32.0 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading websocket_client-1.7.0-py3-none-any.whl.metadata (7.9 kB)
Collecting requests-oauthlib (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading requests_oauthlib-1.3.1-py2.py3-none-any.whl (23 kB)
Collecting oauthlib>=3.2.2 (from kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading oauthlib-3.2.2-py3-none-any.whl (151 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 151.7/151.7 kB 5.3 MB/s eta 0:00:00
Collecting cachetools<6.0,>=2.0.0 (from google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading cachetools-5.3.2-py3-none-any.whl.metadata (5.2 kB)
Collecting pyasn1-modules>=0.2.1 (from google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading pyasn1_modules-0.3.0-py2.py3-none-any.whl (181 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 181.3/181.3 kB 6.8 MB/s eta 0:00:00
Collecting rsa<5,>=3.1.4 (from google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading rsa-4.9-py3-none-any.whl (34 kB)
Collecting pyasn1<0.6.0,>=0.4.6 (from pyasn1-modules>=0.2.1->google-auth>=1.0.1->kubernetes<=27.2.0,>=24.2.0->actoolkit==3.0.0a11)
  Downloading pyasn1-0.5.1-py2.py3-none-any.whl.metadata (8.6 kB)
Downloading actoolkit-3.0.0a11-py3-none-any.whl (107 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 107.1/107.1 kB 6.5 MB/s eta 0:00:00
Downloading requests-2.31.0-py3-none-any.whl (62 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 62.6/62.6 kB 3.3 MB/s eta 0:00:00
Downloading Jinja2-3.1.3-py3-none-any.whl (133 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 133.2/133.2 kB 4.9 MB/s eta 0:00:00
Downloading kubernetes-27.2.0-py2.py3-none-any.whl (1.5 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.5/1.5 MB 8.5 MB/s eta 0:00:00
Downloading PyYAML-6.0.1-cp310-cp310-musllinux_1_1_x86_64.whl (707 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 707.5/707.5 kB 23.7 MB/s eta 0:00:00
Downloading termcolor-2.4.0-py3-none-any.whl (7.7 kB)
Downloading urllib3-2.1.0-py3-none-any.whl (104 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 104.6/104.6 kB 5.5 MB/s eta 0:00:00
Downloading certifi-2023.11.17-py3-none-any.whl (162 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 162.5/162.5 kB 7.6 MB/s eta 0:00:00
Downloading charset_normalizer-3.3.2-cp310-cp310-musllinux_1_1_x86_64.whl (142 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 142.6/142.6 kB 5.8 MB/s eta 0:00:00
Downloading google_auth-2.26.2-py2.py3-none-any.whl (186 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 186.5/186.5 kB 7.6 MB/s eta 0:00:00
Downloading idna-3.6-py3-none-any.whl (61 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 61.6/61.6 kB 1.4 MB/s eta 0:00:00
Downloading MarkupSafe-2.1.3-cp310-cp310-musllinux_1_1_x86_64.whl (29 kB)
Downloading websocket_client-1.7.0-py3-none-any.whl (58 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.5/58.5 kB 1.6 MB/s eta 0:00:00
Downloading cachetools-5.3.2-py3-none-any.whl (9.3 kB)
Downloading pyasn1-0.5.1-py2.py3-none-any.whl (84 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 84.9/84.9 kB 4.4 MB/s eta 0:00:00
Installing collected packages: websocket-client, urllib3, termcolor, tabulate, six, PyYAML, pyasn1, oauthlib, MarkupSafe, idna, charset-normalizer, certifi, cachetools, rsa, requests, python-dateutil, pyasn1-modules, Jinja2, requests-oauthlib, google-auth, kubernetes, actoolkit
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
Successfully installed Jinja2-3.1.3 MarkupSafe-2.1.3 PyYAML-6.0.1 actoolkit-3.0.0a11 cachetools-5.3.2 certifi-2023.11.17 charset-normalizer-3.3.2 google-auth-2.26.2 idna-3.6 kubernetes-27.2.0 oauthlib-3.2.2 pyasn1-0.5.1 pyasn1-modules-0.3.0 python-dateutil-2.8.2 requests-2.31.0 requests-oauthlib-1.3.1 rsa-4.9 six-1.16.0 tabulate-0.9.0 termcolor-2.4.0 urllib3-2.1.0 websocket-client-1.7.0
--> managing namespace default
{"apiVersion": "astra.netapp.io/v1", "kind": "Application", "metadata": {"creationTimestamp": "2024-01-19T20:25:19Z", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:spec": {".": {}, "f:includedNamespaces": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:19Z"}], "name": "default", "namespace": "astra-connector", "resourceVersion": "74372508", "uid": "c492226b-330d-4351-a5cc-f862013d81bb"}, "spec": {"includedNamespaces": [{"namespace": "default"}]}}
    --> creating hourly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:19Z", "generateName": "default-hourly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:19Z"}], "name": "default-hourly-crtvl", "namespace": "astra-connector", "resourceVersion": "74372514", "uid": "a93a1f20-dcd1-4ab2-a0bd-141df3ee6c25"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "default", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "hourly", "hour": "", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating daily   protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "default-daily-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "default-daily-dxr9l", "namespace": "astra-connector", "resourceVersion": "74372515", "uid": "78aca477-0325-4ece-9cf1-4318f7f8dc3b"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "default", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "daily", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating weekly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "default-weekly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "default-weekly-8wlmd", "namespace": "astra-connector", "resourceVersion": "74372521", "uid": "c6c78c08-4e11-4bfe-a830-b13a46740c93"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "default", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "1", "enabled": true, "granularity": "weekly", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating monthly protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "default-monthly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "default-monthly-hr8p2", "namespace": "astra-connector", "resourceVersion": "74372524", "uid": "7cd8fb4b-0da5-4886-bc19-ede66285388c"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "default", "backupRetention": "1", "dayOfMonth": "1", "dayOfWeek": "", "enabled": true, "granularity": "monthly", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
--> managing namespace wordpress
{"apiVersion": "astra.netapp.io/v1", "kind": "Application", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:spec": {".": {}, "f:includedNamespaces": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress", "namespace": "astra-connector", "resourceVersion": "74372533", "uid": "555389e1-b82b-481a-b5c8-ca577349b8d2"}, "spec": {"includedNamespaces": [{"namespace": "wordpress"}]}}
    --> creating hourly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-hourly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-hourly-ppvg2", "namespace": "astra-connector", "resourceVersion": "74372538", "uid": "aaff9a54-cca0-4b71-8396-ccffde72dcd7"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "hourly", "hour": "", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating daily   protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-daily-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-daily-dh6sp", "namespace": "astra-connector", "resourceVersion": "74372540", "uid": "37004025-fca7-4113-b4bd-3c10cb2f0f8c"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "daily", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating weekly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-weekly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-weekly-w85b2", "namespace": "astra-connector", "resourceVersion": "74372544", "uid": "ce5cb587-06bc-438d-894a-8eaff97eacf3"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "1", "enabled": true, "granularity": "weekly", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating monthly protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-monthly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-monthly-4dbg9", "namespace": "astra-connector", "resourceVersion": "74372550", "uid": "3d243b0b-1cfc-423c-9410-387b3be71205"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress", "backupRetention": "1", "dayOfMonth": "1", "dayOfWeek": "", "enabled": true, "granularity": "monthly", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
--> managing namespace wordpress-clone
{"apiVersion": "astra.netapp.io/v1", "kind": "Application", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:spec": {".": {}, "f:includedNamespaces": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-clone", "namespace": "astra-connector", "resourceVersion": "74372554", "uid": "6e37f362-b391-4df7-b08a-f88834382d17"}, "spec": {"includedNamespaces": [{"namespace": "wordpress-clone"}]}}
    --> creating hourly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-clone-hourly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-clone-hourly-ljvrl", "namespace": "astra-connector", "resourceVersion": "74372565", "uid": "dae77bbe-31ef-4cba-9cb9-2bf4bb5e4bae"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress-clone", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "hourly", "hour": "", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating daily   protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-clone-daily-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-clone-daily-pg7bn", "namespace": "astra-connector", "resourceVersion": "74372569", "uid": "698bd0bc-83a8-45e7-b4fd-43f0ba873a0d"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress-clone", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "", "enabled": true, "granularity": "daily", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating weekly  protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-clone-weekly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-clone-weekly-c7hqr", "namespace": "astra-connector", "resourceVersion": "74372575", "uid": "63ed88c1-5463-4a19-859d-a9b02981913b"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress-clone", "backupRetention": "1", "dayOfMonth": "", "dayOfWeek": "1", "enabled": true, "granularity": "weekly", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
    --> creating monthly protection policy
{"apiVersion": "astra.netapp.io/v1", "kind": "Schedule", "metadata": {"creationTimestamp": "2024-01-19T20:25:20Z", "generateName": "wordpress-clone-monthly-", "generation": 1, "managedFields": [{"apiVersion": "astra.netapp.io/v1", "fieldsType": "FieldsV1", "fieldsV1": {"f:metadata": {"f:generateName": {}}, "f:spec": {".": {}, "f:appVaultRef": {}, "f:applicationRef": {}, "f:backupRetention": {}, "f:dayOfMonth": {}, "f:dayOfWeek": {}, "f:enabled": {}, "f:granularity": {}, "f:hour": {}, "f:minute": {}, "f:replicate": {}, "f:snapshotRetention": {}}}, "manager": "OpenAPI-Generator", "operation": "Update", "time": "2024-01-19T20:25:20Z"}], "name": "wordpress-clone-monthly-cpnc9", "namespace": "astra-connector", "resourceVersion": "74372580", "uid": "ca200fc8-31aa-4229-b5bc-5cffe01c1340"}, "spec": {"appVaultRef": "ontap-s3-astra-bucket8", "applicationRef": "wordpress-clone", "backupRetention": "1", "dayOfMonth": "1", "dayOfWeek": "", "enabled": true, "granularity": "monthly", "hour": "1", "minute": "0", "replicate": false, "snapshotRetention": "2"}}
```
