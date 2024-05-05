import argparse
from . import arm_api
from . import profile
from .tokens import search_token_for_subscription
import json

def parse_args():
    parser = argparse.ArgumentParser(
        "List virtual machine permissions."
    )

    parser.add_argument(
        "-g","--resource-group",
        help="VM Resource group name",
    )

    parser.add_argument(
        "--vm-name",
        help="VM name",
    )

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    resource_group_name = args.resource_group
    vm_name = args.vm_name

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://management.core.windows.net//.default"]
    )

    access_token_raw = access_token_obj["secret"]

    resp = arm_api.list_vm_permissions(
        access_token_raw,
        default_sub["id"],
        resource_group_name,
        vm_name,
    )

    print(json.dumps(resp, indent=4))

