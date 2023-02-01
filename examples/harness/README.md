# Kubernetes Application Deployment and Data Management with Harness and Astra Control

[Harness](https://www.harness.io/) provides a GitOps, continuous delivery, and continuous integration platform for software development team, which helps customers automate and streamline their delivery processes, reducing the time and effort required to get new features and updates into production. By using Harness, customers can increase their velocity, improve the reliability of their deployments, and simplify the overall delivery process. This is important because it allows development teams to focus on delivering value to their users, while relying on Harness to handle the complex and error-prone aspects of delivery.

By integrating Harness with [NetApp Astra Control](https://cloud.netapp.com/astra), customers can take advantage of the robust data management capabilities provided by Astra Control and use Harness to automate and streamline their delivery processes for containerized applications running on Kubernetes. This integration provides an end-to-end solution for application data management and continuous delivery of Kubernetes applications, ensuring reliable and consistent deployment experiences while reducing the time and effort required to manage applications.

* [Template Overview](#template-overview)
  * [Scope](#scope)
  * [Variables](#variables)
  * [Steps](#steps)
* [Manage App](#manage-app)
* [Clone App](#clone-app)
* [Backup App](#backup-app)
* [Snapshot App](#snapshot-app)

## Template Overview

### Scope

Each of the templates contained within this directory are configured as `Account` scoped templates, however they can easily be reduced in scope to an `Organization` template by adding the following line:

```text
  orgIdentifier: <orgID>
```

Or to a `Project` scope with the following lines:

```text
  projectIdentifier: <projectID>
  orgIdentifier: <orgID>
```

These lines should be placed within the initial `template` dictionary.

### Variables

Each template has the same four stage variables:

* `actoolkit_version`: the version of [actoolkit](https://pypi.org/project/actoolkit/) to install. These templates are set to `2.6.0`, which is the latest release at the time of creating this integration. It is recommended to thoroughly test all steps and stages if changing this value.
* `cluster_name`: the Kubernetes [cluster name](../../docs/toolkit/list/README.md#clusters) that the application lives on, which should already be managed by Astra Control
* `namespace`: the Kubernetes namespace name that the application lives in
* `app_name`: the friendly name of the Astra Control application

### Steps

Each template has three steps:

1. `install-actoolkit`: Installs python3, pip, and actoolkit (to the version specified by `actoolkit_version`) on the delegate
1. `create-credential-file`: Creates a file `/etc/astra-toolkits/config.yaml` on the delegate based on a Harness secret with the id of `astracontrolsdkcreds`. For more info on the components of this file, see the [main readme](../../README.md#authentication) or [this video](https://www.youtube.com/watch?v=o-q-q_41A5A).
1. Stage-specific-step: The final step varies depending upon the template, see below sections for additional detail.

Depending upon the delegate in use in your environment, it may not be necessary to run steps 1 and 2 above every time the stage runs (for instance if you use long lived VMs). However, for ephemeral delegates like Kubernetes pods, it's a good practice to leave these steps in the stage.

## Manage App

The [manage app](./astra-manage-app.yaml) template has a 3rd step `manage-app` which carries out the following actions:

* Finds the `clusterID` of the cluster with the name provided by the `cluster_name` variable
* Checks to see if there's already an app with the name `app_name` based on the namespace `namespace` in the cluster `cluster_name`
  * If there is, then it exits 0 (success), as the app is already managed
* Moves the `namespace` within `cluster_name` under Astra Control management with the friendly name `app_name`
* Creates hourly, daily, weekly, and monthly protection policies

## Clone App

The [clone app](./astra-clone-app.yaml) template has a 3rd step `clone-app` which carries out the following actions:

* Finds the `clusterID` of the cluster with the name provided by the `cluster_name` variable
* Checks to ensure there's already an app with the name `app_name` based on the namespace `namespace` in the cluster `cluster_name`
  * If there is not, then it exits 1 (failure), as the app must be under management to clone
* Clones the app to a new namespace, with a name of `<app_name>-harness-clone-<pipeline.sequenceId>`
* Ensures that the clone succeeds and is under management, otherwise exits 1 (failure)

## Backup App

The [backup app](./astra-backup-app.yaml) template has a 3rd step `backup-app` which carries out the following actions:

* Finds the `clusterID` of the cluster with the name provided by the `cluster_name` variable
* Checks to ensure there's already an app with the name `app_name` based on the namespace `namespace` in the cluster `cluster_name`
  * If there is not, then it exits 0 (success) so the rest of the pipeline continues, but prints an error message to the console stating the app was not found
* Creates (and verifies) a backup of the Astra Control `app_name`

## Snapshot App

The [snapshot app](./astra-snapshot-app.yaml) template has a 3rd step `snapshot-app` which carries out the following actions:

* Finds the `clusterID` of the cluster with the name provided by the `cluster_name` variable
* Checks to ensure there's already an app with the name `app_name` based on the namespace `namespace` in the cluster `cluster_name`
  * If there is not, then it exits 0 (success) so the rest of the pipeline continues, but prints an error message to the console stating the app was not found
* Creates (and verifies) a snapshot of the Astra Control `app_name`
