# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import json
from typing import TypedDict
from argparse import Namespace

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors.bulk_export import BulkExportErrors
from fabric_cli.core.fab_commands import Command
from fabric_cli.utils import fab_ui
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_storage
from fabric_cli.utils import fab_cmd_export_utils as utils_export


class ContextItemsSupportMap(TypedDict):
    supported_items: list[Item]
    unsupported_items: list[Item]


def is_command_supported(element: Item) -> bool:
    return element.check_command_support(Command.FS_BULKEXPORT)


def create_bulk_export_payload(items_ids: list[str]) -> str:
    if not items_ids:
        # If no specific item IDs are provided, we can choose to export all items or handle it as needed
        # For this example, we'll return an empty payload which the API can interpret as "export all"
        return json.dumps({"items": [], "mode": "All"})
    payload_items = []
    for item_id in items_ids:
        item_dict = {
            "id": item_id,
        }
        payload_items.append(item_dict)

    payload = {
        "items": payload_items,
        "mode": "Selective",
    }

    return json.dumps(payload)


def export_definition_parts_to_storage(
    args: Namespace,
    artifact_name: str,
    exported_definitions: dict,
) -> None:
    # Response contains definitionParts array; extract the single item
    item_definitions = exported_definitions.get("definitionParts", [])
    if not item_definitions:
        raise FabricCLIError(
            BulkExportErrors.no_definition_returned(artifact_name),
            fab_constant.ERROR_INVALID_DEFINITION_PAYLOAD,
        )

    item_def = utils_export.decode_payload(exported_definitions)
    _strip_parent_folders_from_definition_paths(item_def, args.from_path)

    export_path = fab_storage.get_export_path(args.output)

    _validate_definition_parts_paths_are_under_export_path(
        item_def, export_path["path"]
    )

    fab_ui.print_grey(f"Bulk-exporting '{args.from_path}' → '{export_path['path']}'...")
    utils_export.export_json_parts(
        args, item_def, export_path, definition_parts="definitionParts"
    )


def print_bulk_export_summary(
    args: Namespace, items_support: ContextItemsSupportMap
) -> None:
    output_format_message = (
        f"Exported {len(items_support['supported_items'])} items to '{args.output}'"
    )
    unsupported_count = len(items_support["unsupported_items"])
    if unsupported_count > 0:
        unsupported_types_count = _count_items_by_type(
            items_support["unsupported_items"]
        )
        unsupported_types = [
            f"{item_type} ({count})"
            for item_type, count in unsupported_types_count.items()
        ]
        output_format_message += (
            f". Skipped {unsupported_count} items due to unsupported item types: "
            f"{', '.join(unsupported_types)}"
        )
    fab_ui.print_output_format(
        args=args,
        data=[
            {
                "exported": len(items_support["supported_items"]),
                "exported_types": _count_items_by_type(
                    items_support["supported_items"]
                ),
                "skipped": len(items_support["unsupported_items"]),
                "skipped_types": _count_items_by_type(
                    items_support["unsupported_items"]
                ),
                "output": args.output,
            }
        ],
        message=output_format_message,
    )


def _count_items_by_type(items: list[Item]) -> dict[str, int]:
    """Count items grouped by item type."""
    counts: dict[str, int] = {}
    for item in items:
        item_type = str(item.item_type)
        counts[item_type] = counts.get(item_type, 0) + 1
    return counts


def _strip_parent_folders_from_definition_paths(item_def: dict, from_path: str) -> None:
    """Remove the parent prefix from each part's path so only the bulk-export target remains.

    For example, if from_path is "myws.Workspace/f1.Folder/f2.Folder/n1.Notebook", the
    workspace segment is skipped (not part of definitionParts paths) and the prefix
    "/f1/f2/" is stripped from each definition part path (folder names without .Folder suffix).
    """
    # Strip the workspace segment (first component) since definitionParts paths don't include it
    parts = from_path.split("/", 1)
    if len(parts) < 2:  # workspace export, whole path is relevant, no prefix to strip
        return
    path_without_ws = parts[1]

    parent_dir = path_without_ws.rsplit("/", 1)[0] if "/" in path_without_ws else ""
    if not parent_dir:  # First folder level, no parent directory to strip, return early
        return

    # Remove ".Folder" suffix from each segment since definitionParts paths use plain folder names
    segments = parent_dir.split("/")
    segments = [seg.removesuffix(".Folder") for seg in segments]
    prefix = "/" + "/".join(segments) + "/"

    for part in item_def.get("definitionParts", []):
        path = part.get("path", "")
        if path.startswith(prefix):
            part["path"] = "/" + path[len(prefix) :]
        else:
            raise FabricCLIError(
                BulkExportErrors.path_mismatch(),
                fab_constant.ERROR_INVALID_DEFINITION_PAYLOAD,
            )


def _validate_definition_parts_paths_are_under_export_path(
    item_def: dict, export_path: str
) -> None:
    """Validate that all definition part paths concatenated with the export path are under the export path to prevent path traversal issues."""
    for part in item_def.get("definitionParts", []):
        part_path = part.get("path", "").lstrip("/")
        full_export_path = os.path.abspath(os.path.join(export_path, part_path))
        if not full_export_path.startswith(os.path.abspath(export_path) + os.sep):
            raise FabricCLIError(
                BulkExportErrors.path_mismatch_full_export_path(),
                fab_constant.ERROR_INVALID_DEFINITION_PAYLOAD,
            )
