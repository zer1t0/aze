import argparse
import json
import logging
from . import read_in
from . import profile
from . import tokens
from . import storage_api
from .error import AzeRequestError
import sys

logger = logging.getLogger("aze")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Download blob from URL.",
    )

    parser.add_argument(
        "url",
        help="Specify blob file url"
    )

    parser.add_argument(
        "-a", "--auth",
        help="Use the current login context for the operation.",
        action="store_true",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="Verbosity",
        default=0
    )

    return parser.parse_args()


def main():
    args = parse_args()
    init_log(args.verbose)

    if args.auth:
        default_sub = profile.get_profile_default_subscription()
        access_token_obj = tokens.search_token_for_subscription(
            default_sub,
            scopes=["https://storage.azure.com/.default"]
        )

        access_token = access_token_obj["secret"]
    else:
        access_token = None

    url = args.url
    blob_content = storage_api.download_blob(url, access_token)
    sys.stdout.buffer.write(blob_content)

def init_log(verbosity=0, log_file=None):

    if verbosity == 1:
        level = logging.INFO
    elif verbosity > 2:
        level = logging.DEBUG
    else:
        level = logging.WARN

    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(levelname)s:%(name)s:%(message)s"
    )
