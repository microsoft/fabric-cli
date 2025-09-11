# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import re
from argparse import Namespace

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item, OneLakeItem
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils
from fabric_cli.utils import fab_item_util as item_utils


def move_onelake_file(
    from_context: OneLakeItem, to_context: OneLakeItem, args: Namespace
) -> None:
    # Only supported in Lakehouse
    item: Item = from_context.item
    item_type = item.item_type

    if item_type != ItemType.LAKEHOUSE:
        raise FabricCLIError(
            fab_constant.WARNING_MKDIR_INVALID_ONELAKE, fab_constant.ERROR_NOT_SUPPORTED
        )

    from_local_path = utils.remove_dot_suffix(from_context.local_path)
    to_local_path = utils.remove_dot_suffix(to_context.local_path)

    # Only supported in /Files
    pattern = r"^/?Files(?:/[^/]+)*$"
    if re.match(pattern, from_local_path) and re.match(pattern, to_local_path):

        # Extract IDs
        from_path_id, from_path_name, to_path_id, to_path_name = (
            item_utils.obtain_id_names_for_onelake(from_context, to_context)
        )

        args.from_path = from_path_id
        args.to_path = to_path_id

        if _confirm_move(args.force):
            utils_ui.print_grey(f"Moving '{from_path_name}' → '{to_path_name}'...")

            response = onelake_api.move_rename(args)
            if response.status_code in (200, 201):
                utils_ui.print_output_format(args, message="Move onelake file completed succesfully"
                )
    else:
        raise FabricCLIError(
            fab_constant.WARNING_MKDIR_INVALID_ONELAKE, fab_constant.ERROR_NOT_SUPPORTED
        )


# Utils
def _confirm_move(bypass_confirmation: bool) -> bool:
    if not bool(bypass_confirmation):
        return utils_ui.prompt_confirm()
    return True
