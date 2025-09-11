# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.commands.fs import fab_fs as fs
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_start: bool
) -> None:
    fs.fill_capacity_args(virtual_ws_item, args)

    # Only start if the capacity is in an acceptable state
    response = capacity_api.get_capacity(args)
    if response.status_code == 200:
        state = json.loads(response.text)["properties"]["state"]
        if state not in ("Paused", "Suspended"):
            raise FabricCLIError(
                ErrorMessages.StartStop.invalid_state_start_capacity(args.name, state),
                fab_constant.ERROR_ALREADY_RUNNING,
            )

    if capacity_api.resume_capacity(args, force_start):
        utils_mem_store.delete_capacity_from_cache(virtual_ws_item)
