# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def create_gateway(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/create-gateway?tabs=HTTP"""
    args.uri = "gateways"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def get_gateway(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/get-gateway?tabs=HTTP"""
    args.uri = f"gateways/{args.id}"
    args.method = "get"

    return fabric_api.do_request(args)


def update_gateway(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/update-gateway?tabs=HTTP"""
    args.uri = f"gateways/{args.id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


def delete_gateway(
    args: Namespace, bypass_confirmation: Optional[bool] = False
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/delete-gateway?tabs=HTTP"""
    args.uri = f"gateways/{args.id}"
    args.method = "delete"

    return api_utils.delete_resource(args, bypass_confirmation)


def list_gateways(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/list-gateways?tabs=HTTP"""
    args.uri = "gateways"
    args.method = "get"

    return fabric_api.do_request(args)


# Members


# ACLs


def acl_list_from_gateway(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/list-gateway-role-assignments?tabs=HTTP"""
    args.uri = f"gateways/{args.gw_id}/roleAssignments"
    args.method = "get"

    return fabric_api.do_request(args)


def acl_delete_from_gateway(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/delete-gateway-role-assignment?tabs=HTTP"""
    args.uri = f"gateways/{args.gw_id}/roleAssignments/{args.id}"
    args.method = "delete"

    return fabric_api.do_request(args)


def acl_add_for_gateway(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/add-gateway-role-assignment?tabs=HTTP"""
    args.uri = f"gateways/{args.gw_id}/roleAssignments"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def acl_update_for_gateway(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/update-gateway-role-assignment?tabs=HTTP"""
    args.uri = f"gateways/{args.gw_id}/roleAssignments/{args.id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


def acl_get_for_gateway(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/get-gateway-role-assignment?tabs=HTTP"""
    args.uri = f"gateways/{args.gw_id}/roleAssignments/{args.id}"
    args.method = "get"

    return fabric_api.do_request(args)
