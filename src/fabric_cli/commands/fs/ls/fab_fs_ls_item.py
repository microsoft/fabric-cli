# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Union

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_types import VirtualItemContainerType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Workspace
from fabric_cli.utils import fab_cmd_fs_utils as utils_fs
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls


def exec(workspace: Workspace, args):
    show_details = bool(args.long)
    show_all = bool(args.all)
    ws_elements: list[Union[Item, Folder]] = utils_fs.get_ws_elements(workspace)
    
    # Check if folder listing is enabled and we should separate folders and items
    folder_listing_enabled = (
        fab_state_config.get_config(fab_constant.FAB_FOLDER_LISTING_ENABLED) == "true"
    )
    
    # Separate folders and items if folder listing is enabled
    if folder_listing_enabled and ws_elements:
        folders_dict, items_dict = utils_fs.sort_ws_elements_with_separation(
            ws_elements, show_details
        )
        # Combine for columns detection
        sorted_elements_dict = folders_dict + items_dict if folders_dict or items_dict else []
        folders_for_output = folders_dict if folders_dict else None
        items_for_output = items_dict if items_dict else None
    else:
        sorted_elements_dict = utils_fs.sort_ws_elements(ws_elements, show_details)
        folders_for_output = None
        items_for_output = None

    show_hidden = (
        show_all or fab_state_config.get_config(fab_constant.FAB_SHOW_HIDDEN) == "true"
    )

    utils_ls.format_and_print_output(
        data=sorted_elements_dict,
        args=args,
        show_details=show_details,
        columns=sorted_elements_dict[0].keys() if sorted_elements_dict else [],
        hidden_data=VirtualItemContainerType if show_hidden else None,
        folders_data=folders_for_output,
        items_data=items_for_output,
    )
