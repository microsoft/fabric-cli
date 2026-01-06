# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.commands.fs.get import fab_fs_get_workspace as get_workspace
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_WORKSPACE = [
    "description",
    "displayName",
    "sparkSettings",
]


def exec(workspace: Workspace, args: Namespace) -> None:
    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_WORKSPACE)

    # Get workspace
    args.deep_traversal = True
    args.output = None
    workspace_def = get_workspace.exec(workspace, args, verbose=False)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        updated_def = utils_set.update_fabric_element(workspace_def, query, args.input)

        args.ws_id = workspace.id

        utils_ui.print_grey(f"Setting new property for '{workspace.name}'...")

        # Update workspace settings
        if query.startswith("sparkSettings"):
            spark_settings_def = updated_def["sparkSettings"]
            updated_spark_settings_def = json.dumps(spark_settings_def)
            response = workspace_api.update_workspace_spark_settings(
                args, updated_spark_settings_def
            )
        # Update workspace
        else:
            response = workspace_api.update_workspace(args, json.dumps(updated_def))

        if response.status_code == 200:
            utils_set.update_cache(
                updated_def, workspace, utils_mem_store.upsert_workspace_to_cache
            )
            utils_ui.print_output_format(args, message="Workspace updated")
