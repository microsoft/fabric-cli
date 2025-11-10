# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import OneLakeItem
from fabric_cli.utils import fab_ui
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace) -> None:
    schema = _extract_schema_from_commit_logs(args)
    if schema:
        fab_ui.print_grey("Schema extracted successfully")
        _schema = json.loads(schema)["fields"]
        fab_ui.print_output_format(args, data=_schema, text_style=TextFormatStyle.UNIX)

    else:
        raise FabricCLIError(
            "Failed to extract the table schema. Please ensure the path points to a valid Delta table",
            fab_constant.ERROR_INVALID_DETLA_TABLE,
        )


def _get_commit_logs(args: Namespace) -> Optional[list[str]]:
    _delta_log_path = args.path
    _delta_log_path[-1] = _delta_log_path[-1] + "/_delta_log"

    _context = handle_context.get_command_context(_delta_log_path, raise_error=True)
    assert isinstance(_context, OneLakeItem)
    onelake: OneLakeItem = _context
    workspace_id = onelake.workspace.id
    item_id = onelake.item.id
    local_path = onelake.local_path

    local_path = utils.remove_dot_suffix(local_path)
    args.directory = f"{workspace_id}/?recursive=false&resource=filesystem&directory={item_id}/{local_path}&getShortcutMetadata=true"
    response = onelake_api.list_tables_files_recursive(args)

    if response.status_code in {200, 201}:
        file_names = [f["name"] for f in response.json().get("paths", [])]
        json_files = [
            f"{workspace_id}/{item_id}/{f.split('/', 1)[1]}"
            for f in file_names
            if f.endswith(".json") and f != "_temporary"
        ]
        json_files.sort(reverse=True)
        return json_files
    return None


def _extract_schema_from_commit_logs(args: Namespace) -> Optional[str]:
    commit_logs = _get_commit_logs(args)

    if not commit_logs:
        return None

    for log in commit_logs:
        args.from_path = log
        args.wait = True
        response = onelake_api.read(args)

        if response.status_code in {200, 201}:
            json_string = response.text
            json_objects = json_string.strip().split("\n")

            for obj in json_objects:
                commit_data = json.loads(obj)
                if "metaData" in commit_data:
                    metadata = commit_data["metaData"]
                    schema = metadata["schemaString"]
                    return schema

    return None
