# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(item: Item, args: Namespace, force_delete: bool) -> None:
    args.ws_id = item.workspace.id
    args.id = item.id
    args.name = item.name
    args.item_type = item.type.value

    if item_api.delete_item(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_item_from_cache(item)
