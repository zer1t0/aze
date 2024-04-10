# AZE (Azure Cli Enhacement)

Extended utilities for azure management.

A python package intended to be used along with Azure Cli to expand its
capabilities, even if many commands are completely independent from Azure Cli.


## Commands

AZE includes the following commands:

- **az-get-login-info**: Retrieve login information about an Azure domain.
- **az-inspect-token**: Show access token (jwt) payload in json format.
- **az-login-with-token**: Adds tokens directly into Azure Cli token cache.
- **az-tenant-id**: Retrieves the tenant id from tenant domain.
- **az-whoami**: Shorcut for "az ad signed-in-user show".

## Install

```
pip install zer1t0-aze
```

## Development

To probe in a development scenario:
```
cd aze/
pip install -e .
```
