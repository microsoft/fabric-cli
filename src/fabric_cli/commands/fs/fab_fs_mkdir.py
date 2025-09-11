# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_capacity as mkdir_capacity
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_connection as mkdir_connection
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_domain as mkdir_domain
from fabric_cli.commands.fs.mkdir import (
    fab_fs_mkdir_externaldatashare as mkdir_externaldatashare,
)
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_folder as mkdir_folder
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_gateway as mkdir_gateway
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_item as mkdir_item
from fabric_cli.commands.fs.mkdir import (
    fab_fs_mkdir_managedidentity as mkdir_managedidentity,
)
from fabric_cli.commands.fs.mkdir import (
    fab_fs_mkdir_managedprivateendpoint as mkdir_managedprivateendpoint,
)
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_onelake as mkdir_onelake
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_sparkpool as mkdir_sparkpool
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_workspace as mkdir_workspace
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import VirtualItemType, VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    VirtualItem,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace, context: FabricElement) -> None:
    if (
        isinstance(context, VirtualItem)
        and context.item_type == VirtualItemType.SPARK_POOL
    ):
        args.params = utils.get_dict_from_params(args.params, max_depth=1)
    elif (
        isinstance(context, VirtualWorkspaceItem)
        and context.item_type == VirtualWorkspaceItemType.CONNECTION
    ):
        args.params = utils.get_dict_from_params(args.params, max_depth=3)
    else:
        args.params = utils.get_dict_from_params(args.params)

    # Lowercase params
    args.params = mkdir_utils.lowercase_keys(args.params)

    if isinstance(context, Workspace):
        mkdir_workspace.exec(context, args)
    elif isinstance(context, Item):
        mkdir_item.exec(context, args)
    elif isinstance(context, VirtualItem):
        _mkdir_virtual_item(context, args)
    elif isinstance(context, VirtualWorkspaceItem):
        _mkdir_virtual_ws_item(context, args)
    elif isinstance(context, OneLakeItem):
        mkdir_onelake.create_directory(context, args)
    elif isinstance(context, Folder):
        mkdir_folder.exec(context, args)


# Virtual Workspace Items
def _mkdir_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace
) -> None:
    if virtual_ws_item.id is not None:
        raise FabricCLIError(
            "An element with the same name exists", fab_constant.ERROR_ALREADY_EXISTS
        )

    match virtual_ws_item.item_type:
        case VirtualWorkspaceItemType.CAPACITY:
            mkdir_capacity.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.DOMAIN:
            mkdir_domain.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.CONNECTION:
            mkdir_connection.exec(virtual_ws_item, args)
        case VirtualWorkspaceItemType.GATEWAY:
            mkdir_gateway.exec(virtual_ws_item, args)
        case _ as x:
            raise FabricCLIError(
                f"{str(x)} not supported", fab_constant.ERROR_NOT_SUPPORTED
            )


# Virtual Items
def _mkdir_virtual_item(virtual_item: VirtualItem, args: Namespace) -> None:
    if virtual_item.id is not None:
        raise FabricCLIError(
            "An element with the same name exists", fab_constant.ERROR_ALREADY_EXISTS
        )

    match virtual_item.item_type:
        case VirtualItemType.SPARK_POOL:
            mkdir_sparkpool.exec(virtual_item, args)
        case VirtualItemType.MANAGED_IDENTITY:
            mkdir_managedidentity.exec(virtual_item, args)
        case VirtualItemType.MANAGED_PRIVATE_ENDPOINT:
            mkdir_managedprivateendpoint.exec(virtual_item, args)
        case VirtualItemType.EXTERNAL_DATA_SHARE:
            mkdir_externaldatashare.exec(virtual_item, args)
        case _ as x:
            raise FabricCLIError(
                f"{str(x)} not supported", fab_constant.ERROR_NOT_SUPPORTED
            )
