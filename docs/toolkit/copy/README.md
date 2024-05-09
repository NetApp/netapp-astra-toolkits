# Copy

The `copy` argument allows you to copy application resources from one app to another, or copy Astra Control resources to your local workstation.

* [Asup](#asup)
* [Hooks](#hooks)
* [Protections](#protections)

```text
$ actoolkit copy -h
usage: actoolkit copy [-h] {asup,hooks,protections} ...

options:
  -h, --help            show this help message and exit

objectType:
  {asup,hooks,protections}
    asup                copy auto-support bundle to local workstation
    hooks               copy all hooks (executionHooks) from one app to another
    protections         copy all protections from one app to another
```

## Asup

The `copy asup` command allows you to copy / download an existing auto-support bundle to your local workstation. To create an auto-support bundle, please see the [create asup](../create/README.md#asup) command.

It requires a single argument, the `asupID`, which can be gathered via the [list asups](../list/README.md#asups) command. The command usage is:

```text
actoolkit copy asup <asupID>
```

Example output:

```text
$ actoolkit copy asup b1398002-f2ad-4d73-a0e4-aed33d3e05e0
'b1398002-f2ad-4d73-a0e4-aed33d3e05e0.tgz' downloaded to current directory successfully.
```

You can then view the downloaded auto-support bundle:

```text
$ ls -l b1398002*
-rw-r--r--  1 mhaigh  staff    13M May  9 10:04 b1398002-f2ad-4d73-a0e4-aed33d3e05e0.tgz
```

## Hooks

The `copy hooks` command allows you to copy all execution hooks from a source app to a destination app. This can be useful when cloning an application, as by default these resources are not currently copied. The command usage is:

```text
actoolkit copy hooks <sourceAppID> <destinationAppID>
```

Example output:

```text
$ actoolkit copy hooks 1c252557-b5d3-4446-b5fe-c41ed2b0595c 6676813f-4f6c-4487-9877-2d92cbd801fc
{"metadata": {"labels": [], "creationTimestamp": "2023-08-16T18:19:22Z", "modificationTimestamp": "2023-08-16T18:19:22Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "type": "application/astra-executionHook", "version": "1.3", "id": "a07b76c0-fae7-4d98-bc04-61136e9b25d0", "name": "db-presnap", "hookType": "custom", "matchingCriteria": [{"type": "containerImage", "value": "mariadb"}], "action": "snapshot", "stage": "pre", "hookSourceID": "302915c6-3c9a-4394-9393-283c11108c73", "arguments": ["pre"], "appID": "6676813f-4f6c-4487-9877-2d92cbd801fc", "enabled": "true"}
{"metadata": {"labels": [], "creationTimestamp": "2023-08-16T18:19:22Z", "modificationTimestamp": "2023-08-16T18:19:22Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}, "type": "application/astra-executionHook", "version": "1.3", "id": "d8dd33ee-c42e-4c17-a0a0-bf51412fa8ed", "name": "db-postsnap", "hookType": "custom", "matchingCriteria": [{"type": "containerImage", "value": "mariadb"}], "action": "snapshot", "stage": "post", "hookSourceID": "302915c6-3c9a-4394-9393-283c11108c73", "arguments": ["post"], "appID": "6676813f-4f6c-4487-9877-2d92cbd801fc", "enabled": "true"}
```

## Protections

The `copy protections` command allows you to copy all protection policies from a source app to a destination app. This can be useful when cloning an application, as by default these resources are not currently copied. The command usage is:

```text
actoolkit copy protections <sourceAppID> <destinationAppID>
```

Example output:

```text
$ actoolkit copy protections 1c252557-b5d3-4446-b5fe-c41ed2b0595c 6676813f-4f6c-4487-9877-2d92cbd801fc
{"type": "application/astra-schedule", "version": "1.3", "id": "bd7f215d-6f0d-4c25-a508-7c64bb596ca4", "name": "hourly-i7gmr", "enabled": "true", "granularity": "hourly", "minute": "0", "snapshotRetention": "1", "backupRetention": "1", "metadata": {"labels": [], "creationTimestamp": "2023-08-16T18:35:24Z", "modificationTimestamp": "2023-08-16T18:35:24Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
{"type": "application/astra-schedule", "version": "1.3", "id": "71e16400-aa00-46f0-a9ee-530d82de8ced", "name": "daily-uvnw5", "enabled": "true", "granularity": "daily", "minute": "0", "hour": "2", "snapshotRetention": "1", "backupRetention": "1", "metadata": {"labels": [], "creationTimestamp": "2023-08-16T18:35:24Z", "modificationTimestamp": "2023-08-16T18:35:24Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
{"type": "application/astra-schedule", "version": "1.3", "id": "9918ce3c-e1a3-4c67-b0bf-b77ef96f18b5", "name": "weekly-9vpa1", "enabled": "true", "granularity": "weekly", "minute": "0", "hour": "2", "dayOfWeek": "0", "snapshotRetention": "1", "backupRetention": "1", "metadata": {"labels": [], "creationTimestamp": "2023-08-16T18:35:25Z", "modificationTimestamp": "2023-08-16T18:35:25Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
{"type": "application/astra-schedule", "version": "1.3", "id": "d985d3e5-7cfb-4e5b-90b5-1aeaab041b49", "name": "monthly-am9sa", "enabled": "true", "granularity": "monthly", "minute": "0", "hour": "2", "dayOfMonth": "1", "snapshotRetention": "1", "backupRetention": "1", "metadata": {"labels": [], "creationTimestamp": "2023-08-16T18:35:25Z", "modificationTimestamp": "2023-08-16T18:35:25Z", "createdBy": "8146d293-d897-4e16-ab10-8dca934637ab"}}
```
