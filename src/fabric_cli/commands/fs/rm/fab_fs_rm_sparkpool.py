# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_sparkpool as sparkpool_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(virtual_item: VirtualItem, args: Namespace, force_delete: bool) -> None:
    args.ws_id = virtual_item.workspace.id
    args.id = virtual_item.id
    args.name = virtual_item.name

    if sparkpool_api.delete_spark_pool(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_spark_pool_from_cache(virtual_item)
