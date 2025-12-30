# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Union

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.core.hiearchy.fab_workspace import Workspace
from fabric_cli.utils import fab_item_util as item_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def select_workspace_items(from_context):
    ws_elems: list[Item | Folder] = get_ws_elements(from_context)
    if not ws_elems:
        raise FabricCLIError(
            fab_constant.WARNING_WORKSPACE_EMPTY,
            fab_constant.ERROR_INVALID_OPERATION,
        )

    # Only filter those items supporting definition
    supported_elems: list[Item | Folder] = [
        f for f in ws_elems if isinstance(f, Folder)
    ]
    for item in [item for item in ws_elems if isinstance(item, Item)]:
        try:
            if item.check_command_support(Command.FS_EXPORT):
                supported_elems.append(item)
        except Exception:
            pass

    if not supported_elems:
        raise FabricCLIError(
            "Not possible. Your workspace items don't support definition",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    sorted_supported_elems = item_utils.sort_ws_elems_by_config(supported_elems)

    selected_elems = (
        utils_ui.prompt_select_items(
            "Select items:",
            [item.name for item in sorted_supported_elems],
        )
        or []
    )

    filtered_elems = [item for item in supported_elems if item.name in selected_elems]
    filtered_folders = [item for item in filtered_elems if isinstance(item, Folder)]
    filtered_items = [item for item in filtered_elems if isinstance(item, Item)]

    return selected_elems, filtered_folders, filtered_items


def get_ws_elements(parent: Workspace | Folder) -> list[Union[Item, Folder]]:
    ws_elements: list[Union[Item, Folder]] = []
    ws = parent.workspace if isinstance(parent, Folder) else parent
    ws_items: list[Item] = utils_mem_store.get_workspace_items(ws)

    if (
        isinstance(parent, Folder)
        or fab_state_config.get_config(fab_constant.FAB_FOLDER_LISTING_ENABLED)
        == "true"
    ):
        ws_folders: list[Folder] = utils_mem_store.get_workspace_folders(ws)
        ws_folders = [f for f in ws_folders if f.parent == parent]
        ws_items = [i for i in ws_items if i.parent == parent]
        ws_elements.extend(ws_folders)

    ws_elements.extend(ws_items)

    return ws_elements


def sort_ws_elements(ws_elements: list[Union[Item, Folder]], show_details):

    if not ws_elements:
        return []

    sorted_elements = item_utils.sort_ws_elems_by_config(ws_elements)
    columns = ["name", "id"] if show_details else ["name"]

    return [
        {key: getattr(item, key) for key in columns if hasattr(item, key)}
        for item in sorted_elements
    ]


def sort_ws_elements_with_separation(
    ws_elements: list[Union[Item, Folder]], show_details
) -> list[dict]:
    """
    Sort workspace elements with folders first, then items.
    If both folders and items exist, inserts a divider entry between them.
    
    Returns:
        list: Single list with folders first, optional divider, then items
    """
    if not ws_elements:
        return []

    type_order = [Folder, Item]
    divider_name = "------------------------------"
    
    result = []
    first_group = True

    for typ in type_order:
        group = [el for el in ws_elements if isinstance(el, typ)]
        if group:
            group_dicts = sort_ws_elements(group, show_details)
            if not first_group:
                divider = {"name": divider_name}
                if show_details:
                    divider["id"] = ""
                result.append(divider)
            result.extend(group_dicts)
            first_group = False

    return result
