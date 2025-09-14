# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.commands.fs.cp import fab_fs_cp_folder as cp_folder
from fabric_cli.commands.fs.cp import fab_fs_cp_item as cp_item
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.utils import fab_cmd_fs_utils as fs_utils
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as util
from fabric_cli.utils import fab_item_util as item_utils


def copy_workspace_elements(
    from_context: Workspace,
    to_context: Workspace | Folder,
    args: Namespace,
) -> None:

    selected_elements, filtered_folders, filtered_items = (
        fs_utils.select_workspace_items(from_context)
    )

    utils_ui.print_grey("\n".join(selected_elements))
    utils_ui.print_grey("------------------------------")

    execute_copy_operation(
        from_context,
        to_context,
        args,
        filtered_folders,
        filtered_items,
    )


def execute_copy_operation(
    from_context,
    to_context,
    args,
    filtered_folders,
    filtered_items,
    delete_after_copy=False,
):
    is_move_command = delete_after_copy if delete_after_copy is not None else False
    confirm_message = item_utils.get_confirm_copy_move_message(is_move_command)

    if args.force or utils_ui.prompt_confirm(confirm_message):
        ui_texts = []
        if filtered_items:
            # Sort output by config
            n_items = cp_item.copy_items(
                filtered_items, to_context, args, delete_after_copy
            )
            ui_texts.append(f"{n_items} items")

        if filtered_folders and args.recursive:
            for folder in filtered_folders:
                cp_folder.copy_folder(
                    from_folder=folder,
                    to_context=to_context,
                    args=args,
                    delete_after_copy=delete_after_copy,
                )
            ui_texts.append(f"{len(filtered_folders)} folders")

        ui_text = (
            " and ".join(ui_texts) if len(ui_texts) > 0 else "No items nor folders"
        )

        utils_ui.print_output_format(
            args,
            message=f"{ui_text} {'moved' if delete_after_copy else 'copied'} successfully from {from_context.path} to {to_context.path}",
        )
