from .request_az import request_az_api, request_az_api_values_until_no_more


def add_secret_to_application(access_token, app_id):
    return request_az_api(
        "https://graph.microsoft.com/v1.0/applications/{}/addPassword".format(app_id),
        access_token,
        method="POST",
        json={
            "passwordCredential": {
                "displayName": "Password"
            }
        },
    )

def list_applications(access_token):
    return request_az_api(
        "https://graph.microsoft.com/v1.0/applications",
        access_token,
    )["value"]

def list_sp_app_role_asignments(access_token, sp_id=None, app_id=None):
    if sp_id:
        url = "https://graph.microsoft.com/v1.0/servicePrincipals/{}/appRoleAssignments".format(sp_id)
    elif app_id:
        url = "https://graph.microsoft.com/v1.0/servicePrincipals(appId='{}')/appRoleAssignments".format(app_id)

    else:
        raise ValueError("Must provide sp_id or app_id")

    return request_az_api(
        url,
        access_token,
    )["value"]

def list_user_memberof(access_token, user):
    return request_az_api(
        "https://graph.microsoft.com/v1.0/users/{}/memberOf".format(user),
        access_token,
    )["value"]

def show_ad_role(access_token, role_id):
    return request_az_api(
        "https://graph.microsoft.com/v1.0/directoryRoles/{}".format(role_id),
        access_token,
    )

def show_administrative_unit(access_token, au):
    return request_az_api(
        "https://graph.microsoft.com/v1.0/directory/administrativeUnits/{}".format(au),
        access_token,
    )

def list_administrative_unit_members(access_token, au):
    return request_az_api_values_until_no_more(
        "https://graph.microsoft.com/v1.0/directory/administrativeUnits/{}/members".format(au),
        access_token,
    )

def list_administrative_unit_role_members(access_token, au):
    return request_az_api_values_until_no_more(
        "https://graph.microsoft.com/v1.0/directory/administrativeUnits/{}/scopedRoleMembers".format(au),
        access_token,
    )
