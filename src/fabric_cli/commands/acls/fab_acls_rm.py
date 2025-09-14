# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Callable

from fabric_cli.client import fab_api_connection as api_connection
from fabric_cli.client import fab_api_gateway as api_gateway
from fabric_cli.client import fab_api_workspace as api_workspaces
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Workspace
from fabric_cli.core.hiearchy.fab_virtual_workspace_item import VirtualWorkspaceItem
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace, context: FabricElement) -> None:
    if isinstance(context, Workspace):
        _rm_acls_workspace(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        if context.item_type == VirtualWorkspaceItemType.CONNECTION:
            fab_logger.log_warning(constant.WARNING_FABRIC_ADMIN_ROLE)
            _rm_acls_connection(context, args)
        elif context.item_type == VirtualWorkspaceItemType.GATEWAY:
            fab_logger.log_warning(constant.WARNING_FABRIC_ADMIN_ROLE)
            _rm_acls_gateway(context, args)
        else:
            raise FabricCLIError(
                f"{context.item_type} not supported for command 'acl rm'",
                constant.ERROR_UNSUPPORTED_COMMAND,
            )


# Workspaces
def _rm_acls_workspace(workspace: Workspace, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        identity = args.identity
        args.ws_id = workspace.id

        response = api_workspaces.acl_list_from_workspace(args)

        data = json.loads(response.text)
        _rm_acls_by_identity(
            args,
            data,
            workspace.name,
            identity,
            api_workspaces.acl_delete_from_workspace,
        )


# Connections
def _rm_acls_connection(connection: VirtualWorkspaceItem, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        identity = args.identity
        # args.ws_id = connection.workspace_id
        args.con_id = connection.id

        response = api_connection.acl_list_from_connection(args)

        data = json.loads(response.text)
        _rm_acls_by_identity(
            args,
            data,
            connection.name,
            identity,
            api_connection.acl_delete_from_connection,
        )


# Gateways
def _rm_acls_gateway(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        identity = args.identity
        args.gw_id = gateway.id

        response = api_gateway.acl_list_from_gateway(args)

        data = json.loads(response.text)

        _rm_acls_by_identity(
            args, data, gateway.name, identity, api_gateway.acl_delete_from_gateway
        )


# Utils
def _validate_identity(identity: str, data: dict) -> tuple[bool, str]:
    for item in data["value"]:
        upn = item["principal"].get("userDetails", {}).get("userPrincipalName")
        spn_client_id = (
            item.get("principal", {}).get("servicePrincipalDetails", {}).get("aadAppId")
        )
        group_name = item.get("principal", {}).get("displayName", "")
        object_id = item.get("principal", {}).get("id", "")

        if (
            upn == identity
            or spn_client_id == identity
            or object_id == identity
            or group_name == identity
        ):
            return True, item["id"]
    return False, ""


def _rm_acls_by_identity(
    args: Namespace, data: dict, name: str, identity: str, delete_callback: Callable
) -> None:
    """Remove ACLs by identity and callback function."""

    is_valid_identity, matching_identity_id = _validate_identity(identity, data)

    if is_valid_identity:
        utils_ui.print_grey(f"Deleting ACL from '{name}'...")
        args.id = matching_identity_id

        response = delete_callback(args)

        if response.status_code == 200:
            utils_ui.print_output_format(args, message="ACL removed")
    else:
        raise FabricCLIError(
            f"'{identity}' identity not found", constant.ERROR_NOT_FOUND
        )
