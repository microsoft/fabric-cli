# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the global parameters parser module."""

import argparse

import pytest

from fabric_cli.parsers import fab_global_params
from fabric_cli.core.fab_parser_setup import create_parser_and_subparsers


def test_add_global_flags():
    """Test adding global flags to a parser."""
    # Setup
    parser = argparse.ArgumentParser()

    # Execute
    fab_global_params.add_global_flags(parser)

    # Verify
    # Get all flags
    all_flags = [action for action in parser._actions if action.option_strings]

    # Check help flag
    help_flag = next(a for a in all_flags if "-help" in a.option_strings)
    assert help_flag.dest == "help"
    assert help_flag.option_strings == ["-help"]

    # Check output format flag
    format_flag = next(a for a in all_flags if "--output_format" in a.option_strings)
    assert format_flag.dest == "output_format"
    assert format_flag.option_strings == ["--output_format"]

    assert format_flag.choices == ["json", "text"]
    assert not format_flag.required
    assert "Override output format type" in format_flag.help

    skill_flag = next(a for a in all_flags if "--skill" in a.option_strings)
    assert skill_flag.dest == "skill"
    assert not skill_flag.required
    assert skill_flag.help == argparse.SUPPRESS


def test_add_global_flags_parser_integration():
    """Test that global flags work correctly in parser."""
    # Setup
    parser = argparse.ArgumentParser()
    fab_global_params.add_global_flags(parser)

    # Test help flag (should raise SystemExit)
    with pytest.raises(SystemExit):
        parser.parse_args(["-help"])

    # Test output format flag with valid choices
    args = parser.parse_args(["--output_format", "json"])
    assert args.output_format == "json"

    args = parser.parse_args(["--output_format", "text"])
    assert args.output_format == "text"

    args = parser.parse_args(["--skill", "semantic-model-authoring"])
    assert args.skill == "semantic-model-authoring"

    # Test invalid output format (should raise SystemExit)
    with pytest.raises(SystemExit):
        parser.parse_args(["--output_format", "invalid"])


@pytest.mark.parametrize(
    "command",
    [
        ["--skill", "semantic-model-authoring", "export", "ws.Workspace", "-o", "out"],
        ["export", "--skill", "semantic-model-authoring", "ws.Workspace", "-o", "out"],
        ["export", "ws.Workspace", "-o", "out", "--skill", "semantic-model-authoring"],
        ["--skill", "semantic-model-authoring", "job", "run", "list", "ws.Notebook"],
        ["job", "--skill", "semantic-model-authoring", "run", "list", "ws.Notebook"],
        ["job", "run", "list", "ws.Notebook", "--skill", "semantic-model-authoring"],
    ],
)
def test_skill_flag_preserved_across_command_tree(command):
    parser, _ = create_parser_and_subparsers()

    args = parser.parse_args(command)

    assert args.skill == "semantic-model-authoring"
