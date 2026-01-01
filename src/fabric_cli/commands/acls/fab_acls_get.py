# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_connection as api_connection
from fabric_cli.client import fab_api_gateway as api_gateway
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
from fabric_cli.utils import fab_jmespath as utils_jmespath
from fabric_cli.utils import fab_storage as utils_storage
from fabric_cli.utils import fab_ui
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace, context: FabricElement) -> None:
    if args.query:
        args.query = utils.process_nargs(args.query)

    if isinstance(context, Workspace):
        _get_acls_workspace(context, args)
    elif isinstance(context, Item):
        fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMINISTRATOR)
        _get_acls_item(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        _get_acls_virtual_ws_item(context, args)
    elif (
        # OneLake security only supporting Lakehouse items
        isinstance(context, OneLakeItem)
        and context.item.item_type == ItemType.LAKEHOUSE
    ):
        fab_logger.log_warning(fab_constant.WARNING_ONELAKE_RBAC_ENABLED)
        _get_acls_onelake(context, args)


# Workspaces
def _get_acls_workspace(workspace: Workspace, args: Namespace) -> None:
    args.ws_id = workspace.id
    response = api_workspaces.acl_list_from_workspace(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        _process_query_and_export(
            data_to_query=data["value"],
            output_file_name=workspace.name,
            args=args,
        )


# Virtual Workspace Items
def _get_acls_virtual_ws_item(item: VirtualWorkspaceItem, args: Namespace) -> None:
    match item.item_type:
        case VirtualWorkspaceItemType.GATEWAY:
            _get_acls_gateway(item, args)
        case VirtualWorkspaceItemType.CONNECTION:
            _get_acls_connection(item, args)
        case _:
            raise FabricCLIError(
                f"Access control operations are not supported for type '{str(item.item_type)}'",
                fab_constant.ERROR_NOT_SUPPORTED,
            )


def _get_acls_gateway(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    gw_id = gateway.id
    args.gw_id = gw_id

    response = api_gateway.acl_list_from_gateway(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        _process_query_and_export(
            data_to_query=data["value"],
            output_file_name=gateway.name,
            args=args,
        )


def _get_acls_connection(connection: VirtualWorkspaceItem, args: Namespace) -> None:
    con_id = connection.id
    args.con_id = con_id

    response = api_connection.acl_list_from_connection(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        _process_query_and_export(
            data_to_query=data["value"],
            output_file_name=connection.name,
            args=args,
        )


# Items
def _get_acls_item(item: Item, args: Namespace) -> None:
    workspace_id = item.workspace.id
    item_id = item.id

    args.ws_id = workspace_id
    args.id = item_id

    response = api_items.acl_list_from_item(args)

    if response.status_code == 200:
        data = json.loads(response.text)
        _process_query_and_export(
            data_to_query=data["accessDetails"],
            output_file_name=item.name,
            args=args,
        )


def _get_acls_onelake(context: OneLakeItem, args: Namespace) -> None:
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
            _process_query_and_export(
                data_to_query=data["value"],
                output_file_name=context.item.name,
                args=args,
            )
    except FabricAPIError as e:
        if e.status_code == "BadRequest":
            fab_ui.print_output_error(
                FabricCLIError(
                    ErrorMessages.Common.universal_security_disabled(item_name),
                    fab_constant.ERROR_UNIVERSAL_SECURITY_DISABLED,
                ),
                f"{args.command_path}",
                output_format_type=args.output_format,
            )
            fab_ui.print_grey(
                f"→ Run 'open /{workspace_name}/{item_name}' and enable it"
            )
        else:
            raise e


# Utils
def _process_query_and_export(
    data_to_query: Any, output_file_name: str, args: Namespace
) -> None:
    json_path_response = utils_jmespath.search(data_to_query, args.query)

    if args.output:
        utils_storage.do_output(
            data=json_path_response, file_name=output_file_name, args=args
        )
    elif json_path_response:
        fab_ui.print_output_format(args, data=json_path_response)
