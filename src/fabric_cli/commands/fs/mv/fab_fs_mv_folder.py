# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_folders as folders_api
from fabric_cli.commands.fs.cp import fab_fs_cp_folder as cp_folder
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def _change_folder_parent(folder: Folder, new_parent: Workspace | Folder) -> None:
    """
    Change the parent of a folder to a new parent.
    """
    if folder.parent == new_parent:
        utils_ui.print_warning(
            f"Folder '{folder.name}' is already in the target parent. Skipping."
        )
        return

    args = Namespace()
    args.ws_id = folder.workspace.id
    args.folder_id = folder.id
    body = {}
    if isinstance(new_parent, Folder):
        body["targetFolderId"] = new_parent.id

    response = folders_api.move_folder(args, json.dumps(body))

    if response.status_code == 200:
        # Update the folder in memory store
        folder._parent = new_parent
        utils_mem_store.upsert_folder_to_cache(folder)
        utils_ui.print_output_format(
            args,
            message=f"Move Completed for Folder '{folder.name}' to '{new_parent.name}'",
        )


def move_folder(
    from_folder: Folder,
    to_context: Workspace | Folder,
    args: Namespace,
) -> int:
    to_workspace = (
        to_context.workspace if isinstance(to_context, Folder) else to_context
    )

    if from_folder.workspace != to_workspace:
        return cp_folder.copy_folder(
            from_folder, to_context, args, delete_after_copy=True
        )
    elif from_folder.parent != to_context:
        _change_folder_parent(from_folder, to_context)
        return 1

    return 0


def move_folders(
    to_context: Workspace | Folder,
    filtered_folders: list[Folder],
    args: Namespace,
) -> int:
    """
    Copy a list of folders to the specified context (Workspace or Folder).
    If delete_after_copy is True, the original folders will be deleted after copying.
    """
    successful_moves = 0

    for folder in filtered_folders:
        successful_moves += move_folder(
            from_folder=folder,
            to_context=to_context,
            args=args,
        )

    return successful_moves
