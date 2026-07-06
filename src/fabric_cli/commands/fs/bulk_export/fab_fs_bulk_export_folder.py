# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from copy import deepcopy

from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core import fab_constant
from fabric_cli.client import fab_api_item as item_api
from fabric_cli.errors.bulk_export import BulkExportErrors
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_fs_utils as utils_fs
from fabric_cli.utils.fab_cmd_bulk_export_utils import ContextItemsSupportMap
from fabric_cli.utils import fab_cmd_bulk_export_utils as bulk_export_utils


def bulk_export_folder(context: Folder, args: Namespace) -> None:
    """Bulk-export a folder with its contents, including sub-folders recursively."""
    args = deepcopy(args)

    workspace_id = context.workspace.id
    args.ws_id = workspace_id
    args.from_path = context.path.strip("/")

    items_support = _collect_context_items(context)
    if not items_support["supported_items"]:
        error_message = (
            BulkExportErrors.empty_target(context.full_name)
            if not items_support["unsupported_items"]
            else BulkExportErrors.no_exportable_items()
        )
        raise FabricCLIError(
            error_message,
            fab_constant.ERROR_INVALID_OPERATION,
        )

    exported_item_ids = [item.id for item in items_support["supported_items"]]
    payload = bulk_export_utils.create_bulk_export_payload(exported_item_ids)
    response = item_api.bulk_export_definitions(args, payload)
    bulk_export_utils.export_definition_parts_to_storage(
        args, context.full_name, response
    )
    bulk_export_utils.print_bulk_export_summary(args, items_support)


def _collect_context_items(
    context: Folder,
) -> ContextItemsSupportMap:
    """Recursively collect all item IDs under a folder and its sub-folders."""
    supported_items: list[Item] = []
    unsupported_items: list[Item] = []
    elements = utils_fs.get_ws_elements(context)

    for element in elements:
        if isinstance(element, Item):
            try:
                if bulk_export_utils.is_command_supported(element):
                    supported_items.append(element)
            except FabricCLIError:
                unsupported_items.append(element)
                pass
        elif isinstance(element, Folder):
            folder_items = _collect_context_items(element)
            supported_items.extend(folder_items["supported_items"])
            unsupported_items.extend(folder_items["unsupported_items"])

    return {"supported_items": supported_items, "unsupported_items": unsupported_items}
