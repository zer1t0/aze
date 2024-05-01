import requests
from .error import AzeRequestError

def request_az_api_values_until_no_more(url, access_token):
    values = []
    next_link = url
    while next_link:
        resp = request_az_api(next_link, access_token)
        values.extend(resp["value"])
        next_link = resp.get("@odata.nextLink", "")

    return values

def request_az_api(url, access_token, method="GET", json=None):
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    if method.upper() == "POST":
        req = requests.post
    else:
        req = requests.get

    resp = req(
        url,
        headers=headers,
        json=json,
        # verify=False,
    )

    if resp.status_code != 200:
        raise AzeRequestError(
            "Error {} in response: {} ({})".format(
                resp.status_code,
                resp.json()["error"]["code"],
                resp.json()["error"]["message"],
        ))

    return resp.json()
