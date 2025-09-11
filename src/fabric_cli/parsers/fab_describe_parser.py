# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys
from argparse import Namespace, _SubParsersAction
from typing import Any

from fabric_cli.core import fab_commands as cmd
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core import fab_logger
from fabric_cli.core.fab_decorators import set_command_context
from fabric_cli.core.fab_types import (
    FabricElementType,
    ItemType,
    VirtualItemType,
    VirtualWorkspaceItemType,
    WorkspaceType,
)
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, _BaseItem
from fabric_cli.core.hiearchy.fab_tenant import Tenant
from fabric_cli.core.hiearchy.fab_workspace import Workspace
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def register_parser(subparsers: _SubParsersAction) -> None:
    desc_examples = [
        "# check command support for .Capacity (using extension)",
        "$ desc .capacity\n",
        "# check command support for an existing capacity (using path)",
        "$ desc .capacities/capac1.Capacity\n",
        "# check command support for .Notebook (using extension)",
        "$ desc .notebook\n",
        "# check command support for an existing notebook (using path)",
        "$ desc /ws1.Workspace/nb1.Notebook",
    ]
    desc_learnmore = ["Tip: Use `desc all` to check all Dot elements"]

    describe_parser = subparsers.add_parser(
        "desc",
        help=fab_constant.COMMAND_DESCRIBE_DESCRIPTION,
        fab_examples=desc_examples,
        fab_learnmore=desc_learnmore,
    )
    describe_parser.add_argument(
        "path", nargs="*", type=str, default=None, help="Directory path"
    )
    describe_parser.usage = f"{utils_error_parser.get_usage_prog(describe_parser)}"
    describe_parser.set_defaults(func=_show_commands_supported)


# Utils
@set_command_context()
def _show_commands_supported(args: Namespace) -> None:
    try:
        context = handle_context.get_command_context(args.path)
        commands = cmd.get_all_supported_commands()
        available_commands = _get_available_commands(context, commands)
        _print_available_commands(f"{context.name}", available_commands)
    except Exception as e:
        element_or_path = utils.process_nargs(args.path)
        available_elements = _get_available_elements()

        if element_or_path.lower() in (item.lower() for item in available_elements):
            _print_supported_commands_by_element(element_or_path)
        else:
            fab_logger.log_warning(
                f'unknown Fabric element or valid path for "{args.command_path}"\n'
            )
            usage_format = f"{args.command_path} <fabric_dot_element> or <valid_path>"

            element_list = "\n  ".join(sorted(available_elements))
            custom_message = (
                f"Usage:  {usage_format}\n\n" f"Available elements:\n  {element_list}\n"
            )
            utils_ui.print(custom_message)
            sys.exit(2)


def _print_supported_commands_by_element(element_or_path: str) -> None:
    enum_class, sub_type = _get_enum_type_from_string_element(element_or_path)

    element_type = None
    base_element: FabricElement | None = None

    if enum_class == ItemType:
        element_type = FabricElementType.ITEM
    elif enum_class == VirtualItemType:
        element_type = FabricElementType.VIRTUAL_ITEM
    elif enum_class == VirtualWorkspaceItemType:
        element_type = FabricElementType.VIRTUAL_WORKSPACE_ITEM
    elif enum_class == WorkspaceType:
        element_type = FabricElementType.WORKSPACE

    if element_type in (
        FabricElementType.ITEM,
        FabricElementType.VIRTUAL_ITEM,
        FabricElementType.VIRTUAL_WORKSPACE_ITEM,
    ):
        base_element = _BaseItem(
            name="fab",
            id=None,
            element_type=element_type,
            parent=None,
            item_type=sub_type,
        )
    elif element_type == FabricElementType.WORKSPACE:
        base_element = Workspace(
            name="fab",
            id=None,
            parent=Tenant(name="fab", id=None),
            type=sub_type,
        )
    elif element_or_path.lower().endswith(".folder"):
        base_element = Folder(
            name="fab",
            id=None,
            parent=Workspace(
                name="fab",
                id=None,
                type=WorkspaceType.WORKSPACE.value,
                parent=Tenant(name="fab", id=None),
            ),
        )
        sub_type = "Folder"

    if base_element:
        commands = cmd.get_all_supported_commands()
        available_commands = _get_available_commands(base_element, commands)
        _print_available_commands(f".{sub_type}", available_commands)


def _get_enum_type_from_string_element(s: str) -> tuple:
    s_lower = s.lower()
    for enum_class in [
        ItemType,
        VirtualItemType,
        VirtualWorkspaceItemType,
        WorkspaceType,
    ]:
        for item in enum_class:
            if f".{item}".lower() == s_lower:
                return enum_class, item
    return None, None


def _print_available_commands(element_or_path: str, available_commands: list) -> None:
    command_list = "\n  ".join(sorted(available_commands))
    custom_message = (
        f"Commands for '{element_or_path}'. Type '<command> -h' for help.\n\n"
        f"Available commands:\n  {command_list}\n"
    )
    utils_ui.print(custom_message)


def _get_available_commands(context: FabricElement, commands: Any) -> list:
    available_commands = []
    for command in commands:
        try:
            if context.check_command_support(command):
                available_commands.append(f"{command.value}")
        except Exception:
            pass
    return available_commands


def _get_available_elements() -> list:
    available_elements = [".Folder"]
    for enum_class in [
        ItemType,
        VirtualItemType,
        VirtualWorkspaceItemType,
        WorkspaceType,
    ]:
        for item in enum_class:
            if item != WorkspaceType.PERSONAL:
                available_elements.append(f".{item}")
    return available_elements
