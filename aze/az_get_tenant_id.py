#!/usr/bin/env python3
import argparse
import requests
import json
import re
from . import read_in

def parse_args():
    parser = argparse.ArgumentParser(
        description="Retrieves the Azure tenant id from tenant domain."
    )
    parser.add_argument(
        "domain",
        nargs="*",
        help="An Azure tenant domain. If none then stdin is used."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        for domain in read_in.read_text_targets(args.domain):
            tenant_id = request_tenant_id(domain)
            if tenant_id:
                print(tenant_id)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


def request_tenant_id(domain):
    url = "https://login.microsoftonline.com/{}/.well-known/openid-configuration".format(domain)
    resp = requests.get(url)
    if resp.status_code == 200:
        tenant_id = resp.json()["token_endpoint"][34:70]
        return tenant_id
    else:
        return ""
