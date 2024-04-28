from .request_az import request_az_api


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

def list_sp_app_role_asignments(access_token, sp_id):
    return request_az_api(
        "https://graph.microsoft.com/v1.0/servicePrincipals/{}/appRoleAssignments".format(sp_id),
        access_token,
    )["value"]

