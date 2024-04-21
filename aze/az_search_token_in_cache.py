import argparse
from .tokens import load_token_cache
import json

def parse_args():
    parser = argparse.ArgumentParser(
        description="Retrieve items from token cache based on the filters."
    )
    parser.add_argument(
        "-c", "--client-id",
        help="The id of the client application associated with the token",
    )

    parser.add_argument(
        "--realm",
        help="The realm of the token. Can be the id of the"\
        " tenant associated with the token, or the word 'organizations'",
    )

    parser.add_argument(
        "-s", "--scope",
        help="An API Permission (scope) associated with the token",
        action="append",
    )

    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument(
        "-a", "--access", "--access-token",
        help="Search for access tokens",
        action="store_true",
    )
    type_group.add_argument(
        "-r", "--refresh", "--refresh-token",
        help="Search for refresh tokens",
        action="store_true",
    )
    type_group.add_argument(
        "-A", "--account",
        help="Search for account items",
        action="store_true",
    )
    type_group.add_argument(
        "-i", "--id", "--id-token",
        help="Search for ID tokens",
        action="store_true",
    )
    type_group.add_argument(
        "-m", "--metadata", "--app-metadata",
        help="Search for App Metadata tokens",
        action="store_true",
    )

    return parser.parse_args()


# class CredentialType:
#         ACCESS_TOKEN = "AccessToken"
#         REFRESH_TOKEN = "RefreshToken"
#         ACCOUNT = "Account"  # Not exactly a credential type, but we put it here
#         ID_TOKEN = "IdToken"
#         APP_METADATA = "AppMetadata"

def main():
    args = parse_args()
    client_id = args.client_id
    environment = None # usually "login.microsoft.com"
    realm = args.realm
    home_id = None

    token_cache = load_token_cache()

    scopes = args.scope

    if args.refresh:
        token_type = token_cache.CredentialType.REFRESH_TOKEN
    elif args.account:
        token_type = token_cache.CredentialType.ACCOUNT
    elif args.id:
        token_type = token_cache.CredentialType.ID_TOKEN
    elif args.metadata:
        token_type = token_cache.CredentialType.APP_METADATA
    else:
        token_type = token_cache.CredentialType.ACCESS_TOKEN


    query = {}
    if client_id:
        query["client_id"] = client_id
    if environment:
        query["environment"] = environment
    if realm:
        query["realm"] = realm
    if home_id:
        query["home_account_id"] = home_id

    for entry in token_cache.find(
            token_type,
            query=query,
            target=scopes,
    ):
        print(json.dumps(entry))
