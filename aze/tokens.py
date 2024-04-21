
from msal_extensions import FilePersistenceWithDataProtection,\
    KeychainPersistence, LibsecretPersistence, FilePersistence,\
    PersistedTokenCache
import os

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
