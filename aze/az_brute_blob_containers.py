import argparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import sys
import logging
from . import read_in
from .permutations import DEFAULT_PERMUTATIONS
import requests
from xml.etree import ElementTree

logger = logging.getLogger("aze")

DEFAULT_WORKERS = 2

def parse_args():
    parser = argparse.ArgumentParser(
        description="Discover public containers in Azure blobs.",
    )
    parser.add_argument(
        "blobs",
        nargs="*",
        help="Specify blob domains or files. If None then stdin is used"
    )

    parser.add_argument(
        "-w", "--workers",
        default=DEFAULT_WORKERS,
        type=int,
        help="Number of concurrent workers. Default: {}".format(DEFAULT_WORKERS)
    )

    parser.add_argument(
        "-W", "--wordlist",
        nargs="*",
        help="Words or file with words per line to check folder names."\
        " If none, default wordlist will be used.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=5000,
        help="Timeout milliseconds, default 5000"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="Verbosity",
        default=0
    )

    args = parser.parse_args()
    args.timeout = args.timeout / 1000

    return args

def main():
    args = parse_args()
    init_log(args.verbose)

    pool = ThreadPoolExecutor(args.workers)
    print_lock = Lock()

    if args.wordlist:
        words = list(read_in.read_text_targets(
            args.wordlist,
            use_stdin_if_none=False,
            use_stdin_if_minus=False,
        ))
    else:
        words = DEFAULT_PERMUTATIONS

    timeout = args.timeout

    try:
        for blob_domain in read_in.read_text_targets(args.blobs):
            for word in words:
                pool.submit(
                    check_blob,
                    blob_domain,
                    word,
                    timeout,
                    print_lock,
                )
    except (KeyboardInterrupt, BrokenPipeError):
        pass

def check_blob(blob_domain, folder, timeout, print_lock):
    url = "https://{}/{}".format(blob_domain, folder).lower()
    logging.info("Checking {}".format(url))
    resp = requests.get(
        url,
        params={
            "restype": "container",
            "comp": "list"
        },
        timeout=timeout
    )

    if resp.status_code != 200:
        return

    with print_lock:
        print(url)

    filenames = extract_filenames(resp.text)
    logging.info("{} {} files found: {}".format(
        url,
        len(filenames),
        ",".join(filenames)
    ))

def extract_filenames(text):
    root = ElementTree.fromstring(text)
    return [n.text for n in root.findall("./Blobs/Blob/Name")]

def init_log(verbosity=0, log_file=None):

    if verbosity == 1:
        level = logging.WARN
    elif verbosity == 2:
        level = logging.INFO
    elif verbosity > 2:
        level = logging.DEBUG
    else:
        level = logging.ERROR

    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(levelname)s:%(name)s:%(message)s"
    )


