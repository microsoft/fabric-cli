# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_item_util as item_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_util as utils


def exec(virtual_item: VirtualItem, args: Namespace, force_delete: bool) -> None:
    args.ws_id = virtual_item.workspace.id
    args.id = virtual_item.id
    args.name = virtual_item.name

    item_name = item_utils.get_item_name_from_eds_name(virtual_item.name)
    args.item_id = utils_mem_store.get_item_id(virtual_item.workspace, item_name)

    if item_api.revoke_item_external_data_share(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_external_data_share_from_cache(virtual_item)
