# Base Classes

In all likelyhood these classes will not need to be invoked on their own, rather their child classes should be called.  However, it may be necessary to change the default code behavior for [reading in the credentials configuration file](#getConfig) or the [base SDK / API class](#SDKCommon).

## getConfig

`getConfig` reads in the `config.yaml` file from the following locations (in order):

1. The directory that astraSDK.py is located in
1. `~/.config/astra-toolkits/`
1. `/etc/astra-toolkits/`
1. The directory pointed to by the shell env var `ASTRATOOLKITS_CONF`

It then sets the `base` url, `headers`, and `verifySSL` values based on the `config.yaml` file.

## SDKCommon

The SDKCommon class is the parent class for all other classes within `astraSDK.py`.  It relies on the values set via [getConfig](#getConfig), and has the below functions.

## apicall

`apicall` uses the [requests](https://pypi.org/project/requests/) module to make API calls.

## jsonifyResults

`jsonifyResults` takes in an API response, and returns a JSON object, with error handling.

## preflight

`preflight` performs a `get` on `topology/v1/clouds` to validate that the access information in the `config.yaml` file is valid.
