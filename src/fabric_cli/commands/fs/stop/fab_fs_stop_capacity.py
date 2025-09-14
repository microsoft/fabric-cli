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
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_stop: bool
) -> None:
    fs.fill_capacity_args(virtual_ws_item, args)

    # Only stop if the capacity is in an acceptable state
    response = capacity_api.get_capacity(args)
    if response.status_code == 200:
        state = json.loads(response.text)["properties"]["state"]
        if state not in ("Active"):
            raise FabricCLIError(
                ErrorMessages.StartStop.invalid_state_stop_capacity(args.name, state),
                fab_constant.ERROR_NOT_RUNNING,
            )

    if capacity_api.suspend_capacity(args, force_stop):
        utils_mem_store.delete_capacity_from_cache(virtual_ws_item)
