# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Fabric CLI Item Utilities

This module contains utility functions specifically related to Fabric items and operations
that require API dependencies. These functions are separated from general utilities to
avoid circular import issues with the API layer.

The module includes functions for:
- Item manipulation and retrieval
- OneLake path handling
- External data share management
- Item type and workspace element sorting
"""

import json
import platform
from argparse import Namespace
from collections.abc import Sequence
from typing import Optional, Union

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.commands.fs.export import fab_fs_export_item as export_item
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType, format_mapping
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Item, OneLakeItem
from fabric_cli.utils import fab_ui


def obtain_id_names_for_onelake(
    from_context: OneLakeItem, to_context: OneLakeItem
) -> tuple:
    from_path_id, from_path_name = extract_paths(from_context)
    to_path_id, to_path_name = extract_paths(to_context)
    return from_path_id, from_path_name, to_path_id, to_path_name


def extract_paths(context: FabricElement) -> tuple:
    path_id = context.path_id.lstrip("/")
    path_name = context.path.lstrip("/")
    return path_id, path_name


def _get_elem_type(elem: FabricElement) -> str:
    return str(elem.item_type.name) if isinstance(elem, Item) else str(elem.type)


def sort_ws_elems_by_config(
    ws_items: Sequence[Union[Item, Folder]],
) -> list[Union[Item, Folder]]:
    if (
        fab_state_config.get_config(fab_constant.FAB_OUTPUT_ITEM_SORT_CRITERIA)
        == "bytype"
    ):
        return sorted(
            ws_items,
            key=lambda elem: (_get_elem_type(elem), elem.short_name.lower()),
        )
    return sorted(
        ws_items, key=lambda elem: (elem.short_name.lower(), _get_elem_type(elem))
    )


def get_item_with_definition(
    item: Item,
    args: Namespace,
    decode: Optional[bool] = True,
    obtain_definition: bool = True,
) -> dict:

    args.force = True
    args.ws_id = item.workspace.id
    args.id = item.id
    args.item_uri = format_mapping.get(item.item_type, "items")

    if not obtain_definition:
        response = item_api.get_item(args, item_uri=True)
        item_def = json.loads(response.text)
    else:
        try:
            item.check_command_support(Command.FS_EXPORT)
            item_def = export_item.export_single_item(
                item, args, do_export=False, decode=decode, item_uri=True
            )
        except FabricCLIError as e:
            # Fallback
            if e.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND:
                # Obtain item
                response = item_api.get_item(args, item_uri=True)
                item_def = json.loads(response.text)
            else:
                raise e

    return item_def


def get_external_data_share_name(item_name: str, eds_id: str) -> str:
    return item_name + "_" + eds_id.split("-")[0]


def get_item_name_from_eds_name(eds_name) -> str:
    parts = eds_name.split("_")
    item_name = "_".join(parts[:-1])
    return item_name


def item_types_supporting_external_data_shares() -> list:
    return [ItemType.LAKEHOUSE, ItemType.KQL_DATABASE, ItemType.WAREHOUSE]


def item_sensitivity_label_warnings(args: Namespace, action: str) -> None:
    if args.force:
        fab_ui.print_warning(
            f"Item definition is {action} without its sensitivity label and its data"
        )


def get_confirm_copy_move_message(is_move_command: bool) -> str:
    action = "moved" if is_move_command else "copied"
    confirm_message = (
        f"Item definition is {action} without its sensitivity label. Are you sure?"
    )
    return confirm_message