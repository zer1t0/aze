import argparse
import requests
import json
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="Retrieve login information about an Azure domain"
    )
    parser.add_argument(
        "domain",
        help="Domain to search Azure login information",
    )
    parser.add_argument(
        "-u", "--user",
        help="User to use in requests (do not include the domain part)",
        default="nn"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    username = "{}@{}".format(args.user, args.domain)

    r1 = get_userrealm_v1(username)
    # print(json.dumps(r1))
    r2 = get_userrealm_v2(username)
    # print(json.dumps(r2))
    r3 = get_getuserrealm(username)
    # print(json.dumps(r3))
    r4 = get_getcredentialtype(username)
    # print(json.dumps(r4))

    tenant_branding_info = (r2.get("TenantBrandingInfo", None) or [{}])[0]

    attributes = {
        "Account Type": r1["account_type"], # Managed or federated
        "Domain Name": r1["domain_name"],
        "Cloud Instance": r1["cloud_instance_name"],
        "Cloud Instance audience urn": r1["cloud_audience_urn"],
        "Federation Brand Name": r2["FederationBrandName"],
        "Tenant Locale": tenant_branding_info.get("Locale", ""),
        "Tenant Banner Logo": tenant_branding_info.get("BannerLogo", ""),
        "Tenant Banner Illustration": tenant_branding_info.get("Illustration", ""),
        "State": r3["State"],
        "User State": r3["UserState"],
        "Exists": r4["IfExistsResult"],
        "Throttle Status": r4["ThrottleStatus"],
        "Pref Credential": r4["Credentials"]["PrefCredential"],
        "Has Password": r4["Credentials"]["HasPassword"],
        "Domain Type": r4["EstsProperties"]["DomainType"],
        "Federation Protocol": r1.get("federation_protocol", ""),
        "Federation Metadata Url": r1.get("federation_metadata_url", ""),
        "Federation Active Authentication Url": r1.get("federation_active_auth_url", ""),
        "Authentication Url": r2.get("AuthUrl", ""),
        "Consumer Domain": r2.get("ConsumerDomain", ""),
        "Federation Global Version": r3.get("FederationGlobalVersion", ""),
        "Desktop Sso Enabled": r4["EstsProperties"].get("DesktopSsoEnabled", ""),
    }

    print(json.dumps(attributes, indent=4))



def get_userrealm_v1(username):
    url = "https://login.microsoftonline.com/common/userrealm/{}?api-version=1.0".format(username)
    resp = requests.get(url)
    return resp.json()

def get_userrealm_v2(username):
    url = "https://login.microsoftonline.com/common/userrealm/{}?api-version=2.0".format(username)
    resp = requests.get(url)
    return resp.json()

def get_getuserrealm(username):
    url = "https://login.microsoftonline.com/GetUserRealm.srf?login={}".format(
        username
    )
    resp = requests.get(url)
    return resp.json()

def get_getcredentialtype(username):
    url = "https://login.microsoftonline.com/common/GetCredentialType"
    resp = requests.post(url, json={
        "username": username,
        "isOtherIdpSupported": True,
        "checkPhones": True,
        "isRemoteNGCSupported": False,
        "isCookieBannerShown": False,
        "isFidoSupported": False,
        "originalRequest": "",
        "flowToken": "",
    })
    return resp.json()
