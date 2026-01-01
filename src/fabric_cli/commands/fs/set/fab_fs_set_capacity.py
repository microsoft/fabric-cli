# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.commands.fs import fab_fs as fs
from fabric_cli.commands.fs.get import fab_fs_get_capacity as get_capacity
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_CAPACITIES = ["sku.name"]


def exec(virtual_ws_item: VirtualWorkspaceItem, args: Namespace) -> None:
    fs.check_fabric_capacity(virtual_ws_item)
    fs.fill_capacity_args(virtual_ws_item, args)

    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_CAPACITIES)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        vwsi_capacity_def = get_capacity.exec(virtual_ws_item, args, verbose=False)

        updated_def = utils_set.update_fabric_element(
            vwsi_capacity_def, query, args.input
        )

        utils_ui.print_grey(f"Setting new property for '{virtual_ws_item.name}'...")
        response = capacity_api.update_capacity(args, json.dumps(updated_def, indent=4))

        if response.status_code == 200:
            utils_ui.print_output_format(args, message="Capacity updated")
