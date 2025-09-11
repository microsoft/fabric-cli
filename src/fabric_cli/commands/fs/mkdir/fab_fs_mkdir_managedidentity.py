# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_managedidentity as managed_identity_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(managed_identity: VirtualItem, args: Namespace) -> None:
    if mkdir_utils.show_params_desc(args.params, managed_identity.item_type):
        return

    utils_ui.print_warning(
        "Managed Identity will use the workspace name, provided name is ignored"
    )

    managed_identity._name = managed_identity.workspace.short_name
    args.ws_id = managed_identity.workspace.id

    utils_ui.print_grey(f"Creating a new Managed Identity...")
    response = managed_identity_api.provision_managed_identity(args)
    if response.status_code in (200, 201):
        utils_ui.print_output_format(args, message=f"'{managed_identity.name}' created")

        data = json.loads(response.text)
        managed_identity._id = data["servicePrincipalId"]

        # Add to mem_store
        utils_mem_store.upsert_managed_identity_to_cache(managed_identity)
