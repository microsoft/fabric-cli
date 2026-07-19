# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from argparse import Namespace

from fabric_cli.commands.fs.bulk_export.fab_fs_bulk_export_folder import (
    bulk_export_folder,
)
from fabric_cli.commands.fs.bulk_export.fab_fs_bulk_export_workspace import (
    bulk_export_workspace,
)
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Workspace
from fabric_cli.errors.bulk_export import BulkExportErrors
from fabric_cli.utils import fab_storage
from fabric_cli.utils import fab_ui, fab_util


def exec_command(args: Namespace, context: FabricElement) -> None:
    args.output = fab_util.process_nargs(args.output)

    if not isinstance(context, (Workspace, Folder)):
        raise FabricCLIError(
            BulkExportErrors.invalid_target(context.full_name),
            fab_constant.ERROR_INVALID_OPERATION,
        )

    _validate_bulk_export_arguments(args)
    if not _confirm_export_preconditions(args):
        return
    if isinstance(context, Workspace):
        bulk_export_workspace(context, args)
    elif isinstance(context, Folder):
        bulk_export_folder(context, args)


def _validate_bulk_export_arguments(args: Namespace) -> None:
    """Validate required flags for workspace/folder bulk-export."""
    if not args.recursive:
        raise FabricCLIError(
            BulkExportErrors.recursive_flag_required(),
            fab_constant.ERROR_INVALID_OPERATION,
        )
    if not args.output:
        raise FabricCLIError(
            BulkExportErrors.invalid_export_path(""),
            fab_constant.ERROR_INVALID_OPERATION,
        )


def _confirm_export_preconditions(args: Namespace) -> bool:
    """Validate export preconditions and prompt for confirmations. Returns True if all confirmed or --force is set."""
    export_path_warning = False
    export_path = fab_storage.get_export_path(args.output)
    if (export_path["type"] != "local") or (
        export_path["type"] == "local" and not os.path.isdir(export_path["path"])
    ):
        raise FabricCLIError(
            BulkExportErrors.invalid_export_path(export_path["path"]),
            fab_constant.ERROR_INVALID_OPERATION,
        )
    if os.path.isdir(export_path["path"]):
        is_export_path_empty = True
        with os.scandir(export_path["path"]) as entries:
            is_export_path_empty = not any(entries)
        if not is_export_path_empty:
            if not args.force:
                if not fab_ui.prompt_confirm(
                    f"Output folder '{export_path['path']}' is not empty. Do you want to proceed?"
                ):
                    return False
            else:
                export_path_warning = True
    else:
        os.makedirs(export_path["path"], exist_ok=True)

    if args.force:
        fab_ui.print_warning(
            "Item definitions are exported without their sensitivity labels"
        )
        if export_path_warning:
            fab_ui.print_warning("Exporting to a non-empty output folder")
        return True
    return fab_ui.prompt_confirm(
        "Item definitions are exported without their sensitivity labels. Are you sure?"
    )
