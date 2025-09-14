# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def create_connection(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/create-connection?tabs=HTTP"""
    args.uri = "connections"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def get_connection(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/get-connection?tabs=HTTP"""
    args.uri = f"connections/{args.id}"
    args.method = "get"

    return fabric_api.do_request(args)


def update_connection(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/update-connection?tabs=HTTP"""
    args.uri = f"connections/{args.id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


def delete_connection(
    args: Namespace, bypass_confirmation: Optional[bool] = False
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/delete-connection?tabs=HTTP"""
    args.uri = f"connections/{args.id}"
    args.method = "delete"

    return api_utils.delete_resource(args, bypass_confirmation)


def list_connections(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/list-connections?tabs=HTTP"""
    args.uri = "connections"
    args.method = "get"

    return fabric_api.do_request(args)


# Connection types


def list_supported_connection_types(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/list-supported-connection-types?tabs=HTTP"""
    args.uri = "connections/supportedConnectionTypes"
    args.method = "get"

    return fabric_api.do_request(args)


# ACLS


def acl_list_from_connection(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/list-connection-role-assignments?tabs=HTTP"""
    args.uri = f"connections/{args.con_id}/roleAssignments"
    args.method = "get"

    return fabric_api.do_request(args)


def acl_delete_from_connection(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/delete-connection-role-assignment?tabs=HTTP"""
    args.uri = f"connections/{args.con_id}/roleAssignments/{args.id}"
    args.method = "delete"

    return fabric_api.do_request(args)


def acl_add_for_connection(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/add-connection-role-assignment?tabs=HTTP"""
    args.uri = f"connections/{args.con_id}/roleAssignments"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def acl_update_for_connection(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/update-connection-role-assignment?tabs=HTTP"""
    args.uri = f"connections/{args.con_id}/roleAssignments/{args.id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


def acl_get_for_connection(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/get-connection-role-assignment?tabs=HTTP"""
    args.uri = f"connections/{args.con_id}/roleAssignments/{args.id}"
    args.method = "get"

    return fabric_api.do_request(args)
