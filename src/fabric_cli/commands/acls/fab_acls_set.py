# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Literal

from fabric_cli.client import fab_api_connection as api_connection
from fabric_cli.client import fab_api_gateway as api_gateway
from fabric_cli.client import fab_api_workspace as api_workspaces
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Workspace
from fabric_cli.core.hiearchy.fab_virtual_workspace_item import VirtualWorkspaceItem
from fabric_cli.utils import fab_ui as utils_ui

# Valid roles for different contexts
WORKSPACE_ROLES = ["Admin", "Member", "Contributor", "Viewer"]
CONNECTION_ROLES = ["Owner", "IserWithReshare", "User"]
GATEWAY_ROLES = ["Admin", "ConnectionCreator", "ConnectionCreatorWithResharing"]
PRINCIPAL_TYPES = [
    "User",
    "ServicePrincipal",
    "Group",
    "ServicePrincipalProfile",
]


def exec_command(args: Namespace, context: FabricElement) -> None:
    if isinstance(context, Workspace):
        _validate_role_by_type(args.role, "Workspace")
        _set_acls_workspace(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        if context.item_type == VirtualWorkspaceItemType.CONNECTION:
            _validate_role_by_type(args.role, "Connection")
            _set_acls_connection(context, args)
        elif context.item_type == VirtualWorkspaceItemType.GATEWAY:
            _validate_role_by_type(args.role, "Gateway")
            _set_acls_gateway(context, args)
        else:
            raise FabricCLIError(
                f"Unsupported item type '{context.item_type}' for ACL setting",
                fab_constant.ERROR_NOT_SUPPORTED,
            )


# Workspaces
def _set_acls_workspace(workspace: Workspace, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        args.ws_id = workspace.id
        identity = args.identity

        response = api_workspaces.acl_list_from_workspace(args)

        if _try_update_acl_if_exists(
            response=response,
            identity=identity,
            args=args,
            acl_update_callback=api_workspaces.acl_update_to_workspace,
        ):
            return

        _add_acl(
            name=workspace.name,
            identity=identity,
            args=args,
            acl_add_callback=api_workspaces.acl_add_to_workspace,
        )


def _set_acls_connection(connection: VirtualWorkspaceItem, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        identity = args.identity
        args.con_id = connection.id

        response = api_connection.acl_list_from_connection(args)

        if _try_update_acl_if_exists(
            response=response,
            identity=identity,
            args=args,
            acl_update_callback=api_connection.acl_update_for_connection,
        ):
            return

        _add_acl(
            name=connection.name,
            identity=identity,
            args=args,
            acl_add_callback=api_connection.acl_add_for_connection,
        )


def _set_acls_gateway(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        identity = args.identity
        args.gw_id = gateway.id

        response = api_gateway.acl_list_from_gateway(args)

        if _try_update_acl_if_exists(
            response=response,
            identity=identity,
            args=args,
            acl_update_callback=api_gateway.acl_update_for_gateway,
        ):
            return

        _add_acl(
            name=gateway.name,
            identity=identity,
            args=args,
            acl_add_callback=api_gateway.acl_add_for_gateway,
        )


# Helper functions


def _validate_role_by_type(
    role: str,
    type: Literal["Workspace", "Gateway", "Connection"],
) -> bool:
    """Validate if the role is valid for the given type."""
    if not role:
        raise FabricCLIError(
            "Role must be provided",
            fab_constant.ERROR_INVALID_INPUT,
        )
    if type == "Workspace":
        if role.lower() not in [r.lower() for r in WORKSPACE_ROLES]:
            raise FabricCLIError(
                f"Invalid role '{role}' for workspace. Valid roles are: {', '.join(WORKSPACE_ROLES)}",
                fab_constant.ERROR_INVALID_INPUT,
            )
    elif type == "Connection":
        if role.lower() not in [r.lower() for r in CONNECTION_ROLES]:
            raise FabricCLIError(
                f"Invalid role '{role}' for connection. Valid roles are: {', '.join(CONNECTION_ROLES)}",
                fab_constant.ERROR_INVALID_INPUT,
            )
    elif type == "Gateway":
        if role.lower() not in [r.lower() for r in GATEWAY_ROLES]:
            raise FabricCLIError(
                f"Invalid role '{role}' for gateway. Valid roles are: {', '.join(GATEWAY_ROLES)}",
                fab_constant.ERROR_INVALID_INPUT,
            )
    return True


def _add_acl(name: str, identity: str, args: Namespace, acl_add_callback) -> None:
    success = False
    utils_ui.print_grey(f"Adding ACL to '{name}'...")

    for principal_type in PRINCIPAL_TYPES:
        payload = json.dumps(
            {
                "principal": {"id": identity, "type": principal_type},
                "role": args.role,
            }
        )

        try:
            response = acl_add_callback(args, payload)
            if response.status_code in (200, 201):
                utils_ui.print_output_format(args, message="ACL set")
                success = True
                break
        except Exception:
            pass

    if not success:
        raise FabricCLIError(
            message=f"'{identity}' identity not found",
            status_code=fab_constant.ERROR_NOT_FOUND,
        )


def _try_update_acl_if_exists(
    response, identity: str, args: Namespace, acl_update_callback
) -> bool:
    """Check if the ACL exists for the given identity and update it if it does."""
    if response.status_code in (200, 201):
        list_acls = response.text
        if list_acls:
            if identity in list_acls:
                fab_logger.log_warning(
                    "The provided principal already has a role assigned in the connection"
                )
                if args.force or utils_ui.prompt_confirm("Overwrite?"):
                    args.id = identity
                    payload = json.dumps({"role": args.role})
                    response = acl_update_callback(args, payload)

                    if response.status_code in (200, 201):
                        utils_ui.print_output_format(args, message="ACL updated")

                return True

    return False
