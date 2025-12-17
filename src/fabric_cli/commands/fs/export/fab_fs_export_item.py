# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from argparse import Namespace
from copy import deepcopy
from typing import Optional, Union

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType, definition_format_mapping
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Workspace
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_cmd_export_utils as utils_export
from fabric_cli.utils import fab_item_util, fab_mem_store, fab_storage, fab_ui


def export_bulk_items(workspace: Workspace, args: Namespace) -> None:
    ws_items = fab_mem_store.get_workspace_items(workspace)

    if not ws_items:
        raise FabricCLIError(
            f"Your workspace is empty",
            fab_constant.ERROR_INVALID_OPERATION,
        )

    supported_items: list[Union[Item, Folder]] = []
    for item in ws_items:
        try:
            if item.check_command_support(Command.FS_EXPORT):
                supported_items.append(item)
        except Exception:
            pass

    if not supported_items:
        raise FabricCLIError(
            "Export not possible. Existing items cannot be imported/exported",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    # Add path validation before item selection
    fab_storage.get_export_path(args.output)

    # Sort output by config
    sorted_supported_items = fab_item_util.sort_ws_elems_by_config(supported_items)

    if args.all:
        selected_items = [item.name for item in sorted_supported_items]
    else:
        selected_items = fab_ui.prompt_select_items(
            "Select items:",
            [item.name for item in sorted_supported_items],
        )

    if selected_items:
        fab_ui.print_grey("\n".join(selected_items))
        fab_ui.print_grey("------------------------------")
        filtered_items = [
            item
            for item in supported_items
            if isinstance(item, Item) and item.name in selected_items
        ]

        if args.force or fab_ui.prompt_confirm(
            "Item definition is exported without its sensitivity label. Are you sure?"
        ):
            successful_exports = 0

            for item in filtered_items:
                args.force = True  # Already confirmed for workspace
                if export_single_item(item, args):
                    successful_exports = successful_exports + 1

            fab_ui.print_output_format(
                args,
                message=f"{successful_exports} {'items' if successful_exports > 1 else 'item'} exported successfully",
            )
    else:
        fab_ui.print_output_format(args, message="No items selected")


# Items
def export_single_item(
    item: Item,
    args: Namespace,
    do_export: Optional[bool] = True,
    decode: Optional[bool] = True,
    item_uri: Optional[bool] = False,
) -> dict:
    item_def = {}
    args = deepcopy(args)

    if args.force or fab_ui.prompt_confirm(
        "Item definition is exported without its sensitivity label. Are you sure?"
    ):
        workspace_id = item.workspace.id
        item_id = item.id
        item_type = item.item_type

        args.from_path = item.path.strip("/")
        args.ws_id, args.id, args.item_type = workspace_id, item_id, str(item_type)

        valid_export_formats = definition_format_mapping.get(item_type, {"default": ""})
        export_format_param = (
            args.format if getattr(args, "format", None) is not None else "default"
        )            
        if export_format_param not in valid_export_formats:
            valid_export_formats.pop("default")
            raise FabricCLIError(
                ErrorMessages.Export.invalid_export_format(
                    list(valid_export_formats.keys())
                ),
                fab_constant.ERROR_INVALID_INPUT,
            )
        else:
            args.format = valid_export_formats[export_format_param]

        item_def = item_api.get_item_withdefinition(args, item_uri)

        if decode:
            item_def = utils_export.decode_payload(item_def)
            if item.item_type == ItemType.NOTEBOOK:
                tags_to_clean = ["outputs"]
                item_def = utils_export.clean_notebook_cells(item_def, tags_to_clean)

        if do_export:
            export_path = fab_storage.get_export_path(args.output)

            original_path = export_path["path"]
            export_path["path"] = f"{original_path}/{item.name}"
            _to_path = export_path["path"]

            if export_path["type"] == "local":
                os.makedirs(_to_path, exist_ok=True)
            fab_ui.print_grey(f"Exporting '{args.from_path}' → '{_to_path}'...")
            utils_export.export_json_parts(args, item_def["definition"], export_path)

    return item_def
