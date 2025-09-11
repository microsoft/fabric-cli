# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.start import fab_fs_start_capacity as start_capacity
from fabric_cli.commands.fs.start import fab_fs_start_item as start_item
from fabric_cli.core.fab_types import VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    VirtualWorkspaceItem,
)


def exec_command(args: Namespace, context: FabricElement) -> None:
    force_start = bool(args.force)
    if isinstance(context, VirtualWorkspaceItem):
        _start_virtual_ws_item(context, args, force_start)
    elif isinstance(context, Item):
        start_item.exec(context, args, force_start)


# Virtual Workspace Items
def _start_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_start: bool
) -> None:
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.CAPACITY:
        start_capacity.exec(virtual_ws_item, args, force_start)
