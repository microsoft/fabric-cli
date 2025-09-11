# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_delete: bool
) -> None:
    args.id = virtual_ws_item.id
    args.name = virtual_ws_item.name
    if connection_api.delete_connection(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_connection_from_cache(virtual_ws_item)
