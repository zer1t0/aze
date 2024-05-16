#!/usr/bin/env python3

import requests
import argparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import sleep
import logging
import sys
from . import read_in

USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
TIMEOUT = 5
DELAY = 0
WORKERS_DEFAULT = 10
DEFAULT_DELAY = 0
STOP_ATTACK = 0
STOP_WHEN_THROTTLE = 1

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify that Microsoft managed email exists.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "username",
        help="username or file with email per line to process. "
        "If none then stdin will be use",
        nargs="*",
    )

    parser.add_argument(
        "-d", "--domain",
        help="If specified, usernames are not required to have domain.",
    )

    parser.add_argument(
        "-A", "--user-agent",
        default=USER_AGENT,
        help="User Agent to perform requests"
    )

    parser.add_argument(
        "-t", "--timeout",
        default=TIMEOUT,
        type=int,
        help="HTTP request timeout in seconds"
    )

    parser.add_argument(
        "--delay",
        default=DEFAULT_DELAY,
        type=int,
        help="Delay between requests in seconds. Default: {}".format(DEFAULT_DELAY),
    )

    parser.add_argument(
        "-w", "--workers",
        default=10,
        type=int,
        help="Number of concurrent workers"
    )

    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop if throttle error is returned",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="Verbosity",
        default=0
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    init_log(args.verbose)

    global TIMEOUT
    global USER_AGENT
    global DELAY
    global STOP_WHEN_THROTTLE

    TIMEOUT = args.timeout
    USER_AGENT = args.user_agent
    DELAY = args.delay
    STOP_WHEN_THROTTLE = args.stop_on_error
    domain = args.domain
    

    pool = ThreadPoolExecutor(args.workers)
    print_lock = Lock()

    for username in read_in.read_text_targets(args.username):
        if "@" not in username and domain:
            username += "@" + domain
        pool.submit(verify_email, username, print_lock)

def init_log(verbosity=0):

    if verbosity == 1:
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG
    else:
        level = logging.WARN

    logging.basicConfig(
        level=logging.ERROR,
        format="%(levelname)s:%(message)s"
    )
    logger.level = level


def verify_email(email, print_lock):
    if STOP_ATTACK:
        return
    if is_valid_email(email):
        with print_lock:
            print(email, flush=True)
    if DELAY:
        sleep(DELAY)

def is_valid_email(email):
    resp = request_getcredentialtype(email)
    jresp = resp.json()
    logger.debug(jresp)

    is_valid = jresp["IfExistsResult"] == 0

    if is_valid and jresp["ThrottleStatus"] != 0:
        logger.warn("Throttle detected for %s, email may not be valid", email)
        if STOP_WHEN_THROTTLE:
            global STOP_ATTACK
            STOP_ATTACK = 1
        is_valid = False

    return is_valid


URL = 'https://login.microsoftonline.com/common/GetCredentialType'
def request_getcredentialtype(email):
    headers = {
        'User-Agent': USER_AGENT
    }
    return requests.post(
        URL,
        json={"Username": email},
        timeout=TIMEOUT,
        headers=headers
    )
