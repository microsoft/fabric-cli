# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import fabric_cli.utils.fab_commands as commands


def test_commands_structure():
    """Test that COMMANDS dictionary has expected structure."""
    assert isinstance(commands.COMMANDS, dict)

    # Test main categories exist
    expected_categories = [
        "Core Commands",
        "Resource Commands",
        "Util Commands",
        "Flags",
    ]
    for category in expected_categories:
        assert category in commands.COMMANDS
        assert isinstance(commands.COMMANDS[category], dict)
