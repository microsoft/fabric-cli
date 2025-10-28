# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.commands.fs.ls import fab_fs_ls_capacity as ls_capacity
from fabric_cli.commands.fs.ls import fab_fs_ls_connection as ls_connection
from fabric_cli.commands.fs.ls import fab_fs_ls_domain as ls_domain
from fabric_cli.commands.fs.ls import (
    fab_fs_ls_externaldatashare as ls_externaldatashare,
)
from fabric_cli.commands.fs.ls import fab_fs_ls_folder as ls_folder
from fabric_cli.commands.fs.ls import fab_fs_ls_gateway as ls_gateway
from fabric_cli.commands.fs.ls import fab_fs_ls_item as ls_item
from fabric_cli.commands.fs.ls import fab_fs_ls_managedidentity as ls_managedidentity
from fabric_cli.commands.fs.ls import (
    fab_fs_ls_managedprivateendpoint as ls_managedprivateendpoint,
)
from fabric_cli.commands.fs.ls import fab_fs_ls_onelake as ls_onelake
from fabric_cli.commands.fs.ls import fab_fs_ls_sparkpool as ls_sparkpool
from fabric_cli.commands.fs.ls import fab_fs_ls_workspace as ls_workspace
from fabric_cli.core.fab_types import VirtualItemContainerType, VirtualWorkspaceType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    Tenant,
    VirtualItemContainer,
    VirtualWorkspace,
    Workspace,
)
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args, context: FabricElement):
    args.long = bool(args.long) if args.long else (args.query is not None and bool(len(args.query) > 1))
    if isinstance(context, Tenant):
        ls_workspace.exec(context, args)
    elif isinstance(context, VirtualWorkspace):
        _ls_virtual_workspace(context, args)
    elif isinstance(context, Workspace):
        ls_item.exec(context, args)
    elif isinstance(context, Folder):
        ls_folder.exec(context, args)
    elif isinstance(context, Item):
        ls_onelake.list_item_folders(context, args)
    elif isinstance(context, OneLakeItem):
        ls_onelake.list_onelake(context, args)
    elif isinstance(context, VirtualItemContainer):
        _ls_virtual_item_container(context, args)


# Virtual Workspaces
def _ls_virtual_workspace(virtual_workspace: VirtualWorkspace, args):
    show_details = bool(args.long)
    match virtual_workspace.vws_type:
        case VirtualWorkspaceType.CAPACITY:
            ls_capacity.exec(virtual_workspace, args, show_details)
        case VirtualWorkspaceType.DOMAIN:
            ls_domain.exec(virtual_workspace, args, show_details)
        case VirtualWorkspaceType.CONNECTION:
            ls_connection.exec(virtual_workspace, args, show_details)
        case VirtualWorkspaceType.GATEWAY:
            ls_gateway.exec(virtual_workspace, args, show_details)
        case _:
            utils_ui.print_grey("Not Supported")


# Virtual Items
def _ls_virtual_item_container(virtual_item_container: VirtualItemContainer, args):
    show_details = bool(args.long)
    match virtual_item_container.vic_type:
        case VirtualItemContainerType.SPARK_POOL:
            ls_sparkpool.exec(virtual_item_container, args, show_details)
        case VirtualItemContainerType.MANAGED_IDENTITY:
            ls_managedidentity.exec(virtual_item_container, args, show_details)
        case VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT:
            ls_managedprivateendpoint.exec(virtual_item_container, args, show_details)
        case VirtualItemContainerType.EXTERNAL_DATA_SHARE:
            ls_externaldatashare.exec(virtual_item_container, args, show_details)
        case _:
            utils_ui.print_grey("Not Supported")
