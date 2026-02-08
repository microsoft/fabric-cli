# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_connection as api_connections
from fabric_cli.client import fab_api_gateway as api_gateways
from fabric_cli.client import fab_api_item as api_items
from fabric_cli.client import fab_api_onelake as api_onelake
from fabric_cli.client import fab_api_workspace as api_workspaces
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_exceptions import FabricAPIError, FabricCLIError
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace, context: FabricElement) -> None:
    if isinstance(context, Workspace):
        _ls_acls_workspace(context, args)
    elif isinstance(context, Item):
        fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMINISTRATOR)
        _ls_acls_item(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        _ls_acls_vwitem(context, args)
    elif (
        # OneLake security only supporting Lakehouse items
        isinstance(context, OneLakeItem)
        and context.item.item_type == ItemType.LAKEHOUSE
    ):
        fab_logger.log_warning(fab_constant.WARNING_ONELAKE_RBAC_ENABLED)
        _ls_acls_onelake(context, args)


# Workspaces
def _ls_acls_workspace(workspace: Workspace, args: Namespace) -> None:
    show_all = bool(args.long)
    args.ws_id = workspace.id

    response = api_workspaces.acl_list_from_workspace(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        ws_acls = data["value"]

        if ws_acls:
            sorted_acls = []

            for acl in ws_acls:
                principal = acl.get("principal", {})
                user_details = principal.get("userDetails")
                service_principal_details = principal.get("servicePrincipalDetails")
                group_details = principal.get("groupDetails")

                identity = None
                if user_details:
                    identity = user_details.get("userPrincipalName")
                elif service_principal_details:
                    identity = service_principal_details.get("aadAppId")
                elif group_details:
                    identity = principal.get("displayName")

                sorted_acls.append(
                    {
                        "name": principal.get("displayName", "Unknown"),
                        "type": principal.get("type", "Unknown"),
                        "identity": identity,
                        "objectId": acl.get("id", "Unknown"),
                        "acl": acl.get("role", "Unknown"),
                    }
                )
            sorted_acls = sorted(sorted_acls, key=lambda acl: acl["acl"])
            columns = ["acl", "identity", "type"]

            if show_all:
                columns.extend(["objectId", "name"])

            utils_ls.format_and_print_output(
                data=sorted_acls,
                columns=columns,
                args=args,
                show_details=True,
            )


# Virtual Workspace Items
def _ls_acls_vwitem(item: VirtualWorkspaceItem, args: Namespace) -> None:
    match item.item_type:
        case VirtualWorkspaceItemType.GATEWAY:
            _ls_acls_gateway(item, args)
        case VirtualWorkspaceItemType.CONNECTION:
            _ls_acls_connection(item, args)
        case _:
            raise FabricCLIError(
                f"Listing access controls is not supported for type '{str(item.item_type)}'",
                fab_constant.ERROR_NOT_SUPPORTED,
            )


def _ls_acls_gateway(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    show_all = bool(args.long)
    args.gw_id = gateway.id
    response = api_gateways.acl_list_from_gateway(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        access_details = data["value"]

        if access_details:
            sorted_acls = []

            for acl in access_details:
                sorted_acls.append(
                    {
                        "id": acl["id"],
                        "role": acl["role"],
                        "principalId": acl["principal"]["id"],
                        "principalType": acl["principal"]["type"],
                    }
                )

            sorted_acls = sorted(sorted_acls, key=lambda acl: acl["role"])

            columns = ["role", "principalId", "principalType"]
            if show_all:
                columns.insert(0, "id")

            utils_ls.format_and_print_output(
                data=sorted_acls,
                columns=columns,
                args=args,
                show_details=True,
            )


def _ls_acls_connection(connection: VirtualWorkspaceItem, args: Namespace) -> None:
    show_all = bool(args.long)
    args.con_id = connection.id

    response = api_connections.acl_list_from_connection(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        access_details = data["value"]

        if access_details:
            sorted_acls = []

            for acl in access_details:
                sorted_acls.append(
                    {
                        "id": acl["id"],
                        "role": acl["role"],
                        "principalId": acl["principal"]["id"],
                        "principalType": acl["principal"]["type"],
                    }
                )

            sorted_acls = sorted(sorted_acls, key=lambda acl: acl["role"])

            columns = ["role", "principalId", "principalType"]
            if show_all:
                columns.insert(0, "id")

            utils_ls.format_and_print_output(
                data=sorted_acls,
                columns=columns,
                args=args,
                show_details=True,
            )


# Items
def _ls_acls_item(item: Item, args: Namespace) -> None:
    show_all = bool(args.long)
    args.ws_id = item.workspace.id
    args.id = item.id

    response = api_items.acl_list_from_item(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        access_details = data["accessDetails"]

        if access_details:
            sorted_acls = []

            for acl in access_details:
                principal = acl["principal"]
                itemAccessDetails = acl["itemAccessDetails"]

                identity = None
                if "userDetails" in principal:
                    identity = principal["userDetails"].get("userPrincipalName")
                elif "servicePrincipalDetails" in principal:
                    identity = principal["servicePrincipalDetails"].get("aadAppId")
                elif "groupDetails" in principal:
                    identity = principal["groupDetails"].get("groupType")

                sorted_acls.append(
                    {
                        "name": principal["displayName"],
                        "type": principal["type"],
                        "identity": identity,
                        "id": principal["id"],
                        "acl": itemAccessDetails["permissions"],
                    }
                )

            sorted_acls = sorted(sorted_acls, key=lambda acl: acl["acl"])

            columns = ["acl", "identity", "type"]
            if show_all:
                columns = ["id", "name"] + columns

            utils_ls.format_and_print_output(
                data=sorted_acls,
                columns=columns,
                args=args,
                show_details=True,
            )


def _ls_acls_onelake(context: OneLakeItem, args: Namespace) -> None:
    show_all = bool(args.long)
    workspace_name = context.workspace.name
    workspace_id = context.workspace.id
    item_id = context.item.id
    item_name = context.item.name

    args.ws_id = workspace_id
    args.id = item_id

    try:
        response = api_onelake.acl_list_data_access_roles(args)

        if response.status_code == 200:
            data = json.loads(response.text)
            access_details = data["value"]

            if access_details:
                sorted_acls = []

            for rbac in access_details:
                name = rbac["name"]
                decisionRules = rbac["decisionRules"]

                # Safely access "microsoftEntraMembers" and "fabricItemMembers"
                microsoft_en_a_members = [
                    {"identity": member["objectId"], "type": "microsoftEntraMember"}
                    for member in rbac["members"].get("microsoftEntraMembers", [])
                ]
                fabric_item_members = [
                    {"identity": member["sourcePath"], "type": "fabricItemMember"}
                    for member in rbac["members"].get("fabricItemMembers", [])
                ]

                # Append the members to sorted_acls
                for member in microsoft_en_a_members:
                    sorted_acls.append(
                        {
                            "identity": member["identity"],
                            "details": decisionRules,
                            "acl": name,
                            "type": member[
                                "type"
                            ],  # Add the type for microsoftEntraMember
                        }
                    )

                for member in fabric_item_members:
                    sorted_acls.append(
                        {
                            "identity": member["identity"],
                            "details": decisionRules,
                            "acl": name,
                            "type": member["type"],  # Add the type for fabricItemMember
                        }
                    )

            sorted_acls = sorted(sorted_acls, key=lambda acl: acl["acl"])
            columns = ["acl", "identity", "type"]
            if show_all:
                columns = ["id", "name"] + columns
            utils_ls.format_and_print_output(
                data=sorted_acls,
                columns=columns,
                args=args,
                show_details=True,
            )

    except FabricAPIError as e:
        if e.status_code == "BadRequest":
            fab_ui.print_output_error(
                FabricCLIError(
                    ErrorMessages.Common.universal_security_disabled(item_name),
                    fab_constant.ERROR_UNIVERSAL_SECURITY_DISABLED,
                ),
                command=f"{args.command_path}",
                output_format_type=args.output_format,
            )
            fab_ui.print_grey(
                f"→ Run 'open /{workspace_name}/{item_name}' and enable it"
            )
        else:
            raise
