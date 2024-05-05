import argparse
import requests
import configparser
import os
from . import utils
from .tenant import resolve_tenant_id
from .error import AzeError
from . import arm_api
from . import profile
from . import tokens
from .tokens import TokenInformation, load_token_cache, store_tokens, request_tokens_from_refresh

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
    elif refresh_token:
        if not tenant:
            utils.eprint("--tenant required when using refresh token")
            return -1
        tenant_id = resolve_tenant_id(tenant)
        tokens = request_tokens_from_refresh(
            tenant_id,
            refresh_token,
            "https://management.core.windows.net//.default offline_access openid profile",
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
        t_infos = [at_info]

    for t_info in t_infos:
        if t_info.endpoint == "https://management.core.windows.net/"\
           or t_info["aud"] == "https://management.azure.com/":
            resp_subscriptions = arm_api.list_subscriptions(
                t_info.access_token
            )
            break

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

