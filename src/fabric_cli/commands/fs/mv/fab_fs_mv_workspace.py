# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.cp import fab_fs_cp_workspace as cp_workspace
from fabric_cli.commands.fs.mv import fab_fs_mv_folder as mv_folder
from fabric_cli.commands.fs.mv import fab_fs_mv_item as mv_items
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.utils import fab_cmd_fs_utils as fs_utils
from fabric_cli.utils import fab_ui as utils_ui


def move_workspace_elements(
    from_context: Workspace,
    to_context: Workspace | Folder,
    args: Namespace,
) -> None:

    selected_elements, filtered_folders, filtered_items = (
        fs_utils.select_workspace_items(from_context)
    )

    utils_ui.print_grey("\n".join(selected_elements))
    utils_ui.print_grey("------------------------------")

    to_workspace = (
        to_context.workspace if isinstance(to_context, Folder) else to_context
    )

    _move_message = "Move completed"

    if from_context == to_workspace:
        if from_context != to_context:
            # 1. Move items
            nitems = mv_items.move_items(
                to_context,
                filtered_items,
                args,
            )
            # 2. Move folders
            nfolders = mv_folder.move_folders(
                to_context,
                filtered_folders,
                args,
            )
            nitems_str = f"{nitems} item" if nitems == 1 else f"{nitems} items"
            nfolders_str = (
                f"{nfolders} folder" if nfolders == 1 else f"{nfolders} folders"
            )
            _move_message = f"Moved {nitems_str} and {nfolders_str} completed"

    else:
        # delete_from_item is true when calling move command
        cp_workspace.execute_copy_operation(
            from_context,
            to_context,
            args,
            filtered_folders,
            filtered_items,
            delete_after_copy=True,
        )

    utils_ui.print_output_format(args, message=_move_message)
