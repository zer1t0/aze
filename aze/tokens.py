
from msal_extensions import FilePersistenceWithDataProtection,\
    KeychainPersistence, LibsecretPersistence, FilePersistence,\
    PersistedTokenCache
import os
from .error import AzeError
from . import utils
import requests
import json
import base64
import time

CredentialType = PersistedTokenCache.CredentialType

# class CredentialType:
#         ACCESS_TOKEN = "AccessToken"
#         REFRESH_TOKEN = "RefreshToken"
#         ACCOUNT = "Account"  # Not exactly a credential type, but we put it here
#         ID_TOKEN = "IdToken"
#         APP_METADATA = "AppMetadata"

def search_token_for_subscription(subscription, scopes, token_cache=None):
    token_cache = token_cache or load_token_cache()

    query = {
        "username": subscription["user"]["name"],
        "realm": subscription["tenantId"],
    }

    accounts = search_token_in_cache(
        CredentialType.ACCOUNT,
        query=query,
        token_cache=token_cache,
    )
    if not accounts and subscription["id"] != subscription["tenantId"]:
        query["realm"] = "organizations"
        accounts = search_token_in_cache(
            CredentialType.ACCOUNT,
            query=query,
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
        refresh_token_obj = search_token_in_cache(
            CredentialType.REFRESH_TOKEN,
            query={"home_account_id": account["home_account_id"]},
            token_cache=token_cache,
        )
        if not refresh_token_obj:
            raise AzeError(
                "Unable to find Access Token (or Refresh Token) for account '{}' with scope '{}'".format(
                    account["home_account_id"],
                    ", ".join(scopes),
                ))

        tokens = request_tokens_from_refresh(
            subscription["tenantId"],
            refresh_token_obj[0]["secret"],
            " ".join(scopes),
        )

        at_info = TokenInformation(
            tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            id_token=tokens["id_token"],
            scope=tokens["scope"],
            client_info=tokens["client_info"],
            expires_in=tokens["expires_in"],
            ext_expires_in=tokens["ext_expires_in"],
        )

        store_tokens([at_info], token_cache)

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


def request_tokens_from_refresh(tenant_id, refresh_token, scope):
    url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(
        tenant_id
    )
    data = {
        "client_id": utils.AZCLI_ID,
        "grant_type": "refresh_token",
        "client_info": 1,
        "claims": '{"access_token": {"xms_cc": {"values": ["CP1"]}}}',
        "refresh_token": refresh_token,
        "scope": scope
    }

    resp = requests.post(url, data)
    if resp.status_code != 200:
        raise AzeError(
            "Unable to get access token, error {}: {} - {}".format(
                resp.status_code,
                resp.json().get("error", ""),
                resp.json().get("error_description", "")
            )
        )

    return resp.json()



def store_tokens(tokens_info, token_cache):
    if not tokens_info:
        return

    tokens_events = [create_event_from_token_info(t_info) for t_info in tokens_info]
    for t_event in tokens_events:
        token_cache.add(t_event)


class TokenInformation:

    def __init__(
            self,
            access_token,
            refresh_token=None,
            id_token=None,
            scope=None,
            client_info=None,
            expires_in=None,
            ext_expires_in=None,
    ):
        self.access_token = access_token
        jwt_header, jwt_payload, jwt_sign = access_token.split(".")
        self._info = json.loads(base64.b64decode(
            utils.add_b64_padding(jwt_payload)
        ).decode())

        self._scope = scope
        self.id_token = id_token
        self.refresh_token = refresh_token

        self.tenant_id = self._info["tid"]

        if "upn" in self._info:
            self.username = self._info["upn"]
            self.account_id = self._info["oid"]
        else:
            self.username = self._info["appid"]
            self.account_id = self._info["appid"]

        self.endpoint = aud_to_endpoint(self._info["aud"])

        if client_info:
            self.client_info = client_info
        else:
            self.client_info = base64.b64encode(json.dumps({
                "uid": self.account_id,
                "utid": self.tenant_id,
            }).encode()).decode()

        now = int(time.time())
        if expires_in:
            self.expires_in = expires_in
        else:
            self.expires_in = int(self._info["exp"]) - now

        if ext_expires_in:
            self.ext_expires_in = ext_expires_in
        else:
            self.ext_expires_in = self.expires_in


    def __getitem__(self,key):
        return self._info[key]

    def get(self, *args, **kwargs):
        return self._info.get(*args, **kwargs)

    @property
    def scopes(self):
        if self._scope:
            scopes = self._scope.split()
        else:
            endpoint = self.endpoint
            scopes = ["{}/.default".format(endpoint)]
            try:
                for scope in self._info["scp"].split():
                    if scope in ["email", "profile", "openid"]:
                        scopes.append(scope)
                    else:
                        scopes.append("{}/{}".format(endpoint, scope))
            except KeyError:
                pass
        return scopes

def aud_to_endpoint(aud):
    # Seems that management.azure.com is the new endpoint
    # but still not used by Azure Cli, so we replace it
    # with the old endpoint to make it compatible
    if aud.startswith("https://management.azure.com"):
        return "https://management.core.windows.net/"

    return aud

def create_event_from_token_info(t_info):
    scopes = t_info.scopes
    resp = {
        "token_type": "Bearer",
        "scope": scopes,
        "access_token": t_info.access_token,
        "expires_in": t_info.expires_in,
        "ext_expires_in": t_info.ext_expires_in,
        "client_info": t_info.client_info,
    }

    if t_info.refresh_token:
        resp["refresh_token"] = t_info.refresh_token
    if t_info.id_token:
        resp["id_token"] = t_info.id_token

    # No matter what is t_info["appid"] since we tell the Azure Cli
    # to use the token as it belongs to it
    client_id = utils.AZCLI_ID
    username = t_info.username
    tenant_id = t_info.tenant_id
    return {
        "username": username,
        "environment": "login.microsoftonline.com",
        "client_id": client_id,
        "scope": scopes,
        "token_endpoint": "https://login.microsoftonline.com/{}".format(tenant_id),
        "grant_type": "",
        "response": resp,
        # "params": {},
        # "data": {},
    }

