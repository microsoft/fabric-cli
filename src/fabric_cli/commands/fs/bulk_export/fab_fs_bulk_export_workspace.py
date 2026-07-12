# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from copy import deepcopy
import json

from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Workspace
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors.bulk_export import BulkExportErrors
from fabric_cli.core import fab_constant
from fabric_cli.client import fab_api_item as item_api
from fabric_cli.utils.fab_cmd_bulk_export_utils import ContextItemsSupportMap
from fabric_cli.utils import fab_cmd_bulk_export_utils as bulk_export_utils


def bulk_export_workspace(context: Workspace, args: Namespace) -> None:
    """Bulk-export a workspace with its contents, including sub-folders recursively."""
    args = deepcopy(args)

    args.ws_id = context.id
    args.from_path = context.path.strip("/")

    ws_items = utils_mem_store.get_workspace_items(context)
    if not ws_items:
        raise FabricCLIError(
            BulkExportErrors.empty_target(context.full_name),
            fab_constant.ERROR_INVALID_OPERATION,
        )

    # bulk export can be called with no items collected and create_bulk_export_payload will handle it as "export all", so we don't need to pre-collect items here like we do for folders. Just call bulk export directly with the workspace ID and let the API determine what to export based on the from_path.
    payload = bulk_export_utils.create_bulk_export_payload(items_ids=[])
    response = item_api.bulk_export_definitions(args, payload)
    exported_definitions = json.loads(response.text)

    items_support = _filter_response_by_supported_items(exported_definitions, context)
    if not items_support["supported_items"]:
        raise FabricCLIError(
            BulkExportErrors.no_exportable_items(),
            fab_constant.ERROR_INVALID_OPERATION,
        )

    bulk_export_utils.export_definition_parts_to_storage(
        args, context.full_name, exported_definitions
    )
    bulk_export_utils.print_bulk_export_summary(args, items_support)


def _filter_response_by_supported_items(
    exported_definitions: dict, workspace: Workspace
) -> ContextItemsSupportMap:
    """Filter response items by matching IDs from itemDefinitionsIndex against known workspace items.

    Uses itemDefinitionsIndex to identify returned items by ID, matches them against cached
    workspace items, and checks command support. Mutates exported_definitions['definitionParts'] in-place
    to remove parts belonging to unsupported or unknown item types.
    Returns a map of supported/unsupported Item objects.
    """
    items_definitions_index = exported_definitions.get("itemDefinitionsIndex", [])
    parts = exported_definitions.get("definitionParts", [])

    # Build a lookup of workspace items by ID
    ws_items = utils_mem_store.get_workspace_items(workspace)
    items_by_id: dict[str, Item] = {item.id: item for item in ws_items}

    supported_item_prefixes: set[str] = set()
    supported_items_list: list[Item] = []
    unsupported_items_list: list[Item] = []

    for index_entry in items_definitions_index:
        item_id = index_entry.get("id", "")
        root_path = index_entry.get("rootPath", "")

        ws_item = items_by_id.get(item_id)
        if ws_item is None:
            # Item not known in workspace - skip
            continue

        try:
            if bulk_export_utils.is_command_supported(ws_item):
                supported_item_prefixes.add(root_path)
                supported_items_list.append(ws_item)
            else:
                unsupported_items_list.append(ws_item)
        except FabricCLIError:
            unsupported_items_list.append(ws_item)

    # find unsupported items that were not in the response index and add them to the unsupported_items_list
    supported_item_ids: set[str] = {item.id for item in supported_items_list}
    unsupported_item_ids: set[str] = {item.id for item in unsupported_items_list}
    for ws_item in ws_items:
        if (
            ws_item.id not in supported_item_ids
            and ws_item.id not in unsupported_item_ids
        ):
            unsupported_items_list.append(ws_item)

    # Filter response parts to keep only supported items
    filtered_parts = [
        part
        for part in parts
        if _path_belongs_to_item(part.get("path", ""), supported_item_prefixes)
    ]
    exported_definitions["definitionParts"] = filtered_parts

    return {
        "supported_items": supported_items_list,
        "unsupported_items": unsupported_items_list,
    }


def _path_belongs_to_item(path: str, item_prefixes: set[str]) -> bool:
    """Check if a definition part path belongs to any of the given item prefixes.

    A part belongs to an item if its path starts with the item prefix followed by '/'.
    e.g., path '/Folder1/MyReport.Report/definition/pages/file.json'
    belongs to item prefix '/Folder1/MyReport.Report'.
    """
    for prefix in item_prefixes:
        if path.startswith(prefix + "/"):
            return True
    return False
