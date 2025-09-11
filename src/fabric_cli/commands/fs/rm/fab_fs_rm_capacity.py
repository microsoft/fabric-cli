# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.commands.fs import fab_fs as fs
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_delete: bool
) -> None:
    fs.fill_capacity_args(virtual_ws_item, args)

    if capacity_api.delete_capacity(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_capacity_from_cache(virtual_ws_item)
