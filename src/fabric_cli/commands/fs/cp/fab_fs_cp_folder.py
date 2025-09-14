# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_folders as folders_api
from fabric_cli.commands.fs.cp import fab_fs_cp_item as cp_item
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_folder as fs_mkdir_folder
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Folder, Item, Workspace
from fabric_cli.utils import fab_cmd_fs_utils as utils_fs
from fabric_cli.utils import fab_ui as utils_ui


def copy_folders(
    filtered_folders: list[Folder],
    to_context: Workspace | Folder,
    args: Namespace,
    delete_after_copy: Optional[bool] = False,
) -> int:
    """
    Copy a list of folders to the specified context (Workspace or Folder).
    If delete_after_copy is True, the original folders will be deleted after copying.
    """
    successful_copies = 0

    for folder in filtered_folders:
        successful_copies += copy_folder(
            from_folder=folder,
            to_context=to_context,
            args=args,
            delete_after_copy=delete_after_copy,
        )

    return successful_copies


def copy_folder(
    from_folder: Folder,
    to_context: Folder | Workspace,
    args: Namespace,
    delete_after_copy: Optional[bool] = False,
) -> int:

    # When copying a folder, recursive is always required
    # When moving a folder it is not
    if not delete_after_copy and not args.recursive:
        raise FabricCLIError(
            f"The --recursive option is required for copying folders.",
            fab_constant.ERROR_INVALID_OPERATION,
        )

    to_folder = _get_destination_folder(from_folder, to_context)
    unsupported_items: list[Item] = _get_nested_unsupported_items(from_folder)
    unsupported_items_names = [item.name for item in unsupported_items]

    if unsupported_items:
        if not args.force and not utils_ui.prompt_confirm(
            f"Folder '{from_folder.name}' contains items that do not support copying: {unsupported_items_names}. Do you still want to proceed?"
        ):
            return 0

    supported_items: list[Item] = []
    folders: list[Folder] = []
    n_items = 0
    n_folders = 0

    for item in utils_fs.get_ws_elements(from_folder):
        if isinstance(item, Item):
            try:
                item.check_command_support(Command.FS_CP)
                supported_items.append(item)
            except FabricCLIError as e:
                if e.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND:
                    pass
                else:
                    raise e
        elif isinstance(item, Folder):
            folders.append(item)

    if not supported_items:
        utils_ui.print_warning(
            f"No items in folder '{from_folder.name}' support definition. Skipping copy."
        )
    else:
        n_items += cp_item.copy_items(
            supported_items, to_folder, args, delete_after_copy
        )

        _n_items, _n_folders = _copy_nested_folders(
            from_folder=from_folder,
            to_context=to_folder,
            args=args,
            delete_after_copy=delete_after_copy,
        )
        n_items += _n_items
        n_folders += _n_folders

    if len(unsupported_items) == 0 and delete_after_copy:
        pending_elements = utils_fs.get_ws_elements(from_folder)
        if len(pending_elements) > 0:
            utils_ui.print_warning(
                f"Folder '{from_folder.name}' is not empty. It will not be deleted."
            )
        else:
            _args = Namespace(
                name=from_folder.name,
                ws_id=from_folder.workspace.id,
                folder_id=from_folder.id,
            )
            folders_api.delete_folder(_args, bypass_confirmation=True)

    utils_ui.print_output_format(
        args,
        message=f"Copied {n_items} items and {n_folders} folders from '{from_folder.name}' to '{to_context.name}'",
    )

    return n_items + n_folders


# Utils


