
from msal_extensions import FilePersistenceWithDataProtection,\
    KeychainPersistence, LibsecretPersistence, FilePersistence,\
    PersistedTokenCache
import os
from .error import AzeError

CredentialType = PersistedTokenCache.CredentialType

# class CredentialType:
#         ACCESS_TOKEN = "AccessToken"
#         REFRESH_TOKEN = "RefreshToken"
#         ACCOUNT = "Account"  # Not exactly a credential type, but we put it here
#         ID_TOKEN = "IdToken"
#         APP_METADATA = "AppMetadata"

def search_token_for_subscription(subscription, scopes, token_cache=None):
    token_cache = token_cache or load_token_cache()

    if subscription["id"] == subscription["tenantId"]:
        realm = subscription["id"]
    else:
        realm = "organizations"

    accounts = search_token_in_cache(
        CredentialType.ACCOUNT,
        query={
            "username": subscription["user"]["name"],
            "realm": realm,
        },
        token_cache=token_cache,
    )
    if not accounts:
        raise AzeError("Unable to find account for subscription")

    account = accounts[0]

    access_tokens = search_token_in_cache(
        CredentialType.ACCESS_TOKEN,
        query={"home_account_id": account["home_account_id"]},
        scopes=scopes,
        token_cache=token_cache,
    )

    if not access_tokens:
        raise AzeError(
            "Unable to find Access Token for account '{}' with scope '{}'".format(
                account["home_account_id"],
                ", ".join(scopes),
        ))

    return access_tokens[0]

def search_token_in_cache(
        token_type,
        query=None,
        scopes=None,
        token_cache=None
):
    token_cache = token_cache or load_token_cache()
    return token_cache.find(token_type, query=query, target=scopes)


def load_token_cache(encrypted=False):
    azure_dir = os.path.join(os.environ["HOME"], ".azure")
    extension = "json" if not encrypted else "bin"
    return load_persisted_token_cache(
        os.path.join(azure_dir, "msal_token_cache.{}".format(extension)),
        encrypted
    )


def load_persisted_token_cache(location, encrypt):
    persistence = build_persistence(location, encrypt)
    return PersistedTokenCache(persistence)

def build_persistence(location, encrypt):
    if encrypt:
        if sys.platform.startswith('win'):
            return FilePersistenceWithDataProtection(location)
        if sys.platform.startswith('darwin'):
            return KeychainPersistence(
                location,
                "my_service_name",
                "my_account_name"
            )
        if sys.platform.startswith('linux'):
            return LibsecretPersistence(
                location,
                schema_name="my_schema_name",
                attributes={"my_attr1": "foo", "my_attr2": "bar"}
            )
    else:
        return FilePersistence(location)
