import requests
from . import utils

def resolve_tenant_id(tenant):
    if utils.is_valid_uuid(tenant):
        return tenant

    return request_tenant_id(domain)

def request_tenant_id(domain):
    url = "https://login.microsoftonline.com/{}/.well-known/openid-configuration".format(domain)
    resp = requests.get(url)
    if resp.status_code == 200:
        tenant_id = resp.json()["token_endpoint"][34:70]
        return tenant_id
    else:
        return ""
