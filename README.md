# AZE (Azure Cli Enhacement)

Extended utilities for azure management.

A python package intended to be used along with Azure Cli to expand its
capabilities, even if many commands are completely independent from Azure Cli.


## Commands

AZE includes the following commands, many of them require to be
authenticated (marked with Auth) in Azure:

- **az-brute-add-app-secret**: Try to add a secret to all applications (Auth).
- **az-brute-passwords**: Validate Azure credentials (No auth).
- **az-brute-usernames**: Validates if a email is Microsoft managed (No auth).
- **az-brute-service-subdomains**: Check if any Azure service is using the given
  subdomains. (No auth)
- **az-brute-blob-containers**: Discover public containers in Azure blobs. (No auth)
- **az-download-blob**: Download blob from URL. (Auth with -a parameter)
- **az-download-deployment-template**: Download a deployment template. (Auth)
- **az-get-login-info**: Retrieve login information about an Azure domain (No auth).
- **az-get-tenant-domains**: Discover the domains associated with a tenant (No auth).
- **az-get-tenant-id**: Retrieves the tenant id from tenant domain (No auth).
- **az-inspect-token**: Show access token (jwt) payload in json format (No auth).
- **az-list-blobs**: List blobs or containers from URL. (Auth with -a parameter)
- **az-list-administrative-unit-members**: List Administrative Unit members (Auth).
- **az-list-administrative-unit-role-members**: List Administrative Unit scoped role members (Auth).
- **az-list-role-assignment**: List roles without requiring a graph access token. (Auth)
- **az-list-sp-app-role-assignment**: List App roles for a service principal. (Auth)
- **az-list-user-memberof**: List membership of user, both groups and administrative units. (Auth)
- **az-list-vm-extensions**: List virtual machine extensions. (Auth)
- **az-list-vm-permissions**: List virtual machine permissions. (Auth)
- **az-login-with-token**: Injects tokens directly into Azure Cli token cache.
- **az-search-token-in-cache**: Retrieve items from token cache based on the filters.
- **az-show-ad-role**: Show Entra ID role. (Auth)
- **az-show-administrative-unit**: Show Administrative Unit. (Auth)
- **az-whoami**: Shorcut for "az ad signed-in-user show". (Auth)

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
- [OffensiveCloud](https://github.com/lutzenfried/OffensiveCloud)
