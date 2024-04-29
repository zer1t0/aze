import argparse
import requests
from xml.etree import ElementTree
import json
import logging
from . import read_in

logger = logging.getLogger("aze")

def parse_args():
    parser = argparse.ArgumentParser(
        description="List blobs of container from URL."
    )

    parser.add_argument(
        "url",
        nargs="*",
        help="Specify blob container url or files. If None then stdin is used"
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

    for url in read_in.read_text_targets(args.url):
        marker = None
        while True:
            resp = request_container_files(url, marker)
            if resp.status_code != 200:
                logging.warning("Unable to list files in {}. Error code {}".format(
                    url, resp.status_code
                ))
                break

            for blob in extract_blobs(resp.text):
                blob["url"] = url + "/" + blob["name"]
                print(json.dumps(blob))

            marker = extract_marker(resp.text)
            if not marker:
                break

def request_container_files(url, marker=None):
    params = {
        "restype": "container",
        "comp": "list"
    }
    if marker:
        params["marker"] = marker

    resp = requests.get(
        url,
        params=params,
    )
    return resp

def extract_marker(text):
    root = ElementTree.fromstring(text)
    return root.find("NextMarker").text

def extract_blobs(text):
    root = ElementTree.fromstring(text)
    for blob in root.findall("Blobs/Blob"):
        name = blob.find("Name").text
        p = blob.find("Properties")
        last_modified = p.find("Last-Modified").text or ""
        etag = p.find("Etag").text or ""
        content_length = int(p.find("Content-Length").text)
        content_type = p.find("Content-Type").text or ""
        content_encoding = p.find("Content-Encoding").text or ""
        content_language = p.find("Content-Language").text or ""
        content_md5 = p.find("Content-MD5").text or ""
        cache_control = p.find("Cache-Control").text or ""
        content_disposition = p.find("Content-Disposition").text or ""
        blob_type = p.find("BlobType").text or ""
        lease_status = p.find("LeaseStatus").text or ""
        lease_state = p.find("LeaseState").text or ""

        yield {
            "name": name,
            "last_modified": last_modified,
            "etag": etag,
            "content_length": content_length,
            "content_type": content_type,
            "content_encoding": content_encoding,
            "content_language": content_language,
            "content_md5": content_md5,
            "cache_control": cache_control,
            "content_disposition": content_disposition,
            "blob_type": blob_type,
            "lease_status": lease_status,
            "lease_state": lease_state,
        }

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
