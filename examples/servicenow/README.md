# Astra Control - ServiceNow Integration

This repo details utilizing Kubernetes CronJobs to initiate Astra Control application backups, with the purpose of any backup failures automatically creating a ServiceNow incident or event.

## actoolkit Secret Creation

In order to initiate application backups against Astra Control, our Kubernetes CronJob must have an appropriate access information and privileges mounted to the pod.  This example makes use of the [Astra Control SDK](https://github.com/NetApp/netapp-astra-toolkits), so a `config.yaml` file is needed which contains several components.

To create this file, run the following commands, but be sure to substitute in your Astra Control account ID, [API authorization token](https://docs.netapp.com/us-en/astra-automation/get-started/get_api_token.html#create-an-astra-api-token), and project name.  If you’re not sure of these values, additional information can be found in the [authentication section of the main SDK readme](https://github.com/NetApp/netapp-astra-toolkits/README.md#authentication) page on GitHub.

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

Next, apply your secret to the namespace of the application that will be protected:

```text
NAMESPACE=wordpress
kubectl -n $NAMESPACE create secret generic astra-control-config --from-file=config.yaml
```

## ServiceNow Secret Creation

If the Astra Control backup fails, a ServiceNow incident or event can be automatically created via the CronJob script. For this functionality, ServiceNow authentication information (which has the ability to open an incident via an API call), must be stored as a secret within the Kubernetes namespace.

To accomplish this, run the following command, substituting in the appropriate ServiceNow information:

```text
NAMESPACE=wordpress
kubectl -n $NAMESPACE create secret generic servicenow-auth \
    --from-literal=snow_instance='dev99999.service-now.com' \
    --from-literal=snow_username='admin' \
    --from-literal=snow_password='thisIsNotARealPassword'
```

## CronJob Creation

To apply the Kubernetes CronJob, run the following command:

```text
kubectl -n $NAMESPACE apply -f cron.yaml
```

## CronJob Verification

To view the status of the CronJob, run the following command:

```text
kubectl -n $NAMESPACE get cronjobs
```

In this example, the job has yet to execute:

```text
$ kubectl -n $NAMESPACE get cronjobs
NAME           SCHEDULE       SUSPEND   ACTIVE   LAST SCHEDULE   AGE
astra-backup   */10 * * * *   False     0        <none>          78s
```

After waiting a set period of time (defined by the `schedule`), we see that the `last schedule` field is populated:

```text
$ kubectl -n $NAMESPACE get cronjobs
NAME           SCHEDULE       SUSPEND   ACTIVE   LAST SCHEDULE   AGE
astra-backup   */10 * * * *   False     0        3m57s           86m
```

We can also check for the status of the pods, and view the logs to ensure everything completed successfully:

```text
$ kubectl -n wordpress get pods
NAME                          READY   STATUS      RESTARTS   AGE
astra-backup-27903980-vfgbg   0/1     Completed   0          14m
astra-backup-27903990-d2w82   0/1     Completed   0          4m10s
wordpress-597fbbf884-pxk58    1/1     Running     0          24h
wordpress-mariadb-0           1/1     Running     0          24h
```

```text
$ kubectl -n wordpress logs astra-backup-27903990-d2w82 | tail
Starting file download and execution
--> creating astra control backup
{"type": "application/astra-appBackup", "version": "1.1", "id": "af6ac8e9-ee14-4ea7-a5c3-a75984fe4c67", "name": "cron-20230120183019", "bucketID": "361aa1e0-60bc-4f1b-ba3b-bdaa890b5bac", "state": "pending", "stateUnready": [], "metadata": {"labels": [{"name": "astra.netapp.io/labels/read-only/triggerType", "value": "backup"}], "creationTimestamp": "2023-01-20T18:30:25Z", "modificationTimestamp": "2023-01-20T18:30:25Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
Starting backup of 30f1b2c2-ff63-4431-a8af-94db8e4671d3
Waiting for backup to complete..complete!
--> checking number of astra control backups
--> backups found: 11 is greater than backups to keep: 10
Backup b6ceaedb-3d07-438b-9f51-86a6bbb58e1d destroyed
--> checking number of astra control backups
--> backups at 10
```
