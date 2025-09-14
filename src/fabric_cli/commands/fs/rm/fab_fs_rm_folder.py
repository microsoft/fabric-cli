# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_folders as folder_api
from fabric_cli.commands.fs.rm import fab_fs_rm_item as rm_item
from fabric_cli.core.hiearchy.fab_hiearchy import Folder
from fabric_cli.utils import fab_cmd_fs_utils as utils_fs
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(folder: Folder, args: Namespace, force_delete: bool) -> None:
    args.ws_id = folder.workspace.id
    args.folder_id = folder.id
    args.name = folder.name

    if folder_api.delete_folder(args, force_delete):
        # Remove from mem_store
        utils_mem_store.delete_folder_from_cache(folder)


def remove_folder_recursively(
    folder: Folder, args: Namespace, force_delete: bool
) -> None:
    """
    Recursively remove a folder and its contents.
    """
    elements = utils_fs.get_ws_elements(folder)
    for elem in elements:
        if isinstance(elem, Folder):
            remove_folder_recursively(elem, args, force_delete)
        else:
            # Handle other item types (e.g., files)
            rm_item.exec(elem, args, force_delete)

    if len(utils_fs.get_ws_elements(folder)) == 0:
        exec(folder, args, force_delete)
    else:
        utils_ui.print_warning(
            f"Folder '{folder.name}' is not empty. It will not be deleted."
        )
