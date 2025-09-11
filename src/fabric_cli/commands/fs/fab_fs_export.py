# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.export import fab_fs_export_item as export_item
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Item, Workspace
from fabric_cli.utils import fab_item_util, fab_ui, fab_util


def exec_command(args: Namespace, context: FabricElement) -> None:
    args.output = fab_util.process_nargs(args.output)

    if isinstance(context, Workspace):
        fab_item_util.item_sensitivity_label_warnings(args, "exported")
        export_item.export_bulk_items(context, args)
    elif isinstance(context, Item):
        fab_item_util.item_sensitivity_label_warnings(args, "exported")
        export_item.export_single_item(context, args)
        fab_ui.print_output_format(args, message=f"'{context.full_name}' exported")
