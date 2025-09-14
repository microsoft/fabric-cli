# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    VirtualWorkspaceItem,
    Workspace,
)


def exec(
    virtual_ws_item: VirtualWorkspaceItem,
    ws: FabricElement,
    args: Namespace,
    force_unassign: bool,
) -> None:
    if isinstance(ws, Workspace):
        get_args = Namespace()
        get_args.ws_id = ws.id
        response = workspace_api.get_workspace(get_args)
        workspace = json.loads(response.text)
        capacity_id = workspace.get("capacityId", None)
        if capacity_id != virtual_ws_item.id:
            raise FabricCLIError(
                f"Cannot unassign capacity: Workspace not linked to it",
                fab_constant.ERROR_INVALID_INPUT,
            )

        args.ws_id = ws.id
        args.name = virtual_ws_item.name

        workspace_api.unassign_from_capacity(args, force_unassign)
    else:
        raise FabricCLIError(
            "Capacity can only be unassigned from a workspace",
            fab_constant.ERROR_NOT_SUPPORTED,
        )
