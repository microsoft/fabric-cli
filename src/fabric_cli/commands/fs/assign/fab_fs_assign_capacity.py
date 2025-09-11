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
    force_assign: bool,
) -> None:
    if isinstance(ws, Workspace):
        payload = json.dumps(
            {
                "capacityId": f"{virtual_ws_item.id}",
            }
        )

        args.ws_id = ws.id
        args.name = virtual_ws_item.name
        workspace_api.assign_to_capacity(args, payload, force_assign)
    else:
        raise FabricCLIError(
            "Capacity can only be assigned to a workspace",
            fab_constant.ERROR_NOT_SUPPORTED,
        )
