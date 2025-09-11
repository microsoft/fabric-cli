# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.mv import fab_fs_mv_folder as mv_folder
from fabric_cli.commands.fs.mv import fab_fs_mv_item as mv_item
from fabric_cli.commands.fs.mv import fab_fs_mv_onelake as mv_onelake
from fabric_cli.commands.fs.mv import fab_fs_mv_workspace as mv_workspace
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    OneLakeItem,
    Workspace,
)
from fabric_cli.utils import fab_item_util


def exec_command(
    args: Namespace, from_context: FabricElement, to_context: FabricElement
) -> None:
    args.from_path = from_context.path
    args.to_path = to_context.path

    if isinstance(from_context, Workspace) and isinstance(
        to_context, Workspace | Folder
    ):
        fab_item_util.item_sensitivity_label_warnings(args, "moved")
        mv_workspace.move_workspace_elements(from_context, to_context, args)
    elif isinstance(from_context, Folder) and isinstance(
        to_context, Workspace | Folder
    ):
        fab_item_util.item_sensitivity_label_warnings(args, "moved")
        mv_folder.move_folder(from_context, to_context, args)
    elif isinstance(from_context, Item) and isinstance(
        to_context, Item | Workspace | Folder
    ):
        fab_item_util.item_sensitivity_label_warnings(args, "moved")
        mv_item.move_item(from_context, to_context, args)
    elif isinstance(from_context, OneLakeItem) and isinstance(
            to_context, OneLakeItem
        ):
            mv_onelake.move_onelake_file(from_context, to_context, args)
    else:
        if from_context.type != to_context.type:
            raise FabricCLIError(
                fab_constant.WARNING_INVALID_PATHS, fab_constant.ERROR_INVALID_INPUT
            )

        raise FabricCLIError(
            fab_constant.WARNING_NOT_SUPPORTED_PATHS, fab_constant.ERROR_NOT_SUPPORTED
        )
