import argparse
import json
import base64
from . import utils

def parse_args():
    parser = argparse.ArgumentParser(
        description="Show access token (jwt) payload in json format."
    )
    parser.add_argument(
        "token",
        help="Access Token to inspect"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    token = args.token
    jwt_header, jwt_payload, jwt_signature = token.split(".")
    jpay = json.loads(base64.b64decode(
        utils.add_b64_padding(jwt_payload)
    ).decode())
    print(json.dumps(jpay, indent=4))

