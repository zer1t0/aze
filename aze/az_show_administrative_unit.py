import argparse
from . import graph_api
from . import profile
from .tokens import search_token_for_subscription
import json

def parse_args():
    parser = argparse.ArgumentParser(
        "Show Administrative Unit",
    )

    parser.add_argument(
        "au",
        help="Administrative unit id",
    )

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    au = args.au

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://graph.microsoft.com//.default"]
    )

    access_token_raw = access_token_obj["secret"]

    resp = graph_api.show_administrative_unit(access_token_raw, au)

    print(json.dumps(resp, indent=4))

