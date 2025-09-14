# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Union

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Tenant, Workspace
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils
from fabric_cli.utils import fab_item_util as item_utils


def bulk(tenant: Tenant, args: Namespace, force_delete: bool) -> None:
    workspaces: list[Workspace] = utils_mem_store.get_workspaces(tenant)
    sorted_workspaces: list[Workspace] = sorted(workspaces, key=lambda ws: ws.name)

    names = [workspace.name for workspace in sorted_workspaces]
    selected_workspaces = utils_ui.prompt_select_items("Select workspaces:", names)
    if selected_workspaces:
        for workspace_str in selected_workspaces:
            utils_ui.print_grey(workspace_str)
        utils_ui.print_grey("------------------------------")
        filtered_workspaces = [
            workspace
            for workspace in sorted_workspaces
            if workspace.name in selected_workspaces
        ]
        if utils_ui.prompt_confirm():

            deleted_workspaces = 0

            for workspace in filtered_workspaces:
                args.ws_id = workspace.id
                args.name = workspace.name

                # Reset args for subsequent calls
                args.uri = None
                args.method = None

                if workspace_api.delete_workspace(args, bypass_confirmation=True):
                    deleted_workspaces = deleted_workspaces + 1

                    # Remove from mem_store
                    utils_mem_store.delete_workspace_from_cache(workspace)

            utils_ui.print("")
            utils_ui.print_output_format(args, message=f"{deleted_workspaces} workspaces deleted successfully")


def single(workspace: Workspace, args: Namespace, force_delete: bool) -> None:
    args.ws_id = workspace.id
    args.name = workspace.name

    ws_items: list[Item] = utils_mem_store.get_workspace_items(workspace)

    # Empty workspace
    if not ws_items and not force_delete:
        raise FabricCLIError(
            "Empty workspace. Use -f to remove it",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    # Filter items supporting rm
    supported_items: list[Union[Item, Folder]] = []
    for item in ws_items:
        try:
            if item.check_command_support(Command.FS_RM):
                supported_items.append(item)
        except Exception:
            pass

    if force_delete:
        utils_ui.print_grey(f"This will delete {len(ws_items)} underlying items")

        if workspace_api.delete_workspace(args, force_delete):
            # Remove from mem_store
            utils_mem_store.delete_workspace_from_cache(workspace)
    else:
        # Some items don't support delete
        if not supported_items:
            raise FabricCLIError(
                "Items can't be deleted. Use -f to remove the workspace",
                fab_constant.ERROR_NOT_SUPPORTED,
            )
        else:
            # Sort output by config
            sorted_items = item_utils.sort_ws_elems_by_config(supported_items)

            names = [item.name for item in sorted_items]
            selected_items = utils_ui.prompt_select_items("Select items:", names)
            if selected_items:
                for item_str in selected_items:
                    utils_ui.print_grey(item_str)
                utils_ui.print_grey("------------------------------")
                filtered_items = [
                    item
                    for item in sorted_items
                    if item.name in selected_items and isinstance(item, Item)
                ]
                if utils_ui.prompt_confirm():

                    deleted_items = 0

                    for item in filtered_items:
                        args.id = item.id
                        args.name = item.name
                        args.item_type = str(item.item_type)

                        # Reset args for subsequent calls
                        args.uri = None
                        args.method = None

                        if item_api.delete_item(
                            args, bypass_confirmation=True, verbose=False
                        ):
                            utils_ui.print_output_format(args, message=f"'{args.name}' deleted")
                            deleted_items = deleted_items + 1

                            # Remove from mem_store
                            utils_mem_store.delete_item_from_cache(item)

                    utils_ui.print("")
                    utils_ui.print_output_format(args, message=f"{deleted_items} items deleted successfully")
