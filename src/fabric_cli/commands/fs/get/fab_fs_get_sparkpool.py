# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_sparkpool as sparkpool_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_cmd_get_utils as utils_get


def exec(
    virtual_item: VirtualItem, args: Namespace, verbose: bool = True
) -> dict:
    args.ws_id = virtual_item.workspace.id
    args.id = virtual_item.id

    virtual_item_def = {}
    response = sparkpool_api.get_spark_pool(args)
    if response.status_code == 200:
        virtual_item_def = json.loads(response.text)
        utils_get.query_and_export(virtual_item_def, args, virtual_item.name, verbose)

    return virtual_item_def
