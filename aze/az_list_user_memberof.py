import argparse
from . import graph_api
from . import profile
from .tokens import search_token_for_subscription
import json

def parse_args():
    parser = argparse.ArgumentParser(
        "List membership of user, both groups and administrative units."
    )

    parser.add_argument(
        "user",
        help="User principal name or id",
    )

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    user = args.user

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://graph.microsoft.com//.default"]
    )

    access_token_raw = access_token_obj["secret"]

    resp = graph_api.list_user_memberof(access_token_raw, user)

    print(json.dumps(resp, indent=4))

