import argparse
from . import arm_api
import json
from . import profile
from .tokens import search_token_for_subscription
from . import arm_api, graph_api
from .error import AzeRequestError
import logging

logger = logging.getLogger("aze")

def parse_args():
    parser = argparse.ArgumentParser(
        "Try to add a secret to all applications."
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        help="Verbosity",
        default=0
    )

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    init_log(args.verbose)

    default_sub = profile.get_profile_default_subscription()
    access_token_obj = search_token_for_subscription(
        default_sub,
        scopes=["https://graph.microsoft.com//.default"]
    )
    access_token_raw = access_token_obj["secret"]
    applications = graph_api.list_applications(access_token_raw)

    for app in applications:
        try:
            logging.info("Try to add secret to app {} ({})".format(
                app["id"], app["displayName"]
            ))
            resp = graph_api.add_secret_to_application(access_token_raw, app["id"])
            resp["app"] = {
                "id": app["id"],
                "displayName": app["displayName"]
            }
            print(json.dumps(resp, indent=4))
        except AzeRequestError as e:
            logging.debug("Error {}".format(e))


def init_log(verbosity=0, log_file=None):

    if verbosity == 1:
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG
    else:
        level = logging.WARN

    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(levelname)s:%(message)s"
    )
