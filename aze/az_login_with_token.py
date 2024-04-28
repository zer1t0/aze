import argparse
import requests
import base64
import json
import time
import configparser
import os
from . import utils
from .tenant import resolve_tenant_id
from .error import AzeError
from .tokens import load_token_cache
from . import arm_api
from . import profile

def parse_args():
    parser = argparse.ArgumentParser(description="Login with Azure Tokens")
    main_token_group = parser.add_mutually_exclusive_group(required=True)
    main_token_group.add_argument(
        "-a", "--access-token",
        help="Access token for any Azure service.",
        action='append',
    )
    main_token_group.add_argument(
        "-r", "--refresh-token",
        help="Refresh token",
    )

    parser.add_argument(
        "--tenant",
        help="Tenant domain or ID. Required when refresh token is used."
    )

    return parser.parse_args()

def main():
    args = parse_args()
    access_tokens = args.access_token
    refresh_token = args.refresh_token
    tenant = args.tenant


    resp_subscriptions = []
    if access_tokens:
        t_infos = [TokenInformation(at) for at in access_tokens]
        for t_info in t_infos:
            if t_info.endpoint == "https://management.core.windows.net/"\
               or t_info["aud"] == "https://management.azure.com/":
                resp_subscriptions = arm_api.list_subscriptions(
                    t_info.access_token
                )
                break
    elif refresh_token:
        if not tenant:
            utils.eprint("--tenant required when using refresh token")
            return -1
        tenant_id = resolve_tenant_id(tenant)
        tokens = request_tokens_from_refresh(tenant_id, refresh_token)

        at_info = TokenInformation(
            tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            id_token=tokens["id_token"],
            scope=tokens["scope"],
            client_info=tokens["client_info"],
            expires_in=tokens["expires_in"],
            ext_expires_in=tokens["ext_expires_in"],
        )
        t_infos = [at_info]

    token_cache = load_token_cache()
    store_tokens(t_infos, token_cache)
    set_subscriptions(t_infos[0], resp_subscriptions)




# A simple implementation of Profile._set_subscriptions
# https://github.com/Azure/azure-cli/blob/6771b2b1ef04ed2f8e71b636eccce5cf68a7d76d/src/azure-cli-core/azure/cli/core/_profile.py#L454
def set_subscriptions(at_info, resp_subscriptions):
    default_subscription_id = store_profiles(at_info, resp_subscriptions)
    set_default_subscription_id(default_subscription_id)

AZURE_CLOUD = "AzureCloud"

def store_profiles(at_info, resp_subscriptions):
    tenant_id = at_info["tid"]
    username = at_info.username

    # To use tokens user type must be "user" since "servicePrincipal"
    # is reserved to use the secrets store
    user_type = "user"

    profile_data = profile.load_profile()

    cached_subscriptions = {}
    for sub in profile_data["subscriptions"]:
        sub["isDefault"] = False
        cached_subscriptions[sub["id"]] = sub


    can_be_default = True
    new_subscriptions = {}
    if resp_subscriptions:
        for rsub in resp_subscriptions:
            sub_id = rsub["subscriptionId"]
            state = rsub["state"]
            is_default = state == "Enabled" and can_be_default
            if is_default:
                can_be_default = False

            new_subscriptions[sub_id] = {
                "id": sub_id,
                "name": rsub["displayName"],
                "state": state,
                "isDefault": is_default,
                "tenantId": tenant_id,
                "environmentName": AZURE_CLOUD,
                "user": {
                    "name": username,
                    "type": user_type,
                }
            }
    else:
        new_subscriptions[tenant_id] = {
            "id": tenant_id,
            "name": "N/A(tenant level account)",
            "state": "Enabled",
            "isDefault": True,
            "tenantId": tenant_id,
            "environmentName": AZURE_CLOUD,
            "user": {
                "name": username,
                "type": user_type,
            }
        }

    cached_subscriptions.update(new_subscriptions)
    default_subscription_id = [
        s["id"]
        for s in cached_subscriptions.values()
        if s["isDefault"]
    ][0]
    profile_data["subscriptions"] = list(cached_subscriptions.values())

    profile.store_profile(profile_data)
    return default_subscription_id

def set_default_subscription_id(default_subscription_id):
    config_file = "{}/.azure/clouds.config".format(os.environ["HOME"])
    config = configparser.ConfigParser()
    config.read(config_file)
    config.set(AZURE_CLOUD, "subscription", default_subscription_id)

    with open(config_file, 'w') as fo:
        config.write(fo)


AZCLI_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"

def request_tokens_from_refresh(tenant_id, refresh_token):
    url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(
        tenant_id
    )
    data = {
        "client_id": AZCLI_ID,
        "grant_type": "refresh_token",
        "client_info": 1,
        "claims": '{"access_token": {"xms_cc": {"values": ["CP1"]}}}',
        "refresh_token": refresh_token,
        "scope": "https://management.core.windows.net//.default offline_access openid profile",
    }

    resp = requests.post(url, data)
    if resp.status_code != 200:
        raise AzeError(
            "Unable to get access token: error code {}".format(resp.status_code)
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

    @property
    def account_id(self):
        if self._info["idtyp"] == "app":
            return self._info["appid"]
        else:
            return self._info["oid"]

    @property
    def username(self):
        if self._info["idtyp"] == "app":
            return self._info["appid"]
        else:
            return self._info["upn"]

    @property
    def endpoint(self):
        endpoint = self._info["aud"]

        # Seems that management.azure.com is the new endpoint
        # but still not used by Azure Cli, so we replace it
        # for the old endpoint to make it compatible
        if endpoint == "https://management.azure.com/":
            return "https://management.core.windows.net/"
        return endpoint


    @property
    def tenant_id(self):
        return self._info["tid"]

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
    client_id = AZCLI_ID
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

