# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.commands.fs.get import fab_fs_get_domain as get_domain
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_DOMAINS = ["contributorsScope", "description", "displayName"]


def exec(virtual_ws_item: VirtualWorkspaceItem, args: Namespace) -> None:
    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_DOMAINS)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        vwsi_domain_def = get_domain.exec(virtual_ws_item, args, verbose=False)

        updated_def = utils_set.update_fabric_element(
            vwsi_domain_def, query, args.input
        )

        args.name = virtual_ws_item.short_name
        args.id = virtual_ws_item.id

        utils_ui.print_grey(f"Setting new property for '{virtual_ws_item.name}'...")
        response = domain_api.update_domain(args, json.dumps(updated_def, indent=4))

        if response.status_code == 200:
            utils_set.update_cache(
                updated_def, virtual_ws_item, utils_mem_store.upsert_domain_to_cache
            )
            utils_ui.print_output_format(args, message="Domain updated")
