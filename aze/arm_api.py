from .error import AzeError
import requests

def list_role_assigments(access_token, subscription):
    return request_az_api(
        "https://management.azure.com/subscriptions/{}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01".format(subscription),
        access_token
    )

def list_role_definitions(access_token, subscription):
    return request_az_api(
        "https://management.azure.com/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-05-01-preview".format(subscription),
        access_token,
    )


def list_subscriptions(access_token):
    return request_az_api(
        "https://management.azure.com/subscriptions?api-version=2019-11-01",
        access_token
    )

def request_az_api(url, access_token):
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }
    resp = requests.get(
        url,
        headers=headers,
        # verify=False,
    )

    if resp.status_code != 200:
        raise AzeError(
            "Error in response: {}".format(
                resp.status_code
        ))

    return resp.json()["value"]
