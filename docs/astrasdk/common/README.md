# Common

In all likelyhood these classes will not need to be invoked on their own, rather their child classes should be called.  However, it may be necessary to change the default code behavior for [reading in the credentials configuration file](#getConfig) or the [base SDK / API class](#SDKCommon).

## getConfig

`getConfig` reads in the `config.yaml` file from the following locations (in order):

1. The directory that astraSDK.py is located in
1. `~/.config/astra-toolkits/`
1. `/etc/astra-toolkits/`
1. The directory pointed to by the shell env var `ASTRATOOLKITS_CONF`

It then sets the following values based on the `config.yaml` file:

* `self.base`: The URL of the Astra Control instance, including the project, hostname, '/accounts/' and account UID
* `self.headers`: The authorization headers for the Astra Control user
* `self.verifySSL`: A bool for whether or not to verify SSL headers when making API calls (useful for Astra Control Center)

## SDKCommon

The SDKCommon class is the parent class for all other classes within `astraSDK.py`.  It relies on the values set via [getConfig](#getConfig), and has the below functions.

### apicall

`apicall` uses the [requests](https://pypi.org/project/requests/) module to make API calls.

### jsonifyResults

`jsonifyResults` takes in an API response, and returns a JSON object (python dict), with error handling.

### printVerbose

`printVerbose` is used by child classes to print [colored](https://pypi.org/project/colored/) text when `verbose=True` (useful for debugging).

### basicTable

`basicTable` is used by some child classes to collate data for printing tables to the terminal.
