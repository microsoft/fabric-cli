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
    force_unassign: bool,
) -> None:
    fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMINISTRATOR)

    if isinstance(ws, Workspace):
        args.id = virtual_ws_item.id
        args.name = virtual_ws_item.name
        ws_id = ws.id

        # Validate that the workspace is assigned to the Domain
        response = domain_api.list_domain_workspaces(args)
        _assigned_workspaces: list = json.loads(response.text)["value"]
        if not ws_id in [ws["id"] for ws in _assigned_workspaces]:
            raise FabricCLIError(
                f"Cannot unassign domain: Workspace not linked to it",
                fab_constant.ERROR_INVALID_INPUT,
            )

        payload = json.dumps(
            {
                "workspacesIds": [f"{ws_id}"],
            }
        )

        domain_api.unassign_from_workspaces(args, payload, force_unassign)

    else:
        raise FabricCLIError(
            "Domain can only be unassigned from a workspace",
            fab_constant.ERROR_NOT_SUPPORTED,
        )
