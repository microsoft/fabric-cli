# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.get import fab_fs_get_capacity as get_capacity
from fabric_cli.commands.fs.get import fab_fs_get_connection as get_connection
from fabric_cli.commands.fs.get import fab_fs_get_domain as get_domain
from fabric_cli.commands.fs.get import (
    fab_fs_get_externaldatashare as get_externaldatashare,
)
from fabric_cli.commands.fs.get import fab_fs_get_folder as get_folder
from fabric_cli.commands.fs.get import fab_fs_get_gateway as get_gateway
from fabric_cli.commands.fs.get import fab_fs_get_item as get_item
from fabric_cli.commands.fs.get import (
    fab_fs_get_managedprivateendpoint as get_managedprivateendpoint,
)
from fabric_cli.commands.fs.get import fab_fs_get_onelake as get_onelake
from fabric_cli.commands.fs.get import fab_fs_get_sparkpool as get_sparkpool
from fabric_cli.commands.fs.get import fab_fs_get_workspace as get_workspace
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    OneLakeItemType,
    VirtualItemType,
    VirtualWorkspaceItemType,
)
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    VirtualItem,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.utils import fab_cmd_get_utils as get_utils
from fabric_cli.utils import fab_item_util, fab_ui, fab_util


def exec_command(args: Namespace, context: FabricElement) -> None:
    args.output = fab_util.process_nargs(args.output)
    args.query = fab_util.process_nargs(args.query)

    if isinstance(context, Workspace):
        get_workspace.exec(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        _get_virtual_ws_item(context, args)
    elif isinstance(context, Item):
        if _validate_sensitivity_label_warning(args, context):
            get_item.exec(context, args)
    elif isinstance(context, VirtualItem):
        _get_virtual_item(context, args)
    elif isinstance(context, OneLakeItem):
        if context.nested_type == OneLakeItemType.SHORTCUT:
            get_onelake.onelake_shortcut(context, args)
        else:
            get_onelake.onelake_resource(context, args)
    elif isinstance(context, Folder):
        get_folder.exec(context, args)


# Virtual Workspace Items
def _get_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace
) -> None:
    match virtual_ws_item.item_type:
        case VirtualWorkspaceItemType.CAPACITY:
            get_capacity.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.DOMAIN:
            get_domain.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.CONNECTION:
            get_connection.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.GATEWAY:
            get_gateway.exec(virtual_ws_item, args)
        case _:
            raise FabricCLIError(
                f"The operation is not supported for type '{str(virtual_ws_item.item_type)}'",
                fab_constant.ERROR_NOT_SUPPORTED,
            )


# Virtual Items
def _get_virtual_item(virtual_item: VirtualItem, args: Namespace) -> None:
    match virtual_item.item_type:
        case VirtualItemType.SPARK_POOL:
            get_sparkpool.exec(virtual_item, args)
        case VirtualItemType.MANAGED_PRIVATE_ENDPOINT:
            get_managedprivateendpoint.exec(virtual_item, args)
        case VirtualItemType.EXTERNAL_DATA_SHARE:
            get_externaldatashare.exec(virtual_item, args)
        case _:
            raise FabricCLIError(
                f"The operation is not supported for type {str(virtual_item.item_type)}",
                fab_constant.ERROR_NOT_SUPPORTED,
            )


def _validate_sensitivity_label_warning(args: Namespace, item: Item) -> bool:
    # refactor to make the condition for get item with definition in one place
    if args.query and not get_utils.should_retrieve_definition(args.query):
        # Query is metadata-only, skip sensitivity warning
        return True

    try:
        item.check_command_support(Command.FS_EXPORT)
    except Exception:
        return True

    if args.force:
        fab_item_util.item_sensitivity_label_warnings(args, "retrieved")
        return True
    else:
        return fab_ui.prompt_confirm(
            "Item definition is retrieved without its sensitivity label. Are you sure?"
        )
