# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    VirtualItem,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace, context: FabricElement) -> None:
    if (
        isinstance(context, Workspace)
        or isinstance(context, Item)
        or isinstance(context, VirtualWorkspaceItem)
        or isinstance(context, VirtualItem)
        or isinstance(context, Folder)
    ):
        _check_if_element_exists(context, args)
    elif isinstance(context, OneLakeItem):
        _check_if_onelake_file_or_directory_exists(context, args)


# Workspaces and Items
def _check_if_element_exists(element: FabricElement, args: Namespace) -> None:
    text_message = True if element.id else False
    utils_ui.print_output_format(args, message=text_message)


# OneLake - Shortcut, File and Folder
def _check_if_onelake_file_or_directory_exists(
    context: OneLakeItem, args: Namespace
) -> None:
    workspace_id = context.workspace.id
    item_id = context.item.id
    local_path = utils.remove_dot_suffix(context.local_path)

    args.directory = f"{workspace_id}/?recursive=false&resource=filesystem&directory={item_id}/{local_path}&getShortcutMetadata=true"
    try:
        onelake_api.list_tables_files_recursive(args)
        utils_ui.print_output_format(args, message=True)
    except FabricCLIError as e:
        if e.status_code == fab_constant.ERROR_NOT_FOUND:
            utils_ui.print_output_format(args, message=False)
        else:
            raise e
