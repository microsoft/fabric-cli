# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_mirroring as mirroring_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item


def exec(item: Item, args: Namespace, force_start: bool) -> None:
    args.ws_id = item.workspace.id
    args.id = item.id
    args.name = item.name

    # Only start if DB stopped
    # status: Initialized, Initializing, Running, Starting, Stopped, Stopping
    response = mirroring_api.get_mirroring_status(args)

    if response.status_code == 200:
        state = json.loads(response.text)["status"]
        if state not in ("Stopped", "Initialized"):
            raise FabricCLIError(
                f"'{args.name}' is not in a valid state to start. State: {state}",
                fab_constant.ERROR_ALREADY_RUNNING,
            )

    if item.item_type == ItemType.MIRRORED_DATABASE:
        mirroring_api.start_mirroring(args, force_start)
