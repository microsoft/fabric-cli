# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_cmd_get_utils as utils_get
from fabric_cli.utils import fab_item_util as item_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_util as utils


def exec(
    virtual_item: VirtualItem, args: Namespace, verbose: bool = True
) -> dict:
    item_name = item_utils.get_item_name_from_eds_name(virtual_item.name)
    args.item_id = utils_mem_store.get_item_id(virtual_item.workspace, item_name)

    args.ws_id = virtual_item.workspace.id
    args.id = virtual_item.id
    response = item_api.get_item_external_data_share(args)

    virtual_item_def = {}
    if response.status_code == 200:
        virtual_item_def = json.loads(response.text)
        utils_get.query_and_export(virtual_item_def, args, virtual_item.name, verbose)

    return virtual_item_def
