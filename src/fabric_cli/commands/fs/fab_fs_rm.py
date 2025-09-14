# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs import fab_fs_cd as fs_cd
from fabric_cli.commands.fs.rm import fab_fs_rm_capacity as rm_capacity
from fabric_cli.commands.fs.rm import fab_fs_rm_connection as rm_connection
from fabric_cli.commands.fs.rm import fab_fs_rm_domain as rm_domain
from fabric_cli.commands.fs.rm import fab_fs_rm_externaldatashare as rm_externaldatashare
from fabric_cli.commands.fs.rm import fab_fs_rm_folder as rm_folder
from fabric_cli.commands.fs.rm import fab_fs_rm_gateway as rm_gateway
from fabric_cli.commands.fs.rm import fab_fs_rm_item as rm_item
from fabric_cli.commands.fs.rm import fab_fs_rm_managedidentity as rm_managedidentity
from fabric_cli.commands.fs.rm import (
    fab_fs_rm_managedprivateendpoint as rm_managedprivateendpoint,
)
from fabric_cli.commands.fs.rm import fab_fs_rm_onelake as rm_onelake
from fabric_cli.commands.fs.rm import fab_fs_rm_sparkpool as rm_sparkpool
from fabric_cli.commands.fs.rm import fab_fs_rm_workspace as rm_workspace
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_types import VirtualItemType, VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    Tenant,
    VirtualItem,
    VirtualWorkspaceItem,
    Workspace,
)


def exec_command(args: Namespace, context: FabricElement) -> None:
    force_delete = bool(args.force)

    if isinstance(context, Tenant):
        rm_workspace.bulk(context, args, force_delete)
    if isinstance(context, Workspace):
        rm_workspace.single(context, args, force_delete)
    elif isinstance(context, Item):
        rm_item.exec(context, args, force_delete)
    elif isinstance(context, VirtualItem):
        _rm_virtual_item(context, args, force_delete)
    elif isinstance(context, VirtualWorkspaceItem):
        _rm_virtual_ws_item(context, args, force_delete)
    elif isinstance(context, OneLakeItem):
        rm_onelake.shortcut_file_or_folder(context, args, force_delete)
    elif isinstance(context, Folder):
        rm_folder.exec(context, args, force_delete)

    # If the current context is contained in the element to be deleted,
    # change the context to the parent of the element to be deleted
    if not isinstance(context, Tenant) and Context().context.is_ascendent(context):
        fs_cd.exec_command(args, context.parent)


# Virtual Items
def _rm_virtual_item(
    virtual_item: VirtualItem, args: Namespace, force_delete: bool
) -> None:
    if virtual_item.item_type == VirtualItemType.SPARK_POOL:
        rm_sparkpool.exec(virtual_item, args, force_delete)
        return
    if virtual_item.item_type == VirtualItemType.MANAGED_IDENTITY:
        rm_managedidentity.exec(virtual_item, args, force_delete)
        return
    if virtual_item.item_type == VirtualItemType.MANAGED_PRIVATE_ENDPOINT:
        rm_managedprivateendpoint.exec(virtual_item, args, force_delete)
        return
    if virtual_item.item_type == VirtualItemType.EXTERNAL_DATA_SHARE:
        rm_externaldatashare.exec(virtual_item, args, force_delete)
        return


# Virtual Workspace Items
def _rm_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_delete: bool
) -> None:
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.CAPACITY:
        rm_capacity.exec(virtual_ws_item, args, force_delete)
        return
    elif virtual_ws_item.item_type == VirtualWorkspaceItemType.CONNECTION:
        rm_connection.exec(virtual_ws_item, args, force_delete)
        return
    elif virtual_ws_item.item_type == VirtualWorkspaceItemType.GATEWAY:
        rm_gateway.exec(virtual_ws_item, args, force_delete)
        return
    elif virtual_ws_item.item_type == VirtualWorkspaceItemType.DOMAIN:
        rm_domain.exec(virtual_ws_item, args, force_delete)
        return
