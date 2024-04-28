import argparse
from . import arm_api
import json
from . import profile
from .tokens import search_token_for_subscription
from . import arm_api, graph_api

def parse_args():
    parser = argparse.ArgumentParser(
        "List App roles for a service principal."
    )

    parser.add_argument("id", help="Service Principal ID")

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    sp_id = args.id

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://graph.microsoft.com//.default"]
    )
    access_token_raw = access_token_obj["secret"]
    roles = graph_api.list_sp_app_role_asignments(access_token_raw, sp_id)

    print(json.dumps(roles, indent=4))

