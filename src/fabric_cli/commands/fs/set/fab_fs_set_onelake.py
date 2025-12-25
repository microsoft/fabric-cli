# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_shortcuts as shortcut_api
from fabric_cli.commands.fs.get import fab_fs_get_onelake as get_onelake
from fabric_cli.commands.fs.rm import fab_fs_rm_onelake as rm_onelake
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import OneLakeItem
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_SHORTCUT = ["name", "target"]


def onelake_shortcut(onelake: OneLakeItem, args: Namespace) -> None:
    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_SHORTCUT)

    # Get shortcut
    args.output = None
    args.deep_traversal = True
    shortcut_def = get_onelake.onelake_shortcut(onelake, args, verbose=False)
    current_name = shortcut_def.get("name", "")

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        # Read new values from the user and retrieve updated shortcut definition with the new values.
        updated_def = utils_set.update_fabric_element(
            shortcut_def, query, args.input, extract_updated_only=False
        )

        # Check if the new name matches the existing name
        new_name = updated_def.get("name", "")
        if new_name == current_name:
            raise FabricCLIError(
                f"The new name matches the existing name. No changes will be made",
                fab_constant.ERROR_INVALID_INPUT,
            )

        if "target" in updated_def and "type" in updated_def["target"]:
            del updated_def["target"]["type"]
        json_payload = updated_def

        # Create a new shortcut with the updated values
        args.shortcutConflictPolicy = "Abort"
        shortcut_api.create_shortcut(args, json_payload)

        # Delete the old shortcut
        rm_onelake.shortcut_file_or_folder(
            onelake, args, force_delete=True, verbose=False
        )
        utils_ui.print_output_format(args, message="Shortcut updated")
