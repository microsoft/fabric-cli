# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.assign import fab_fs_assign_capacity as assign_capacity
from fabric_cli.commands.fs.assign import fab_fs_assign_domain as assign_domain
from fabric_cli.core.fab_types import VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, VirtualWorkspaceItem


def exec_command(
    args: Namespace, from_context: FabricElement, to_context: FabricElement
) -> None:
    force_assign = bool(args.force)
    if isinstance(from_context, VirtualWorkspaceItem):
        _assign_virtual_ws_item(from_context, to_context, args, force_assign)


# Virtual Workspace Items
def _assign_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem,
    ws: FabricElement,
    args: Namespace,
    force_assign: bool,
) -> None:
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.CAPACITY:
        assign_capacity.exec(virtual_ws_item, ws, args, force_assign)
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.DOMAIN:
        assign_domain.exec(virtual_ws_item, ws, args, force_assign)
