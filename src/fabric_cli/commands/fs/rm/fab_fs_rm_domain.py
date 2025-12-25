# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, force_delete: bool
) -> None:
    fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMINISTRATOR)
    args.id = virtual_ws_item.id
    args.name = virtual_ws_item.name
    if domain_api.delete_domain(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_domain_from_cache(virtual_ws_item)
    return
