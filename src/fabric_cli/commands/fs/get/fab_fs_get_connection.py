# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_get_utils as utils_get


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, verbose: bool = True
) -> dict:
    args.id = virtual_ws_item.id

    virtual_ws_item_def = {}
    response = connection_api.get_connection(args)
    if response.status_code == 200:
        virtual_ws_item_def = json.loads(response.text)
        utils_get.query_and_export(
            virtual_ws_item_def, args, virtual_ws_item.name, verbose
        )

    return virtual_ws_item_def
