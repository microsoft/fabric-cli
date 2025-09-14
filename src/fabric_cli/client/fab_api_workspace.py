# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def create_workspace(args: Namespace, payload: Optional[str] = None) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace?tabs=HTTP"""
    args.uri = "workspaces"
    args.method = "post"

    if payload is not None:
        response = fabric_api.do_request(args, data=payload)
    else:
        response = fabric_api.do_request(args)

    return response


def list_workspaces(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/list-workspaces?tabs=HTTP"""
    args.uri = "workspaces"
    args.method = "get"

    return fabric_api.do_request(args)


def ls_workspace_items(args: Namespace, workspace_id: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/items/list-items?tabs=HTTP"""
    args.uri = f"workspaces/{workspace_id}/items"
    args.method = "get"

    return fabric_api.do_request(args)


def ls_workspace_folders(args: Namespace, workspace_id: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/list-folders?tabs=HTTP"""
    args.uri = f"workspaces/{workspace_id}/folders?recursive=False"
    args.method = "get"

    return fabric_api.do_request(args)


def delete_workspace(
    args: Namespace, bypass_confirmation: Optional[bool] = False
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/delete-workspace?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}"
    args.method = "delete"

    return api_utils.delete_resource(args, bypass_confirmation)


def get_workspace(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/get-workspace?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}"
    args.method = "get"

    return fabric_api.do_request(args)


def update_workspace(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/update-workspace?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


# ACLs
def acl_list_from_workspace(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/list-workspace-role-assignments?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/roleAssignments"
    args.method = "get"

    return fabric_api.do_request(args)


def acl_delete_from_workspace(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/delete-workspace-role-assignment?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/roleAssignments/{args.id}"
    args.method = "delete"

    return fabric_api.do_request(args)


def acl_get_from_workspace(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/delete-workspace-role-assignment?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/roleAssignments/{args.id}"
    args.method = "delete"

    return fabric_api.do_request(args)


def acl_add_to_workspace(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/add-workspace-role-assignment?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/roleAssignments"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def acl_update_to_workspace(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/update-workspace-role-assignment?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/roleAssignments/{args.id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


# Spark settings


def get_workspace_spark_settings(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/workspace-settings/get-spark-settings?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/spark/settings"
    args.method = "get"

    return fabric_api.do_request(args)


def update_workspace_spark_settings(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/workspace-settings/update-spark-settings?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/spark/settings"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


# Managed Private Endpoints


def ls_workspace_managed_private_endpoints(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/managed-private-endpoints/list-workspace-managed-private-endpoints?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/managedPrivateEndpoints"
    args.method = "get"

    return fabric_api.do_request(args)


# Spark Pools


def ls_workspace_spark_pools(args: Namespace, workspace_id: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/custom-pools/list-workspace-custom-pools?tabs=HTTP"""
    args.uri = f"workspaces/{workspace_id}/spark/pools"
    args.method = "get"

    return fabric_api.do_request(args)


# Capacities


def assign_to_capacity(
    args: Namespace,
    payload: str,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/assign-to-capacity?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/assignToCapacity"
    args.method = "post"

    return api_utils.assign_resource(args, payload, bypass_confirmation, verbose)


def unassign_from_capacity(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/unassign-from-capacity?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/unassignFromCapacity"
    args.method = "post"

    return api_utils.unassign_resource(args, bypass_confirmation, verbose=verbose)
