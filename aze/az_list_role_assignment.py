import argparse
from . import arm_api
import json
from . import profile
from .tokens import search_token_for_subscription
from . import arm_api

def parse_args():
    parser = argparse.ArgumentParser(
        "List roles without requiring a graph access token."
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://management.core.windows.net//.default"]
    )

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



