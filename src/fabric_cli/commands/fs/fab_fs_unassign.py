# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.unassign import (
    fab_fs_unassign_capacity as unassign_capacity,
)
from fabric_cli.commands.fs.unassign import fab_fs_unassign_domain as unassign_domain
from fabric_cli.core.fab_types import VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    VirtualWorkspaceItem,
)


def exec_command(
    args: Namespace, from_context: FabricElement, to_context: FabricElement
) -> None:
    force_unassign = bool(args.force)
    if isinstance(from_context, VirtualWorkspaceItem):
        _unassign_virtual_ws_item(from_context, to_context, args, force_unassign)


# Virtual Workspace Items
def _unassign_virtual_ws_item(
    virtual_ws_item: VirtualWorkspaceItem,
    ws: FabricElement,
    args: Namespace,
    force_unassign: bool,
) -> None:
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.CAPACITY:
        unassign_capacity.exec(virtual_ws_item, ws, args, force_unassign)
    if virtual_ws_item.item_type == VirtualWorkspaceItemType.DOMAIN:
        unassign_domain.exec(virtual_ws_item, ws, args, force_unassign)
