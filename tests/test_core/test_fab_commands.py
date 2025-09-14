# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core.fab_commands import (
    Command,
    _get_property_from_commands_and_subcommands,
    get_all_supported_commands,
    get_supported_elements,
    get_supported_items,
    get_unsupported_items,
)
from fabric_cli.core.fab_types import (
    FabricElementType,
    ItemType,
    VirtualItemType,
    VirtualWorkspaceItemType,
)


def test_get_command_path():
    # This test is to check if the function returns the correct path of the command
    args = type("", (), {})
    assert Command.get_command_path(args) == ""
    args = type("", (), {"command": "ls"})
    assert Command.get_command_path(args) == "ls"
    args = type("", (), {"command": "acl", "acl_subcommand": "get"})
    assert Command.get_command_path(args) == "acl get"
    args = type("", (), {"command": "config", "config_subcommand": "get"})
    assert Command.get_command_path(args) == "config get"
    args = type("", (), {"command": "label", "labels_command": "set"})
    assert Command.get_command_path(args) == "label set"
    args = type("", (), {"command": "table", "tables_command": "load"})
    assert Command.get_command_path(args) == "table load"
    args = type("", (), {"command": "job", "jobs_command": "run"})
    assert Command.get_command_path(args) == "job run"
    args = type("", (), {"command": "api"})
    assert Command.get_command_path(args) == "api"


def test_get_all_supported_commands():
    # This test is to check if the function returns the list of all members of the Command Enum except CLEAR and API and CONFIG
    expected_output = list(Command)
    expected_output.remove(Command.CLEAR)
    expected_output.remove(Command.API)
    expected_output.remove(Command.CONFIG_CLEAR_CACHE)
    expected_output.remove(Command.CONFIG_GET)
    expected_output.remove(Command.CONFIG_LS)
    expected_output.remove(Command.CONFIG_SET)
    assert get_all_supported_commands() == expected_output


def test_get_property_from_commands_and_subcommands(monkeypatch):

    def mock_get_command_support_dict():
        return {
            "commands": {
                "fs": {
                    "supported_elements": ["workspace"],
                    "subcommands": {
                        "ls": {"supported_elements": ["item", "virtual_item"]}
                    },
                }
            }
        }

    monkeypatch.setattr(
        "fabric_cli.core.fab_commands.get_command_support_dict", 
        mock_get_command_support_dict
    )

    assert _get_property_from_commands_and_subcommands(
        Command.FS_LS, "supported_elements"
    ) == ["workspace", "item", "virtual_item"]


def test_get_element_support(monkeypatch):
    # This test is to check if the function returns the correct list of supported elements for a command
    def mock_get_property_from_commands_and_subcommands(command, map_key):
        return ["workspace", "item", "virtual_item", "invalid_element"]

    monkeypatch.setattr(
        "fabric_cli.core.fab_commands._get_property_from_commands_and_subcommands",
        mock_get_property_from_commands_and_subcommands,
    )

    expected_output = [
        FabricElementType.WORKSPACE,
        FabricElementType.ITEM,
        FabricElementType.VIRTUAL_ITEM,
    ]

    assert get_supported_elements(Command.FS_LS) == expected_output


def test_get_item_support(monkeypatch):

    def mock_get_property_from_commands_and_subcommands(command, map_key):
        return [
            "notebook",
            "mirrored_database",
            "spark_pool",
            "invalid_item",
            "capacity",
        ]

    monkeypatch.setattr(
        "fabric_cli.core.fab_commands._get_property_from_commands_and_subcommands",
        mock_get_property_from_commands_and_subcommands,
    )

    expected_output = [
        ItemType.NOTEBOOK,
        ItemType.MIRRORED_DATABASE,
        VirtualItemType.SPARK_POOL,
        VirtualWorkspaceItemType.CAPACITY,
    ]

    assert get_supported_items(Command.FS_LS) == expected_output

    assert get_unsupported_items(Command.FS_LS) == expected_output
