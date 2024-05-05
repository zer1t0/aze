from .request_az import request_az_api

def export_deployment_template(
        access_token,
        subscription_id,
        resource_group_name,
        deployment_name
):
    url = "https://management.azure.com/subscriptions/{}/resourcegroups/{}/providers/Microsoft.Resources/deployments/{}/exportTemplate?api-version=2021-04-01".format(subscription_id, resource_group_name, deployment_name)

    return request_az_api(url, access_token, method="POST")["template"]

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

def list_vm_extensions(
        access_token,
        subscription_id,
        resource_group_name,
        vm_name
):
    return request_az_api(
        "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachines/{}/extensions".format(
            subscription_id, resource_group_name, vm_name
        ),
        access_token,
        params={"api-version": "2024-03-01"},
    )["value"]

def list_vm_permissions(
        access_token,
        subscription_id,
        resource_group_name,
        vm_name
):
    return request_az_api(
        "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachines/{}/providers/Microsoft.Authorization/permissions".format(
            subscription_id, resource_group_name, vm_name
        ),
        access_token,
        params={"api-version": "2022-04-01"},
    )["value"]
