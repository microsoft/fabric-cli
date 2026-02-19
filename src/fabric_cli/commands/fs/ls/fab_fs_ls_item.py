# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Union

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_types import VirtualItemContainerType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Workspace
from fabric_cli.utils import fab_cmd_fs_utils as utils_fs
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls

# Divider used to separate folders and items in workspace listings
_DIVIDER = "------------------------------"


def _sort_ws_elements_with_seperation(
    ws_elements: list[Union[Item, Folder]], show_details: bool
) -> list[dict]:
    """
    Groups elements by type (Folders first, then Items), sorts each group using sort_ws_elements,
    and inserts a divider between non-empty groups.

    Args:
        ws_elements: List of workspace elements (Items and Folders)
        show_details: Whether to include detailed columns

    Returns:
        list: Single list with folders first, divider, then items
    """
    if not ws_elements:
        return []

    result = []
    first_group = True
    type_order = [Folder, Item]

    for typ in type_order:
        group = [el for el in ws_elements if isinstance(el, typ)]
        if group:
            group_dicts = utils_fs.sort_ws_elements(group, show_details)
            if not first_group:
                divider = {"name": _DIVIDER}
                if show_details:
                    divider["id"] = ""
                result.append(divider)
            result.extend(group_dicts)
            first_group = False

    return result


def exec(workspace: Workspace, args):
    show_details = bool(args.long)
    show_all = bool(args.all)
    ws_elements: list[Union[Item, Folder]] = utils_fs.get_ws_elements(workspace)

    # Check if folder listing is enabled
    folder_listing_enabled = (
        fab_state_config.get_config(fab_constant.FAB_FOLDER_LISTING_ENABLED) == "true"
    )

    # Get output format from args or config
    output_format = getattr(args, "output_format", None) or fab_state_config.get_config(
        fab_constant.FAB_OUTPUT_FORMAT
    )

    # Use separation if folder listing is enabled, output is text format, and --long is not provided
    if folder_listing_enabled and output_format == "text" and not show_details:
        sorted_elements_dict = _sort_ws_elements_with_seperation(
            ws_elements, show_details
        )
    else:
        sorted_elements_dict = utils_fs.sort_ws_elements(ws_elements, show_details)

    show_hidden = (
        show_all or fab_state_config.get_config(fab_constant.FAB_SHOW_HIDDEN) == "true"
    )

    utils_ls.format_and_print_output(
        data=sorted_elements_dict,
        args=args,
        show_details=show_details,
        columns=sorted_elements_dict[0].keys() if sorted_elements_dict else [],
        hidden_data=VirtualItemContainerType if show_hidden else None,
    )
