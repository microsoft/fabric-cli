# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core import fab_state_config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def exec(workspace: Workspace, args: Namespace) -> None:
    # Params
    optional_params = ["capacityName"]
    if mkdir_utils.show_params_desc(
        args.params, workspace.ws_type, optional_params=optional_params
    ):
        return

    if workspace.id is not None:
        raise FabricCLIError(
            ErrorMessages.Mkdir.workspace_name_exists(),
            fab_constant.ERROR_ALREADY_EXISTS,
        )

    default_capacity_id = fab_state_config.get_config(
        fab_constant.FAB_DEFAULT_CAPACITY_ID
    )

    params = args.params
    _capacity_name = params.get("capacityname", "")

    if _capacity_name:
        if _capacity_name != fab_constant.FAB_CAPACITY_NAME_NONE:
            # In case .Capacity is provided, remove it
            _capacity_name = utils.remove_dot_suffix(_capacity_name, ".Capacity")
            capacity = handle_context.get_command_context(
                f"/.capacities/{_capacity_name}.Capacity"
            )
            params["capacityId"] = capacity.id

        # Remove the capacityName from the params so it doesn't get sent to the API
        key_to_remove = next(
            (k for k in params.keys() if k.lower() == "capacityname"), None
        )
        if key_to_remove:
            params.pop(key_to_remove)
    else:
        params["capacityId"] = default_capacity_id

    if "capacityId" in params and not params.get("capacityId"):
        raise FabricCLIError(
            ErrorMessages.Mkdir.workspace_capacity_not_found(),
            fab_constant.ERROR_INVALID_INPUT,
        )

    utils_ui.print_grey("Creating a new Workspace...")

    # Remove all unwanted keys from the params
    utils.remove_keys_from_dict(args.params, ["displayName"])

    payload = {
        "description": "Created by fab",
        "displayName": workspace.short_name,
    }
    payload.update(args.params)
    json_payload = json.dumps(payload)

    response = workspace_api.create_workspace(args, json_payload)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        workspace._id = data["id"]
        # Add to mem_store
        utils_mem_store.upsert_workspace_to_cache(workspace)

        utils_ui.print_output_format(args, message=f"'{workspace.name}' created", data=data, show_headers=True)

