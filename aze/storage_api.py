import requests
from .error import AzeRequestError
from xml.etree import ElementTree

def download_blob(url, access_token=None):
    if access_token:
        headers = {
            "Authorization": "Bearer " + access_token,
            "x-ms-version": "2023-08-03",
        }
    else:
        headers = None

    resp = requests.get(
        url,
        headers=headers,
    )

    if resp.status_code != 200:
        raise AzeRequestError(
            "Unable to download file in {}. Error code {}".format(
                url, resp.status_code
            )
        )

    return resp.content

def list_blobs(url, access_token=None):
    marker = None
    while True:
        resp = request_container_files(
            url, marker=marker, access_token=access_token
        )
        if resp.status_code != 200:
            raise AzeRequestError(
                "Unable to list files in {}. Error code {}".format(
                    url, resp.status_code
                )
            )
            break

        yield from extract_blobs(resp.text)
        yield from extract_containers(resp.text)

        marker = extract_marker(resp.text)
        if not marker:
            break



def request_container_files(url, marker=None, access_token=None):
    params = {
        "restype": "container",
        "comp": "list"
    }
    if marker:
        params["marker"] = marker

    if access_token:
        headers = {
            "Authorization": "Bearer " + access_token,
            "x-ms-version": "2023-08-03",
        }
    else:
        headers = None

    resp = requests.get(
        url,
        params=params,
        headers=headers,
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
            "type": "blob",
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

def extract_containers(text):
    root = ElementTree.fromstring(text)
    for c in root.findall("Containers/Container"):
        name = c.find("Name").text
        p = c.find("Properties")
        last_modified = p.find("Last-Modified").text or ""
        etag = p.find("Etag").text or ""
        lease_status = p.find("LeaseStatus").text or ""
        lease_state = p.find("LeaseState").text or ""
        default_encryption_scope = p.find("DefaultEncryptionScope").text or ""
        deny_encryption_scope_override = p.find("DenyEncryptionScopeOverride").text or ""
        has_immutability_policy = p.find("HasImmutabilityPolicy").text or ""
        has_legal_hold = p.find("HasLegalHold").text or ""
        immutable_storage_with_versioning_enabled = p.find("ImmutableStorageWithVersioningEnabled").text or ""

        yield {
            "type": "container",
            "name": name,
            "last_modified": last_modified,
            "etag": etag,
            "lease_status": lease_status,
            "lease_state": lease_state,
            "default_encryption_scope": default_encryption_scope,
            "deny_encryption_scope_override": deny_encryption_scope_override,
            "has_immutability_policy": has_immutability_policy,
            "has_legal_hold": has_legal_hold,
            "immutable_storage_with_versioning_enabled": immutable_storage_with_versioning_enabled,
        }
