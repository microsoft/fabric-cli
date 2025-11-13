# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages


def create_item(
    args: Namespace, payload: Optional[str] = None, item_uri: Optional[bool] = False
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/create-item"""
    if item_uri:
        args.uri = f"workspaces/{args.ws_id}/{args.item_uri}"
    else:
        args.uri = f"workspaces/{args.ws_id}/items"

    args.method = "post"
    args.wait = True  # Wait for the item to be created in order to get the details

    if payload is not None:
        response = fabric_api.do_request(args, data=payload)
    else:
        response = fabric_api.do_request(args)

    return response


def delete_item(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    item_uri: Optional[bool] = False,
    verbose: bool = True,
    override_method: Optional[str] = None,
    operation: Optional[str] = None,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/delete-item"""
    if not hasattr(args, "uri") or not args.uri:
        if item_uri:
            args.uri = f"workspaces/{args.ws_id}/{args.item_uri}/{args.id}"
        else:
            args.uri = f"workspaces/{args.ws_id}/items/{args.id}"

    args.method = override_method if override_method else "delete"

    if operation is not None:
        return api_utils.delete_resource(args, bypass_confirmation, verbose, operation)
    return api_utils.delete_resource(args, bypass_confirmation, verbose)


def get_item_withdefinition(args: Namespace, item_uri: Optional[bool] = False) -> dict:
    response = get_item(args, item_uri)
    item = json.loads(response.text)

    try:
        def_response = get_item_definition(args)
        definition = json.loads(def_response.text)
        if isinstance(definition, dict):
            item.update(definition)
            return item
        else:
            raise FabricCLIError(
                ErrorMessages.Client.response_payload_not_dictionary(),
                fab_constant.ERROR_INVALID_DEFINITION_PAYLOAD,
            )
    except FabricCLIError as ex:
        # Case where user can view the item but not its definitions we will return the item without definitions
        if (
            ex.status_code == fab_constant.ERROR_UNAUTHORIZED
            or ex.status_code == fab_constant.ERROR_FORBIDDEN
        ):
            return item
        else:
            raise ex


def get_item(
    args: Namespace, item_uri: Optional[bool] = False, ext_uri: Optional[bool] = False
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/get-item"""
    if item_uri:
        args.uri = f"workspaces/{args.ws_id}/{args.item_uri}/{args.id}"
    else:
        args.uri = f"workspaces/{args.ws_id}/items/{args.id}"

    if ext_uri:
        args.uri = args.uri + args.ext_uri

    args.method = "get"

    return fabric_api.do_request(args)


def get_item_definition(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/get-item-definition"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.id}/getDefinition{args.format}"
    args.method = "post"
    args.wait = True

    return fabric_api.do_request(args)


def update_item_definition(
    args: Namespace, payload: str, item_uri: Optional[bool] = False
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/update-item-definition"""
    if item_uri:
        args.uri = f"workspaces/{args.ws_id}/{args.item_uri}/{args.id}/updateDefinition"
    else:
        args.uri = f"workspaces/{args.ws_id}/items/{args.id}/updateDefinition"

    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def update_item(
    args: Namespace,
    payload: str,
    item_uri: Optional[bool] = False,
    ext_uri: Optional[bool] = False,
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/update-item"""
    if item_uri:
        args.uri = f"workspaces/{args.ws_id}/{args.item_uri}/{args.id}"
    else:
        args.uri = f"workspaces/{args.ws_id}/items/{args.id}"

    if ext_uri:
        args.uri = args.uri + args.ext_uri

    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


# ACLs


def acl_list_from_item(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/items/list-item-access-details"""
    args.uri = f"admin/workspaces/{args.ws_id}/items/{args.id}/users"
    args.method = "get"
    return fabric_api.do_request(args)


# Connections


def get_item_connections(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/list-item-connections"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.id}/connections"
    args.method = "get"

    return fabric_api.do_request(args)


# External Data Shares


def create_item_external_data_share(
    args: Namespace, payload: Optional[str] = None
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/external-data-shares/create-external-data-share"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/externalDataShares"
    args.method = "post"
    args.wait = True  # Wait for the item to be created in order to get the details

    return fabric_api.do_request(args, data=payload)


def get_item_external_data_share(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/external-data-shares/get-external-data-share"""
    args.uri = (
        f"workspaces/{args.ws_id}/items/{args.item_id}/externalDataShares/{args.id}"
    )
    args.method = "get"

    return fabric_api.do_request(args)


def list_item_external_data_shares(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/external-data-shares/list-external-data-shares-in-item"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/externalDataShares"
    args.method = "get"

    return fabric_api.do_request(args)


def revoke_item_external_data_share(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/external-data-shares/revoke-external-data-share"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/externalDataShares/{args.id}/revoke"
    # Using Overrides since Revoke API is a POST api without object id in the URI.
    override_method = "post"

    return delete_item(
        args,
        bypass_confirmation=bypass_confirmation,
        verbose=verbose,
        override_method=override_method,
        operation="revoke",
    )


# Environments


def environment_upload_staging_library(args: Namespace, payload: dict) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/environment/spark-libraries/upload-staging-library"""
    args.uri = f"workspaces/{args.ws_id}/environments/{args.id}/staging/libraries"
    args.method = "post"

    return fabric_api.do_request(args, files=payload)


def environment_publish(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/environment/spark-libraries/publish-environment"""
    args.uri = f"workspaces/{args.ws_id}/environments/{args.id}/staging/publish"
    args.method = "post"

    return fabric_api.do_request(args)


def environment_delete_library_staging(
    args: Namespace, library_name: str
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/environment/spark-libraries/delete-staging-library"""
    args.uri = f"workspaces/{args.ws_id}/environments/{args.id}/staging/libraries?libraryToDelete={library_name}"
    args.method = "delete"

    return fabric_api.do_request(args)
