# DESTRUCTIVE - Clean Astra Control Script - DESTRUCTIVE

## CAUTION!

**WARNING! This script destroys *all* applications, their underlying backups and snapshots, and unmanages all clusters.** This script should **only** be used to clean up after the completion of a proof-of-concept. Do not in any circumstances run this script in a production environment.

## Usage

This script can either be run by cloning this git repo, or by installing [actoolkit](https://pypi.org/project/actoolkit/) and downloading [cleanAstra.py](./cleanAstra.py). If you're unsure of which method is preferable, please see the [main project readme](../../README.md#installation).

Regardless of your method of installation, simply run the following command to clean your Astra Control instance.

```text
python path/to/cleanAstra.py
```

## Sample output

```text
$ python examples/astra-cleanup/cleanAstra.py
Cleaning up snaps/backups for app:  wordpress
        Deleting backup:    schedule-wordpress-20240123011000
        Deleting snap:      schedule-wordpress-20240123011000
Cleaning up snaps/backups for app:  mysql
        Deleting backup:    schedule-mysql-20240123011000
        Deleting snap:      schedule-mysql-20240123011000
Cleaning up snaps/backups for app:  jenkins
        Deleting backup:    schedule-jenkins-20240123011000
        Deleting snap:      schedule-jenkins-20240123011000
Cleaning up snaps/backups for app:  kafka
        Deleting backup:    schedule-kafka-20240123011000
        Deleting snap:      schedule-kafka-20240123011000
--> Sleeping for 30 seconds
Unmanaging app:         wordpress
App unmanaged
Unmanaging app:         mysql
App unmanaged
Unmanaging app:         jenkins
App unmanaged
Unmanaging app:         wordpress3
App unmanaged
--> Sleeping for 20 seconds
--> Sleeping for 20 seconds
Unmanaging cluster:	dev-uscentral1-cluster
Cluster unmanaged
ASTRA CLEANED SUCCESSFULLY
```
