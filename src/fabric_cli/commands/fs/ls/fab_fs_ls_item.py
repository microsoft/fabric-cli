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
    
    # Check if folder listing is enabled
    folder_listing_enabled = (
        fab_state_config.get_config(fab_constant.FAB_FOLDER_LISTING_ENABLED) == "true"
    )
    
    # Use separation if folder listing is enabled
    if folder_listing_enabled and ws_elements:
        sorted_elements_dict = utils_fs.sort_ws_elements_with_seperation_by_type_order(
            ws_elements, show_details, type_order=[Folder, Item]
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
