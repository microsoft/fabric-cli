# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs import fab_fs_cd as fs_cd
from fabric_cli.commands.fs.set import fab_fs_set_capacity as set_capacity
from fabric_cli.commands.fs.set import fab_fs_set_connection as set_connection
from fabric_cli.commands.fs.set import fab_fs_set_domain as set_domain
from fabric_cli.commands.fs.set import fab_fs_set_folder as set_folder
from fabric_cli.commands.fs.set import fab_fs_set_gateway as set_gateway
from fabric_cli.commands.fs.set import fab_fs_set_item as set_item
from fabric_cli.commands.fs.set import fab_fs_set_onelake as set_onelake
from fabric_cli.commands.fs.set import fab_fs_set_sparkpool as set_sparkpool
from fabric_cli.commands.fs.set import fab_fs_set_workspace as set_workspace
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_context import Context
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
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace, context: FabricElement) -> None:
    args.query = utils.process_nargs(args.query)
    args.input = utils.process_nargs(args.input)

    # Check if the context has changed
    # This can be either the current context or a parent context
    _changed_context = context.path in Context().context.path
    _old_path = context.path

    if isinstance(context, Workspace):
        set_workspace.exec(context, args)
    elif isinstance(context, Item):
        set_item.exec(context, args)
    elif isinstance(context, VirtualItem):
        _set_virtual_item(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        _set_virtual_ws_item(context, args)
    elif isinstance(context, OneLakeItem):
        if context.nested_type == OneLakeItemType.SHORTCUT:
            set_onelake.onelake_shortcut(context, args)
        else:
            raise FabricCLIError(
                "This operation is not supported for the current OneLake item type. Only shortcuts can be modified in OneLake",
                fab_constant.ERROR_NOT_SUPPORTED,
            )
    elif isinstance(context, Folder):
        set_folder.exec(context, args)

    # If the context has changed, execute the cd command
    if _changed_context and (context.path != _old_path):
        fs_cd.exec_command(args, context)


# Virtual Workspace Items
def _set_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace
) -> None:
    match virtual_ws_item.item_type:
        case VirtualWorkspaceItemType.CAPACITY:
            set_capacity.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.DOMAIN:
            set_domain.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.CONNECTION:
            set_connection.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.GATEWAY:
            set_gateway.exec(virtual_ws_item, args)
        case _ as x:
            raise FabricCLIError(
                f"{str(x)} not supported", fab_constant.ERROR_NOT_SUPPORTED
            )


# Virtual Items
def _set_virtual_item(virtual_item: VirtualItem, args: Namespace) -> None:
    match virtual_item.item_type:
        case VirtualItemType.SPARK_POOL:
            set_sparkpool.exec(virtual_item, args)
        case _ as x:
            raise FabricCLIError(
                f"{str(x)} not supported", fab_constant.ERROR_NOT_SUPPORTED
            )
