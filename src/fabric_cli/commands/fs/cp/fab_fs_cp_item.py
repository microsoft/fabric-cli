# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core import fab_logger
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Folder, Item, Workspace
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_item_util as item_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as util


def copy_items(
    filtered_items: list[Item],
    to_context: Workspace | Folder,
    args: Namespace,
    delete_after_copy: Optional[bool] = False,
) -> int:

    successful_copies = 0
    to_workspace = (
        to_context.workspace if isinstance(to_context, Folder) else to_context
    )

    for item in filtered_items:
        name = (
            f"{item.short_name}_copy"
            if item.workspace == to_workspace
            else item.short_name
        )
        new_item_path = Item(name, None, to_context, str(item.item_type)).path
        new_item = handle_context.get_command_context(new_item_path, False)
        assert isinstance(new_item, Item)
        args.from_path = item.path
        args.to_path = f"{to_context.path}/{item.name}"

        if cp_single_item(item, new_item, args, delete_after_copy=False):
            successful_copies = successful_copies + 1

    # Delete items if delete_after_copy is True
    if delete_after_copy:
        for item in filtered_items:
            try:
                _args = Namespace()
                _args.ws_id = item.workspace.id
                _args.id = item.id
                _args.name = item.name
                _args.uri = None  # empty URI to delete item since it can be completed by a LRO response
                item_api.delete_item(_args, bypass_confirmation=True, verbose=False)
            finally:
                # Remove from mem_store
                utils_mem_store.delete_item_from_cache(item)

    return successful_copies


def copy_item(
    from_context: Item,
    to_context: Item | Workspace | Folder,
    args: Namespace,
    delete_after_copy: Optional[bool] = False,
) -> bool:

    if isinstance(to_context, Item):
        return cp_single_item(
            from_context, to_context, args, delete_after_copy=delete_after_copy
        )
    else:
        assert isinstance(to_context, Workspace | Folder)
        to_workspace = (
            to_context.workspace if isinstance(to_context, Folder) else to_context
        )
        name = (
            f"{from_context.short_name}_copy"
            if from_context.workspace == to_workspace and not delete_after_copy
            else from_context.short_name
        )
        new_item_path = Item(name, None, to_context, str(from_context.item_type)).path
        new_item = handle_context.get_command_context(new_item_path, False)
        assert isinstance(new_item, Item)
        return cp_single_item(
            from_context, new_item, args, delete_after_copy=delete_after_copy
        )


def cp_single_item(
    from_context: Item,
    to_context: Item,
    args: Namespace,
    delete_after_copy: Optional[bool] = False,
) -> bool:
    if from_context.item_type != to_context.item_type:
        raise FabricCLIError(
            fab_constant.WARNING_DIFFERENT_ITEM_TYPES, fab_constant.ERROR_INVALID_INPUT
        )
    # Check supported for mv or if it's a Lakehouse.
    # A Lakehouse is whitelisted to support underlying OneLake move and copy operations
    if (
        not from_context.check_command_support(Command.FS_CP)
        or from_context.item_type == ItemType.LAKEHOUSE
    ):
        raise FabricCLIError(
            fab_constant.WARNING_NOT_SUPPORTED_ITEM, fab_constant.ERROR_NOT_SUPPORTED
        )

    args.ws_id_from, args.ws_id_to = (
        from_context.workspace.id,
        to_context.workspace.id,
    )

    ws_items_target: list[Item] = utils_mem_store.get_workspace_items(
        to_context.workspace
    )

    try:
        is_move_command = delete_after_copy if delete_after_copy is not None else False

        if (
            is_move_command
            and from_context.workspace == to_context.workspace
            and from_context.parent != to_context.parent
        ):
            raise FabricCLIError(
                ErrorMessages.Mv.mv_items_accross_folders_within_ws(),
                fab_constant.ERROR_NOT_SUPPORTED,
            )

        if _confirm_copy(args.force, is_move_command):
            item_already_exists = False
            existing_item_with_same_name = None
            destination_path = args.to_path

            existing_item_with_same_name = next(
                (item for item in ws_items_target if item.name == to_context.name), None
            )

            if existing_item_with_same_name:
                if existing_item_with_same_name.parent != to_context.parent:
                    if (
                        hasattr(args, "block_on_path_collision")
                        and args.block_on_path_collision
                    ):
                        raise FabricCLIError(
                            ErrorMessages.Cp.item_exists_different_path(),
                            fab_constant.ERROR_INVALID_INPUT,
                        )
                    else:
                        destination_path = existing_item_with_same_name.path

                item_already_exists = True
                fab_logger.log_warning(
                    fab_constant.WARNING_ITEM_EXISTS_IN_PATH.format(destination_path)
                )
                if args.force or utils_ui.prompt_confirm("Overwrite?"):
                    pass
                else:
                    return False
            utils_ui.print_grey(
                f"{'Moving' if delete_after_copy else 'Copying'} '{args.from_path}' → '{destination_path}'..."
            )
            # Copy including definition, cross ws
            _copy_item_with_definition(
                args,
                from_context,
                to_context,
                delete_after_copy,
                item_already_exists=item_already_exists,
            )
            return True
        else:
            return False
    except FabricCLIError as e:
        raise e


# Utils
def _confirm_copy(bypass_confirmation: bool, is_move_command: bool) -> bool:
    if not bool(bypass_confirmation):
        confirm_message = item_utils.get_confirm_copy_move_message(is_move_command)
        return utils_ui.prompt_confirm(confirm_message)
    return True


def _copy_item_with_definition(
    args: Namespace,
    from_item: Item,
    to_item: Item,
    delete_after_copy: Optional[bool],
    item_already_exists: Optional[bool] = False,
) -> None:

    # Obtain the source
    args.id = from_item.id
    args.ws_id = from_item.workspace.id
    args.format = ""
    item = item_api.get_item_withdefinition(args)
    payload = json.dumps(
        {
            "type": str(from_item.item_type),
            "description": item["description"],
            "displayName": to_item.short_name,
            "definition": item["definition"],
            "folderId": to_item.folder_id,
        }
    )

    # Create in target
    args.method = "post"
    args.ws_id = to_item.workspace.id
    args.item_type = str(to_item.type)

    if item_already_exists:
        args.id = to_item.id
        response = item_api.update_item_definition(args, payload=payload)
    else:
        response = item_api.create_item(args, payload=payload)

    if response.status_code in (200, 201, 202):
        args.ws_id = from_item.workspace.id

        if delete_after_copy:
            args.id = from_item.id
            args.name = from_item.name
            args.uri = None  # empty URI to delete item since it can be completed by a LRO response
            item_api.delete_item(args, bypass_confirmation=True, verbose=False)
            utils_mem_store.delete_item_from_cache(from_item)

        if not item_already_exists:
            data = json.loads(response.text)
            to_item._id = data["id"]

            # Add new one to mem_store
            utils_mem_store.upsert_item_to_cache(to_item)

        utils_ui.print_output_format(
            args, message=f"{'Move' if delete_after_copy else 'Copy'} completed"
        )
