from .request_az import request_az_api

def list_role_assigments(access_token, subscription):
    return request_az_api(
        "https://management.azure.com/subscriptions/{}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01".format(subscription),
        access_token
    )["value"]

def list_role_definitions(access_token, subscription):
    return request_az_api(
        "https://management.azure.com/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-05-01-preview".format(subscription),
        access_token,
    )["value"]


def list_subscriptions(access_token):
    return request_az_api(
        "https://management.azure.com/subscriptions?api-version=2019-11-01",
        access_token
    )["value"]
