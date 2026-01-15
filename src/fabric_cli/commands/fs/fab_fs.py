# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import re
from argparse import Namespace

from fabric_cli.client import fab_api_azure as azure_api
from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.commands.fs import fab_fs_assign as fs_assign
from fabric_cli.commands.fs import fab_fs_cd as fs_cd
from fabric_cli.commands.fs import fab_fs_cp as fs_cp
from fabric_cli.commands.fs import fab_fs_exists as fs_exists
from fabric_cli.commands.fs import fab_fs_export as fs_export
from fabric_cli.commands.fs import fab_fs_get as fs_get
from fabric_cli.commands.fs import fab_fs_import as fs_import
from fabric_cli.commands.fs import fab_fs_ln as fs_ln
from fabric_cli.commands.fs import fab_fs_ls as fs_ls
from fabric_cli.commands.fs import fab_fs_mkdir as fs_mkdir
from fabric_cli.commands.fs import fab_fs_mv as fs_mv
from fabric_cli.commands.fs import fab_fs_open as fs_open
from fabric_cli.commands.fs import fab_fs_rm as fs_rm
from fabric_cli.commands.fs import fab_fs_set as fs_set
from fabric_cli.commands.fs import fab_fs_start as fs_start
from fabric_cli.commands.fs import fab_fs_stop as fs_stop
from fabric_cli.commands.fs import fab_fs_unassign as fs_unassign
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core import fab_state_config as state_config
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_hiearchy import (
    Item,
    LocalPath,
    OneLakeItem,
    Tenant,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.utils import fab_ui as utils_ui

COMMAND_GROUP = "fs"


@handle_exceptions()
@set_command_context()
def ls_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_LS)
    fs_ls.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def cd_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_CD)
    fs_cd.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def mkdir_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path, False)
    context.check_command_support(Command.FS_MKDIR)
    fs_mkdir.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def rm_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    _check_command_line_support(args.fab_mode, context, args.force)
    context.check_command_support(Command.FS_RM)
    fs_rm.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def mv_command(args: Namespace) -> None:
    from_context, to_context = extract_from_to_paths(args)
    _check_command_line_support(args.fab_mode, from_context, False)
    from_context.check_command_support(Command.FS_MV)
    fs_mv.exec_command(args, from_context, to_context)


@handle_exceptions()
@set_command_context()
def cp_command(args: Namespace) -> None:
    from_context, to_context = extract_from_to_paths(args)
    _check_command_line_support(args.fab_mode, from_context, False)
    from_context.check_command_support(Command.FS_CP)
    fs_cp.exec_command(args, from_context, to_context)


@handle_exceptions()
@set_command_context()
def exists_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path, False)
    context.check_command_support(Command.FS_EXISTS)
    fs_exists.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def open_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_OPEN)
    fs_open.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def pwd_command(args: Namespace) -> None:
    _print_context()


@handle_exceptions()
@set_command_context()
def export_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    _check_command_line_support(args.fab_mode, context, (args.force or args.all))
    context.check_command_support(Command.FS_EXPORT)
    fs_export.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def get_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_GET)
    fs_get.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def import_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path, raise_error=False)
    context.check_command_support(Command.FS_IMPORT)
    fs_import.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def set_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_SET)
    fs_set.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def ln_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path, False)
    context.check_command_support(Command.FS_LN)
    assert isinstance(context, OneLakeItem)
    fs_ln.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def start_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_START)
    fs_start.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def stop_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.FS_STOP)
    fs_stop.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def assign_command(args: Namespace) -> None:
    from_context = handle_context.get_command_context(args.path)
    from_context.check_command_support(Command.FS_ASSIGN)
    to_context = handle_context.get_command_context(args.workspace)
    fs_assign.exec_command(args, from_context, to_context)


@handle_exceptions()
@set_command_context()
def unassign_command(args: Namespace) -> None:
    from_context = handle_context.get_command_context(args.path)
    from_context.check_command_support(Command.FS_UNASSIGN)
    to_context = handle_context.get_command_context(args.workspace)
    fs_unassign.exec_command(args, from_context, to_context)


# Utils
def extract_from_to_paths(
    args: Namespace,
):
    if len(args.from_path) == len(args.to_path) == 1:
        args.path = args.from_path
        from_context = handle_context.get_command_context(
            args.path, supports_local_path=True
        )
        args.path = args.to_path
        to_context = handle_context.get_command_context(
            args.path, raise_error=False, supports_local_path=True
        )
        return from_context, to_context
    else:
        combined_paths = args.from_path + args.to_path
        # Iterate until finding the first correct path as from_path and assume the rest is the valid to_path
        for i in range(1, len(combined_paths)):
            args.path = combined_paths[:i]
            try:
                from_context = handle_context.get_command_context(
                    args.path, supports_local_path=True
                )
                args.path = combined_paths[i:]
                to_context = handle_context.get_command_context(
                    args.path, raise_error=False, supports_local_path=True
                )
                # Check that all paths are of type OneLakeItem
                if all(
                    isinstance(context, OneLakeItem)
                    or isinstance(context, Item)
                    or isinstance(context, LocalPath)
                    for context in (from_context, to_context)
                ) or (
                    isinstance(from_context, Workspace)
                    and isinstance(to_context, Workspace)
                ):
                    return from_context, to_context
            except FabricCLIError:
                continue
        # If no valid path is found, raise an error
        raise FabricCLIError("Invalid path", fab_constant.ERROR_INVALID_PATH)


