# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.commands.fs import fab_fs as fs
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_get_utils as utils_get


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, verbose: bool = True
) -> dict:
    fs.check_fabric_capacity(virtual_ws_item)
    fs.fill_capacity_args(virtual_ws_item, args)

    virtual_ws_item_def = {}
    response = capacity_api.get_capacity(args)
    if response.status_code == 200:
        virtual_ws_item_def = json.loads(response.text)
        virtual_ws_item_def["fabricId"] = virtual_ws_item.id
        utils_get.query_and_export(
            virtual_ws_item_def, args, virtual_ws_item.name, verbose
        )

    return virtual_ws_item_def
