# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.core import fab_constant, fab_logger
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
    fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMINISTRATOR)
    if isinstance(ws, Workspace):
        payload = json.dumps(
            {
                "workspacesIds": [f"{ws.id}"],
            }
        )

        args.id = virtual_ws_item.id
        args.name = virtual_ws_item.name
        domain_api.assign_to_workspaces(args, payload, force_assign)
    else:
        raise FabricCLIError(
            "Domain can only be assigned to a workspace",
            fab_constant.ERROR_NOT_SUPPORTED,
        )
