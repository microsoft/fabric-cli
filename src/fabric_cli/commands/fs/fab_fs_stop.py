# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.stop import fab_fs_stop_capacity as stop_capacity
from fabric_cli.commands.fs.stop import fab_fs_stop_item as stop_item
from fabric_cli.core.fab_types import VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    VirtualWorkspaceItem,
)


def exec_command(args: Namespace, context: FabricElement) -> None:
    force_stop = bool(args.force)
    if isinstance(context, VirtualWorkspaceItem):
        _stop_virtual_ws_item(context, args, force_stop)
    elif isinstance(context, Item):
        stop_item.exec(context, args, force_stop)


# Virtual Workspace Items
def _stop_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_stop: bool
) -> None:
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.CAPACITY:
        stop_capacity.exec(virtual_ws_item, args, force_stop)
