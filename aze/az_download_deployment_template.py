import argparse
from . import arm_api
from . import profile
from .tokens import search_token_for_subscription
import json

def parse_args():
    parser = argparse.ArgumentParser(
        "Download a deployment template.",
    )

    parser.add_argument(
        "-n", "--name",
        help="Deployment name",
        required=True,
    )

    parser.add_argument(
        "-g", "--resource-group",
        help="Resource group name",
        required=True,
    )

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    group = args.resource_group
    deployment = args.name

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://management.core.windows.net//.default"]
    )

    access_token_raw = access_token_obj["secret"]

    resp = arm_api.export_deployment_template(
        access_token_raw,
        default_sub["id"],
        group,
        deployment
    )

    print(json.dumps(resp, indent=4))

