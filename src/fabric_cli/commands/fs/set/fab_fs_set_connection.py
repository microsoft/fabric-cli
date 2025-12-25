# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.commands.fs.get import fab_fs_get_connection as get_connection
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_CONNECTIONS = ["displayName", "privacyLevel", "credentialDetails"]


def exec(connection: VirtualWorkspaceItem, args: Namespace) -> None:
    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_CONNECTIONS)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        vwsi_connection_def = get_connection.exec(connection, args, verbose=False)
        connectivity_type = vwsi_connection_def.get("connectivityType", "")

        updated_def = utils_set.update_fabric_element(
            vwsi_connection_def, query, args.input
        )

        def _prep_for_updated_def(data):
            data.pop("id", None)  # Remove 'id' if it exists
            data.pop("gatewayId", None)  # Remove 'type' if it exists
            data.pop(
                "connectionDetails", None
            )  # Remove 'connectionDetails' if it exists
            data["connectivityType"] = connectivity_type # Add 'type' back
            return json.dumps(data, indent=4)

        connection_update_def = _prep_for_updated_def(updated_def)

        args.id = connection.id
        utils_ui.print_grey(f"Setting new property for '{connection.name}'...")
        response = connection_api.update_connection(args, connection_update_def)

        if response.status_code == 200:
            # Update mem_store
            connection._name = updated_def["displayName"]
            utils_mem_store.upsert_connection_to_cache(connection)

            utils_ui.print_output_format(args, message="Connection updated")
