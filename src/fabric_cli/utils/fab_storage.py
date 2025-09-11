# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from argparse import Namespace
from datetime import datetime
from typing import Any, Optional

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item, OneLakeItem
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui


def write_to_storage(
    args: Namespace,
    export_path: dict,
    data: Any,
    export: Optional[bool] = False,
    content_type: Optional[str] = "application/json",
) -> None:
    if export_path["type"] == "lakehouse":
        _write_to_lakehouse(args, export_path["path"], data, export)
    elif export_path["type"] == "local":
        _write_to_local(args, export_path["path"], data, export)
    elif export_path["type"] == "sparkJobDefinition":
        _write_to_sjd(args, export_path["path"], data, export, content_type)


def _write_to_local(
    args: Namespace, file_path: str, data: Any, export: Optional[bool] = True
) -> None:
    file_path = os.path.normpath(file_path)
    file_dir = os.path.dirname(file_path)

    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=False)

    # Check if the data is binary
    is_binary = isinstance(data, (bytes, bytearray))

    try:
        if is_binary:
            # Write binary data
            with open(file_path, "wb") as f:
                f.write(data)
            if not export:
                fab_ui.print_output_format(args, message="Export completed")
        else:
            # Process as JSON or text
            processed_data, is_json = _validate_json(data)
            if is_json:
                if not export:
                    file_path += ".json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(processed_data, f, indent=4, ensure_ascii=False)
                if not export:
                    fab_ui.print_output_format(args, message="Export completed")
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(
                        processed_data
                        if isinstance(processed_data, str)
                        else str(processed_data)
                    )
                if not export:
                    fab_ui.print_output_format(args, message="Export completed")
    except Exception as e:
        raise IOError(f"Failed to write to local file: {e}")


def _write_to_lakehouse(
    args: Namespace, file_path: str, data: Any, export: Optional[bool] = True
) -> None:
    processed_data, is_json = _validate_json(data)
    if is_json:
        data = json.dumps(processed_data)
        if not export:
            file_path += ".json"

    file_path = file_path.replace(".Workspace", "", 1).replace(".workspace", "", 1)
    args = Namespace()
    args.to_path = file_path

    try:
        response = onelake_api.touch_file(args)
        if response.status_code == 201:
            if len(data) > 0:
                onelake_api.append_file(args, data, 0)
            onelake_api.flush_file(args, len(data))
            if not export:
                fab_ui.print_output_format(args, message="Export completed")
    except Exception as e:
        raise e


def _write_to_sjd(
    args: Namespace,
    file_path: str,
    data: Any,
    export: Optional[bool] = True,
    content_type: Optional[str] = "application/json",
) -> None:
    args = Namespace()
    args.to_path = file_path

    try:
        response = onelake_api.touch_file(args)
        if response.status_code == 201:
            onelake_api.append_file(args, data, 0, content_type)
            onelake_api.flush_file(args, len(data), content_type)
            if not export:
                fab_ui.print_output_format(args, message="Export completed")
    except Exception as e:
        raise FabricCLIError(
            ErrorMessages.Common.file_not_accessible(file_path),
            fab_constant.ERROR_INVALID_PATH,
        )


# Utils
def _validate_json(data: Any) -> tuple:
    try:
        if isinstance(data, str):
            return json.loads(data), True
        elif isinstance(data, (dict, list)):
            return data, True
        else:
            return data, False
    except json.JSONDecodeError:
        return data, False


def get_export_path(output_path: str) -> dict:
    onelake_export_path = None

    try:
        # Try to obtain a valid Fabric context
        onelake_export_path = handle_context.get_command_context(output_path)
    except Exception as e:
        # Try to obtain a local path
        if output_path:
            expanded_path = os.path.expanduser(output_path)
            if os.path.exists(expanded_path):
                return {"type": "local", "path": expanded_path}
            else:
                raise FabricCLIError(
                    ErrorMessages.Common.no_such_file_or_directory(), fab_constant.ERROR_INVALID_PATH
                )

    # Validate Fabric path if exists
    if onelake_export_path and isinstance(onelake_export_path, OneLakeItem):
        parent_item: Item = onelake_export_path.item
        item_type = parent_item.item_type

        if (
            item_type != ItemType.LAKEHOUSE
            or not onelake_export_path.local_path.startswith("Files")
        ):
            raise FabricCLIError(
                ErrorMessages.Common.only_supported_for_lakehouse_files(),
                fab_constant.ERROR_NOT_SUPPORTED,
            )
        return {
            "type": "lakehouse",
            "path": onelake_export_path.path.strip("/"),
        }
    else:
        raise FabricCLIError(
            ErrorMessages.Common.only_supported_for_lakehouse_files(),
            fab_constant.ERROR_NOT_SUPPORTED,
        )


def get_import_path(input_path: str) -> dict:
    onelake_import_path = None
    export_path = None

    try:
        # Try to obtain a valid Fabric context
        onelake_import_path = handle_context.get_command_context(input_path)
    except Exception as e:
        # Try to obtain a local path
        expanded_path = os.path.expanduser(input_path)
        if os.path.exists(expanded_path):
            return {"type": "local", "path": expanded_path}
        else:
            raise FabricCLIError(
                ErrorMessages.Common.no_such_file_or_directory(), fab_constant.ERROR_INVALID_PATH
            )

    # Validate Fabric path if exists
    if onelake_import_path and isinstance(onelake_import_path, OneLakeItem):
        parent_item: Item = onelake_import_path.item
        item_type = parent_item.item_type

        if (
            item_type != ItemType.LAKEHOUSE
            or not onelake_import_path.local_path.startswith("Files/")
        ):
            raise FabricCLIError(
                ErrorMessages.Common.only_supported_for_lakehouse_files(),
                fab_constant.ERROR_NOT_SUPPORTED,
            )
        export_path = {
            "type": "lakehouse",
            "path": onelake_import_path.path.strip("/"),
        }

    if export_path is None:
        raise FabricCLIError(
            ErrorMessages.Common.invalid_path(), fab_constant.ERROR_INVALID_PATH
        )

    return export_path


def do_output(data: Any, file_name: str, args: Namespace) -> None:
    export_path = get_export_path(args.output)

    export_path["path"] = _create_get_export_file_name(
        f"{export_path['path']}/{file_name}"
    )

    file_path = export_path["path"]
    _, is_json = _validate_json(data)
    if is_json:
        file_path = file_path + ".json"

    fab_ui.print_grey(f"Exporting result to '{file_path}'...", True)
    write_to_storage(args, export_path, data)


def _create_get_export_file_name(path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"get_{timestamp}"
    return os.path.join(path, file_name)
