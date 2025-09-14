# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_managedidentity as managed_identity_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(virtual_item: VirtualItem, args: Namespace, force_delete: bool) -> None:
    if virtual_item.short_name != virtual_item.workspace.short_name:
        raise FabricCLIError(
            f"A valid ManagedIdentity matching the Workspace name must be provided",
            fab_constant.ERROR_INVALID_INPUT,
        )

    args.ws_id = virtual_item.workspace.id
    args.id = virtual_item.id
    args.name = virtual_item.name

    if managed_identity_api.deprovision_managed_identity(args, force_delete):
        utils_mem_store.delete_managed_identity_from_cache(virtual_item)
