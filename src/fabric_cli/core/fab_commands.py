# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import platform
from enum import Enum

import yaml
from yaml import Loader

from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    FabricElementType,
    ItemType,
    VirtualItemType,
    VirtualWorkspaceItemType,
    _BaseItemType,
)


class Command(Enum):

    CLEAR = "clear" if platform.system() != "Windows" else "cls"

    FS_LS = "ls" if platform.system() != "Windows" else "dir"
    FS_RM = "rm" if platform.system() != "Windows" else "del"
    FS_MV = "mv" if platform.system() != "Windows" else "move"
    FS_CP = "cp" if platform.system() != "Windows" else "copy"
    FS_LN = "ln" if platform.system() != "Windows" else "mklink"
    FS_CD = "cd"
    FS_EXISTS = "exists"
    FS_EXPORT = "export"
    FS_IMPORT = "import"
    FS_GET = "get"
    FS_SET = "set"
    FS_OPEN = "open"
    FS_MKDIR = "mkdir"
    FS_START = "start"
    FS_STOP = "stop"
    FS_ASSIGN = "assign"
    FS_UNASSIGN = "unassign"

    # ACL commands
    ACL_LS = "acl " + FS_LS
    ACL_RM = "acl " + FS_RM
    ACL_GET = "acl " + FS_GET
    ACL_SET = "acl " + FS_SET

    # API commands
    API = "api"

    # JOB commands
    JOB_START = "job start"
    JOB_RUN = "job run"
    JOB_RUN_CANCEL = "job run-cancel"
    JOB_RUN_LIST = "job run-list"
    JOB_RUN_UPDATE = "job run-update"
    JOB_RUN_RM = "job run-rm"
    JOB_RUN_SCH = "job run-sch"
    JOB_RUN_STATUS = "job run-status"

    # CONFIG commands
    CONFIG_CLEAR_CACHE = "config clear-cache"
    CONFIG_GET = "config " + FS_GET
    CONFIG_LS = "config " + FS_LS
    CONFIG_SET = "config " + FS_SET

    # LABEL commands
    LABEL_SET = "label " + FS_SET
    LABEL_RM = "label " + FS_RM

    # TABLE commands
    TABLE_LOAD = "table load"
    TABLE_OPTIMIZE = "table optimize"
    TABLE_SCHEMA = "table schema"
    TABLE_VACUUM = "table vacuum"

    @staticmethod
    def get_command_path(args):
        """
        Sets the args.command_path to be the path of the command and subcommands excluding any arguments.
        This method constructs a CLI command string based on the provided arguments. It identifies the command group
        and appends the appropriate subcommand to form the complete command path.
        Args:
            args (list): A list of arguments that contains the command and subcommand attributes.
        Returns:
            str: The constructed CLI command string.
        Example:
            If args.command is "config" and args.config_subcommand is "set", the method will return "config set".
            If args.command is "create", the method will return "create".
        """

        if not hasattr(args, "command"):
            return ""

        command_group = args.command
        cli_command_string = command_group

        if command_group == "acl":
            return cli_command_string + " " + (args.acl_subcommand or "")
        elif command_group == "config":
            return cli_command_string + " " + (args.config_subcommand or "")
        elif command_group == "label":
            return cli_command_string + " " + (args.labels_command or "")
        elif command_group == "table":
            return cli_command_string + " " + (args.tables_command or "")
        elif command_group == "job":
            return cli_command_string + " " + (args.jobs_command or "")
        elif command_group == "api" or command_group == "desc":
            return cli_command_string

        return cli_command_string


def _snake_to_camel(snake_str):
    return snake_str.title().replace("_", "")


mem_dictionary = None


def get_command_support_dict():
    global mem_dictionary
    if mem_dictionary is None:
        default_yaml_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fab_config",
            "command_support.yaml",
        )
        yaml_file = default_yaml_file

        stream = open(yaml_file, "r")
        dictionary = yaml.load(stream, Loader=Loader)
        mem_dictionary = dictionary

    return mem_dictionary


def get_all_supported_commands() -> list[Command]:
    command_support_dict = get_command_support_dict()
    commands = command_support_dict["commands"].keys()
    # return a list of Command Enum objects for supported commands
    return [c for c in Command if c.name.split("_")[0].lower() in commands]


def _get_property_from_commands_and_subcommands(
    command: Command, property: str
) -> list[str]:
    _support_dict = get_command_support_dict()
    _command_group = command.name.split("_")[0].lower()
    _sub_command = "_".join(command.name.split("_")[1:]).lower()

    # Get the supported items for the command group
    _command_group_dict = _support_dict["commands"].get(_command_group, {})
    _command_group_dict = {} if _command_group_dict is None else _command_group_dict
    _command_group_elements = _command_group_dict.get(property, [])
    _command_group_elements = (
        [] if _command_group_elements is None else _command_group_elements
    )

    # Get the supported items for the sub_command
    _sub_command_dict = _command_group_dict.get("subcommands", {}).get(_sub_command, {})
    _sub_command_dict = {} if _sub_command_dict is None else _sub_command_dict

    return _command_group_elements + _sub_command_dict.get(property, [])


def get_supported_elements(command: Command) -> list[FabricElementType]:
    _map_key = "supported_elements"
    elements: list[str] = _get_property_from_commands_and_subcommands(command, _map_key)
    # Convert elements to FabricElementType Enum objects
    elements_camel = [_snake_to_camel(e) for e in elements]
    elements_typed = []
    for e in elements_camel:
        try:
            elements_typed.append(FabricElementType.from_string(e))
        except FabricCLIError:
            continue
    return elements_typed


def _get_items(command: Command, key: str) -> list[_BaseItemType]:
    items: list[str] = _get_property_from_commands_and_subcommands(command, key)
    items_camel = [_snake_to_camel(e) for e in items]
    item_typed = []
    for i in items_camel:
        for item_type in (ItemType, VirtualItemType, VirtualWorkspaceItemType):
            try:
                item_typed.append(item_type.from_string(i))
                break
            except FabricCLIError:
                continue
    return item_typed


def get_supported_items(command: Command) -> list[_BaseItemType]:
    return _get_items(command, "supported_items")


def get_unsupported_items(command: Command) -> list[_BaseItemType]:
    return _get_items(command, "unsupported_items")
