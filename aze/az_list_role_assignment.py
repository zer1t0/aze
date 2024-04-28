import argparse
from . import arm_api
import json
from . import profile
from .tokens import search_token_in_cache, CredentialType
from . import arm_api

def parse_args():
    parser = argparse.ArgumentParser(
        "List roles without requiring a graph access token."
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    default_sub = get_profile_default_subscription()
    account = search_token_in_cache(
        CredentialType.ACCOUNT,
        query={
            "username": default_sub["user"]["name"],
            "realm": default_sub["tenantId"],
        }
    )[0]

    access_token_obj = search_token_in_cache(
        CredentialType.ACCESS_TOKEN,
        query={"home_account_id": account["home_account_id"]},
        scopes=["https://management.core.windows.net//.default"]
    )[0]

    access_token_raw = access_token_obj["secret"]

    roles = arm_api.list_role_assigments(access_token_raw, default_sub["id"])

    role_definitions = arm_api.list_role_definitions(access_token_raw, default_sub["id"])
    role_definitions = {
        r["id"]: r for r in role_definitions
    }


    for role in roles:
        definition_id = role["properties"]["roleDefinitionId"]
        role_def_properties = role_definitions[definition_id]["properties"]
        role["properties"]["roleProperties"] = role_def_properties

    print(json.dumps(roles, indent=4))

def get_profile_default_subscription():
    subs = profile.load_profile()["subscriptions"]
    for s in subs:
        if s.get("isDefault", False):
            return s

    raise KeyError("No default subscription found")