def _get_destination_folder(
    from_folder: Folder, to_context: Workspace | Folder
) -> Folder:
    """
    Get the destination folder for the copy operation.
    If the destination is a Workspace or an existing folder, create a new folder with the same name as the source folder.
    If the destination workspace is the same as the source folder's workspace, append "_copy" to the folder name.
    If the destination is a non-existent Folder (no ID), create such folder.
    """
    if isinstance(to_context, Workspace) or (
        isinstance(to_context, Folder) and to_context.id is not None
    ):
        to_workspace = (
            to_context.workspace if isinstance(to_context, Folder) else to_context
        )
        # avoid name collision in the workspace - names must be unique even if in different folders
        new_folder_name = (
            f"{from_folder.short_name}_copy.Folder"
            if to_workspace == from_folder.workspace
            else from_folder.name
        )
        new_folder_path = f"{to_context.path}/{new_folder_name}"
        new_folder = handle_context.get_command_context(new_folder_path, False)
    else:
        assert isinstance(to_context, Folder) and to_context.id is None
        new_folder = to_context

    assert isinstance(new_folder, Folder)
    _args = Namespace(force=True)
    fs_mkdir_folder.exec(new_folder, _args)
    return new_folder


def _copy_nested_folders(
    from_folder: Folder,
    to_context: Workspace | Folder,
    args: Namespace,
    delete_after_copy: Optional[bool] = False,
) -> tuple[int, int]:
    """
    Copy all nested folders from the source folder to the destination context.
    """
    nested_folders = _get_nested_folders(from_folder, args)
    n_copied_items = 0
    for nested_folder in nested_folders:
        new_folder_path = (
            f"{to_context.path}/{nested_folder.path.replace(from_folder.path, '')}"
        )
        new_folder = handle_context.get_command_context(new_folder_path, False)
        assert isinstance(new_folder, Folder)
        if new_folder.id is None:
            _args = Namespace()
            _args.force = True  # Force creation of the folder
            fs_mkdir_folder.exec(new_folder, _args)
        else:
            utils_ui.print_warning(
                f"Folder '{new_folder.name}' already exists. Skipping creation."
            )
        args.from_path = nested_folder.path
        args.to_path = new_folder.path

        supported_items: list[Item] = []

        for item in utils_fs.get_ws_elements(nested_folder):
            try:
                if isinstance(item, Item) and item.check_command_support(
                    Command.FS_EXPORT
                ):
                    supported_items.append(item)
            except Exception:
                pass

        if not supported_items:
            utils_ui.print_warning(
                f"No items in folder '{nested_folder.name}' support definition."
            )
        else:
            n_copied_items += cp_item.copy_items(
                supported_items, new_folder, args, delete_after_copy
            )
        if delete_after_copy:
            _delete_folder_after_cp(nested_folder)

    return n_copied_items, len(nested_folders)


def _delete_folder_after_cp(folder: Folder):
    pending_elements = utils_fs.get_ws_elements(folder)
    if len(pending_elements) > 0:
        utils_ui.print_warning(
            f"Folder '{folder.name}' is not empty. It will not be deleted."
        )
    else:
        _args = Namespace(
            name=folder.name, ws_id=folder.workspace.id, folder_id=folder.id
        )
        folders_api.delete_folder(_args, bypass_confirmation=True)


def _get_nested_folders(folder: Folder, args: Namespace) -> list[Folder]:
    """
    Get all nested folders in a folder.
    """
    if not args.recursive:
        return []

    nested_folders = []
    for item in utils_fs.get_ws_elements(folder):
        if isinstance(item, Folder):
            nested_folders.append(item)
            nested_folders.extend(_get_nested_folders(item, args))

    return nested_folders


def _get_nested_unsupported_items(folder: Folder) -> list[Item]:
    """
    Get all items in a folder that do not support the FS_CP command.
    """
    unsupported_items = []
    for elem in utils_fs.get_ws_elements(folder):
        if isinstance(elem, Item):
            try:
                elem.check_command_support(Command.FS_CP)
            except FabricCLIError as e:
                if e.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND:
                    unsupported_items.append(elem)
                else:
                    raise e
        elif isinstance(elem, Folder):
            unsupported_items.extend(_get_nested_unsupported_items(elem))

    return unsupported_items
