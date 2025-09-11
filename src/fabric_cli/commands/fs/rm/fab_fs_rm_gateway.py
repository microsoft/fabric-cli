# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_gateway as gateway_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_delete: bool
) -> None:
    args.id = virtual_ws_item.id
    args.name = virtual_ws_item.name
    if gateway_api.delete_gateway(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_gateway_from_cache(virtual_ws_item)