def _print_context() -> None:
    context = Context().context

    full_name = context.name
    name = full_name.split(".")[0]
    type_ = "." + full_name.split(".")[1] if "." in full_name else ""
    id_ = context.id if context.id else ""

    # Local path is the current working directory of the python process using the os module
    data = {"name": name, "type": type_, "id": id_, "local_path": os.getcwd()}

    utils_ui.print_grey(json.dumps(data, indent=4))


def _check_command_line_support(mode: str, context: FabricElement, force: bool) -> None:
    if mode == fab_constant.FAB_MODE_COMMANDLINE and isinstance(context, Tenant):
        raise FabricCLIError(
            f"Not supported in '{mode}' mode",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    # Only supported in Interactive mode
    if (
        mode == fab_constant.FAB_MODE_COMMANDLINE
        and isinstance(context, Workspace)
        and not force
    ):
        raise FabricCLIError(
            f"Not supported in '{mode}' mode",
            fab_constant.ERROR_NOT_SUPPORTED,
        )


# Capacity Utils
def _search_capacity_id(capacity_name: str) -> str | None:
    cp_name = capacity_name
    args = Namespace()
    api_response = azure_api.list_subscriptions_azure(args)
    if api_response.status_code != 200:
        raise FabricCLIError(
            "Failed to list subscriptions", fab_constant.ERROR_NOT_FOUND
        )
    subscriptions = json.loads(api_response.text)["value"]
    for sub in subscriptions:
        sub_id = sub["id"].split("/")[-1]
        _args = Namespace()
        _args.subscription_id = sub_id
        capacities_req = capacity_api.list_capacities_azure(_args)
        capacities = json.loads(capacities_req.text)["value"]
        capacity = next(
            (item for item in capacities if item["name"].lower() == cp_name.lower()),
            None,
        )
        if capacity:
            return capacity["id"]

    return None


def _get_capacity_id(
    capacity_name, subscription_id=None, resource_group_name=None
) -> str | None:
    import time
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        if subscription_id and resource_group_name:
            args = Namespace()
            args.name = capacity_name
            args.subscription_id = subscription_id
            args.resource_group_name = resource_group_name
            try:
                response = capacity_api.get_capacity(args)
                if response.status_code == 200:
                    return json.loads(response.text)["id"]
            except FabricCLIError:
                pass  # Continue to fallback search
        
        # Fallback to searching across subscriptions
        capacity_id = _search_capacity_id(capacity_name)
        if capacity_id:
            return capacity_id
            
        # If not found and we still have retries left, wait and try again
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    return None


def get_all_az_capacities() -> list:
    args = Namespace()
    api_response = azure_api.list_subscriptions_azure(args)
    if api_response.status_code != 200:
        raise FabricCLIError(
            "Failed to list subscriptions", fab_constant.ERROR_NOT_FOUND
        )
    subscriptions = json.loads(api_response.text)["value"]
    capacities = []
    for sub in subscriptions:
        sub_id = sub["id"].split("/")[-1]
        _args = Namespace()
        _args.subscription_id = sub_id
        capacities_req = capacity_api.list_capacities_azure(_args)
        capacities += json.loads(capacities_req.text)["value"]
    return capacities


def fill_capacity_args(virtual_ws_item: VirtualWorkspaceItem, args: Namespace) -> None:
    cp_name = virtual_ws_item.short_name

    if hasattr(args, "subscription_id"):
        sub_id = args.subscription_id
    else:
        sub_id = state_config.get_config(fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID)

    if hasattr(args, "resource_group_name"):
        rg_name = args.resource_group_name
    else:
        rg_name = state_config.get_config(fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP)

    cp_id = _get_capacity_id(cp_name, sub_id, rg_name)

    if not cp_id:
        raise FabricCLIError(
            "Capacity not found or insufficient permissions. "
            + "Try to set the Azure subscription ID and resource group name "
            + "using 'config set default_az_subscription_id <subscription_id>' "
            + "and 'config set default_az_resource_group <rg_name>'",
            fab_constant.ERROR_NOT_FOUND,
        )

    args.subscription_id = cp_id.split("/")[2]
    args.resource_group_name = cp_id.split("/")[4]
    args.name = virtual_ws_item.name


def _find_capacity(virtual_ws_item: VirtualWorkspaceItem, capacities: list) -> dict:
    for capacity in capacities:
        if capacity["id"] == virtual_ws_item.id:
            return capacity
    raise FabricCLIError(
        f"Capacity {virtual_ws_item.name} not found",
        fab_constant.ERROR_NOT_FOUND,
    )


def check_fabric_capacity(virtual_ws_item: VirtualWorkspaceItem) -> None:
    _args = Namespace()
    fab_response = capacity_api.list_capacities(_args)
    if fab_response.status_code in {200, 201}:
        _capacities: list = json.loads(fab_response.text)["value"]
        _capacity = _find_capacity(virtual_ws_item, _capacities)
        if not re.match(r"F\d+", _capacity.get("sku", "Unknown")):
            raise FabricCLIError(
                f"Capacity {virtual_ws_item.name} is not a F SKU. Only Fabric capacities are supported",
                fab_constant.WARNING_NON_FABRIC_CAPACITY,
            )
    else:
        raise FabricCLIError(
            "Failed to list capacities",
            fab_constant.ERROR_NOT_FOUND,
        )
