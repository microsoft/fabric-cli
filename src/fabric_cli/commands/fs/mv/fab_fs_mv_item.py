# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.commands.fs.cp import fab_fs_cp_item as cp_item
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Workspace
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def move_items(
    to_context: Workspace | Folder,
    filtered_items: list[Item],
    args: Namespace,
) -> int:

    successful_moves = 0
    from_workspace_path = args.from_path
    to_workspace_path = args.to_path

    for item in filtered_items:
        name = item.name.split(".")[0]
        new_item_path = Item(name, None, to_context, str(item.item_type)).path
        new_item = handle_context.get_command_context(new_item_path, False)
        assert isinstance(new_item, Item)
        args.force = True
        args.from_path = f"{from_workspace_path}/{item.name}"
        args.to_path = f"{to_workspace_path}/{item.name}"

        if move_item(item, new_item, args):
            successful_moves = successful_moves + 1

    return successful_moves


def move_item(
    from_context: Item,
    to_context: Item | Workspace | Folder,
    args: Namespace,
) -> bool:

    to_workspace = (
        to_context.workspace if isinstance(to_context, Folder) else to_context
    )

    # Cross-workspace move, copy the item definitionn and delete the source item after.
    if from_context.workspace != to_workspace:
        # Raise a confirm prompt stating that the item will be copied without its data and the original item will be deleted
        if args.force or utils_ui.prompt_confirm(
            "Moving items across workspaces will not move the data and cause data loss. Do you want to continue?"
        ):
            return cp_item.copy_item(
                from_context, to_context, args, delete_after_copy=True
            )
        else:
            return False

    else:
        # Intra-wokspace move, currently only supports moving items within the same folder (rename)
        if isinstance(to_context, Item):
            if from_context.item_type != to_context.item_type:
                raise FabricCLIError(
                    fab_constant.WARNING_DIFFERENT_ITEM_TYPES,
                    fab_constant.ERROR_INVALID_INPUT,
                )

            if from_context.parent != to_context.parent:
                raise FabricCLIError(
                    fab_constant.WARNING_MOVING_ITEMS_INSIDE_WORKSPACE_NOT_SUPPORTED,
                    fab_constant.ERROR_NOT_SUPPORTED,
                )
            if from_context.name != to_context.name:
                _rename_item(from_context, to_context.name, args)
                return True
            return False
        else:
            # If the destination is a workspace or folder, we don't support parent move for the moment.
            assert isinstance(to_context, Workspace | Folder)
            if from_context.parent != to_context:
                raise FabricCLIError(
                    fab_constant.WARNING_MOVING_ITEMS_INSIDE_WORKSPACE_NOT_SUPPORTED,
                    fab_constant.ERROR_NOT_SUPPORTED,
                )
            return False


def _rename_item(item: Item, name: str, args: Namespace) -> None:
    """
    Renames an item in the workspace.
    """
    _args = Namespace()
    _args.ws_id = item.workspace.id
    _args.id = item.id
    payload = json.dumps({"name": name})
    response = item_api.update_item(_args, payload)
    if response.status_code == 200:
        utils_ui.print_output_format(args, message="Move completed")
        item._name = name
        utils_mem_store.upsert_item_to_cache(item)
