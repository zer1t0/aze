# AZE (Azure Cli Enhacement)

Extended utilities for azure management.

A python package intended to be used along with Azure Cli to expand its
capabilities, even if many commands are completely independent from Azure Cli.


## Commands

AZE includes the following commands, many of them require to be
authenticated (marked with Auth) in Azure:

- **az-brute-add-app-secret**: Try to add a secret to all applications (Auth).
- **az-brute-usernames**: Validates if a email is Microsoft managed (No auth).
- **az-brute-passwords**: Validate Azure credentials (No auth).
- **az-brute-service-subdomains**: Check if any Azure service is using the given
  subdomains (No auth).
- **az-get-login-info**: Retrieve login information about an Azure domain (No auth).
- **az-get-tenant-domains**: Discover the domains associated with a tenant (No auth).
- **az-get-tenant-id**: Retrieves the tenant id from tenant domain (No auth).
- **az-inspect-token**: Show access token (jwt) payload in json format (No auth).
- **az-list-role-assignment**: List roles without requiring a graph access token (Auth).
- **az-login-with-token**: Adds tokens directly into Azure Cli token cache.
- **az-list-sp-app-role-assignment**: List App roles for a service principal.
- **az-search-token-in-cache**: Retrieve items from token cache based on the filters.
- **az-whoami**: Shorcut for "az ad signed-in-user show".

## Installation

```
pip install zer1t0-aze
```

## Development

For development, debugging or testing:
```
cd aze/
pip install -e .
```

## Credits
- [AADInternals](https://github.com/Gerenios/AADInternals)
- [MicroBurst](https://github.com/NetSPI/MicroBurst)
- [MSOLSpray](https://github.com/dafthack/MSOLSpray)
- [o365creeper](https://github.com/LMGsec/o365creeper)
