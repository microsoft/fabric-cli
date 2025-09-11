# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.client import fab_api_tables as tables_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import OneLakeItem
from fabric_cli.utils import fab_cmd_table_utils as utils_table
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace, context: OneLakeItem) -> None:
    file_context = handle_context.get_command_context(args.file, False)
    try:
        assert isinstance(file_context, OneLakeItem)
    except AssertionError:
        raise FabricCLIError(
            f"Invalid path. Please provide a valid file or directory",
            fab_constant.ERROR_INVALID_PATH,
        )

    # Check if the path is a file or a folder
    _args = Namespace()
    _args.from_path = file_context.path_id.strip("/")
    response = onelake_api.get_properties(_args)

    if response.headers["x-ms-resource-type"] == "directory":
        _path_type = "Folder"
    elif response.headers["x-ms-resource-type"] == "file":
        _path_type = "File"
    else:
        raise FabricCLIError(
            f"Invalid path. Please provide a valid file or directory",
            fab_constant.ERROR_INVALID_PATH,
        )

    # Build the payload
    _payload = {
        "pathType": _path_type,  # Values are: "File", "Folder"
        # Path inside the lakehouse
        "relativePath": file_context.local_path,
        "mode": args.mode.capitalize(),
    }

    # Set the formatOptions based on the format
    _payload.setdefault("formatOptions", {})
    _payload["formatOptions"]["format"] = "Csv"

    if args.format:
        format_options = utils_table.parse_table_format_argument(args.format)
        format_value = format_options.get("format", "").capitalize()

        if format_value not in {"Csv", "Parquet"}:
            raise FabricCLIError(
                f"Invalid format: '{format_value}'. Allowed formats are: 'Csv', 'Parquet'"
            )

        if format_value == "Parquet":
            _payload["formatOptions"]["format"] = format_value
        else:
            # If the format is 'Csv', process additional options
            if format_value:
                _payload["formatOptions"]["format"] = format_value

            if format_options.get("header") is not None:
                _payload["formatOptions"]["header"] = format_options.get("header")

            if format_options.get("delimiter") is not None:
                _payload["formatOptions"]["delimiter"] = format_options.get("delimiter")

    # Add the file extension if it is defined
    if args.extension:
        _payload["extension"] = args.extension
    if _payload["pathType"] == "Folder":
        _payload["recursive"] = True

    table_load_payload = json.dumps(_payload)
    response = tables_api.load_table(args, payload=table_load_payload)

    if response.status_code == 202:
        utils_ui.print_output_format(args, message="Load table operation started")
    elif response.status_code in [200, 201]:
        utils_ui.print_output_format(args, message=f"Table '{args.table_name}' loaded successfully")
