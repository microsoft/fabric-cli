# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the global parameters parser module."""

import argparse
import json
from unittest.mock import patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_parser_setup import (
    CustomArgumentParser,
    create_parser_and_subparsers,
)
from fabric_cli.parsers import fab_global_params
from fabric_cli.utils import fab_ui


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

    json_flag = next(a for a in all_flags if "--json" in a.option_strings)
    assert json_flag.dest == "output_format"
    assert json_flag.const == "json"
    assert json_flag.nargs == 0
    assert "--output_format json" in json_flag.help


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

    # Test invalid output format (should raise SystemExit)
    with pytest.raises(SystemExit):
        parser.parse_args(["--output_format", "invalid"])


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ([], None),
        (["--json"], "json"),
        (["--json", "--json"], "json"),
        (["--output_format", "text", "--json"], "json"),
        (["--json", "--output_format", "text"], "text"),
        (["--json", "--output_format", "json"], "json"),
    ],
)
def test_output_format_option_precedence(
    flags: list[str], expected: str | None
) -> None:
    """Use the last format option and preserve the default when none is given."""
    parser = argparse.ArgumentParser()
    fab_global_params.add_global_flags(parser)

    args = parser.parse_args(flags)

    assert args.output_format == expected
    assert not hasattr(args, "json")


@pytest.mark.parametrize(
    "command",
    [
        ["ls"],
        ["dir"],
        ["ls", "/ws.Workspace/Folder.Folder"],
        ["ls", ".capacities"],
        ["auth", "status"],
        ["config", "get", "output_format"],
        ["job", "run-list", "ws.Workspace/item.Notebook"],
    ],
)
@pytest.mark.parametrize(
    "mode",
    [fab_constant.FAB_MODE_COMMANDLINE, fab_constant.FAB_MODE_INTERACTIVE],
)
def test_json_matches_output_format_across_commands(
    command: list[str], mode: str
) -> None:
    """The shorthand produces the same command arguments in both CLI modes."""
    parser, _ = create_parser_and_subparsers()
    parser.set_mode(mode)

    shorthand = parser.parse_args([*command, "--json"])
    explicit = parser.parse_args([*command, "--output_format", "json"])

    assert shorthand.output_format == "json"
    assert vars(shorthand) == vars(explicit)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], None),
        (["ls"], None),
        (["auth", "status"], None),
        (["--json", "ls"], "json"),
        (["auth", "--json", "status"], "json"),
        (["--json", "auth", "status"], "json"),
        (["--output_format", "json", "ls"], "json"),
        (["--output_format", "text", "auth", "status"], "text"),
        (["auth", "--output_format", "json", "status"], "json"),
        (["--json", "ls", "--output_format", "text"], "text"),
        (["--output_format", "text", "ls", "--json"], "json"),
        (["--json", "auth", "--output_format", "text", "status"], "text"),
        (["--output_format", "text", "auth", "--json", "status"], "json"),
        (["--json", "auth", "status", "--output_format", "text"], "text"),
        (["--output_format", "text", "auth", "status", "--json"], "json"),
        (["auth", "--json", "status", "--output_format", "text"], "text"),
        (["auth", "--output_format", "text", "status", "--json"], "json"),
        (
            ["--output_format", "json", "auth", "--output_format", "text", "status"],
            "text",
        ),
        (
            ["--output_format", "text", "auth", "status", "--output_format", "json"],
            "json",
        ),
        (
            [
                "--json",
                "auth",
                "--output_format",
                "text",
                "status",
                "--json",
            ],
            "json",
        ),
    ],
)
@pytest.mark.parametrize(
    "mode",
    [fab_constant.FAB_MODE_COMMANDLINE, fab_constant.FAB_MODE_INTERACTIVE],
)
def test_output_format_preserved_across_subparsers(
    arguments: list[str], expected: str | None, mode: str
) -> None:
    """Only explicit options override earlier format selections."""
    parser, _ = create_parser_and_subparsers()
    parser.set_mode(mode)

    args = parser.parse_args(arguments)

    assert args.output_format == expected
    assert not hasattr(args, "json")


def test_custom_parser_output_format_defaults() -> None:
    """Public parsing supplies a fallback without changing recursive defaults."""
    parser = CustomArgumentParser()
    child = parser.add_subparsers().add_parser("child")
    nested = child.add_subparsers().add_parser("nested")

    assert parser.parse_args([]).output_format is None
    assert parser.parse_args(["child", "nested"]).output_format is None
    assert child.parse_args([]).output_format is None
    assert child.parse_args(["nested"]).output_format is None
    assert nested.parse_args([]).output_format is None
    for subparser in (child, nested):
        args, remaining = subparser.parse_known_args([])
        assert not hasattr(args, "output_format")
        assert remaining == []
    args, remaining = parser.parse_known_args(
        ["--json", "child", "nested", "--unknown"]
    )
    assert args.output_format == "json"
    assert remaining == ["--unknown"]
    args, remaining = parser.parse_known_args(["child", "nested"])
    assert args.output_format is None
    assert remaining == []


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ([], "text"),
        (["--json"], "json"),
        (["--output_format", "json"], "json"),
    ],
)
def test_child_parser_preserves_namespace_output_format(
    flags: list[str], expected: str
) -> None:
    """Public parsing preserves supplied namespaces and explicit format flags."""
    parser = CustomArgumentParser()
    child = parser.add_subparsers().add_parser("child")
    namespace = argparse.Namespace(output_format="text")

    args = child.parse_args(flags, namespace)

    assert args is namespace
    assert args.output_format == expected


def test_json_flag_rejects_value() -> None:
    """The shorthand is a switch, not an option requiring a value."""
    parser = argparse.ArgumentParser()
    fab_global_params.add_global_flags(parser)

    with pytest.raises(SystemExit):
        parser.parse_args(["--json", "text"])


def test_json_flag_is_documented_in_help() -> None:
    """Command help describes the JSON shorthand."""
    parser, subparsers = create_parser_and_subparsers()

    assert "--json" in parser.format_help()
    assert "--json" in subparsers.choices["ls"].format_help()


@pytest.mark.parametrize("flags", [["--json"], ["--output_format", "json"]])
@pytest.mark.parametrize(
    ("before", "after"),
    [
        ([], ["ls"]),
        (["ls"], []),
        ([], ["auth", "status"]),
        (["auth"], ["status"]),
        (["auth", "status"], []),
    ],
)
def test_json_output_overrides_configured_text(
    flags: list[str],
    before: list[str],
    after: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both forms render structured JSON through the existing output helper."""
    parser, _ = create_parser_and_subparsers()
    args = parser.parse_args([*before, *flags, *after])
    data = [{"name": "ws.Workspace"}]

    with patch(
        "fabric_cli.utils.fab_ui.fab_state_config.get_config", return_value="text"
    ):
        fab_ui.print_output_format(args, data=data, hidden_data=[".capacities"])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == "Success"
    assert output["command"] == args.command
    assert output["result"] == {"data": data, "hidden_data": [".capacities"]}
    assert captured.err == ""
