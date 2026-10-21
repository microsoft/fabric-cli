# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for structured help and compatibility with text help."""

import argparse
import json
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import ANY, patch

import pytest

from fabric_cli import __version__
from fabric_cli.core.fab_help import build_help_data
from fabric_cli.core.fab_parser_setup import (
    CustomArgumentParser,
    create_parser_and_subparsers,
)


@pytest.fixture
def parser(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> CustomArgumentParser:
    """Build the complete parser tree with isolated configuration."""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_file", str(tmp_path / "config.json")
    )
    with patch("sys.argv", ["fab"]):
        return create_parser_and_subparsers()[0]


def _json_help(
    parser: CustomArgumentParser,
    arguments: list[str],
    capsys: pytest.CaptureFixture[str],
) -> dict[str, Any]:
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(arguments)
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    output = json.loads(captured.out)
    assert set(output) == {"timestamp", "status", "command", "result"}
    timestamp = datetime.fromisoformat(output["timestamp"].replace("Z", "+00:00"))
    assert timestamp.utcoffset() == timedelta(0)
    assert output["status"] == "Success"
    assert set(output["result"]) == {"data"}
    assert len(output["result"]["data"]) == 1
    return output


@pytest.mark.parametrize("help_flag", ["--help", "-h", "-help"])
@pytest.mark.parametrize(
    "arguments",
    [
        ["mkdir", "{help}", "--output_format", "json"],
        ["mkdir", "--output_format", "json", "{help}"],
        ["--output_format", "json", "mkdir", "{help}"],
        ["mkdir", "{help}", "--output_format=json"],
        ["mkdir", "--output_format=json", "{help}"],
    ],
)
def test_mkdir_json_help_flag_order(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    help_flag: str,
    arguments: list[str],
) -> None:
    output = _json_help(
        parser, [arg.replace("{help}", help_flag) for arg in arguments], capsys
    )
    assert output["command"] == "mkdir"
    data = output["result"]["data"][0]
    assert data["schema_version"] == "1.0"
    assert data["cli_version"] == __version__
    assert data["description"] == "Create a workspace, item, or directory."
    assert data["usage"] == "fab mkdir <path> [flags]"
    assert data["aliases"] == ["create"]
    assert data["subcommands"] == []
    assert data["args"][0]["name"] == "path"
    assert data["args"][0]["required"] is True
    flags = {flag["name"]: flag for flag in data["flags"]}
    assert set(flags) == {"--help", "--output_format", "--params"}
    assert flags["--help"]["aliases"] == ["-h", "-help"]
    assert flags["--help"]["type"] == "boolean"
    assert flags["--output_format"]["choices"] == ["json", "text"]
    assert flags["--params"]["value_optional"] is True
    assert flags["--params"]["repeat_behavior"] == "replace"
    assert data["examples"][0] == {
        "description": "create an empty notebook",
        "command": "fab mkdir ws1.Workspace/nb1.Notebook",
    }
    assert data["notes"]
    assert data["learn_more"] == ["https://aka.ms/fabric-cli"]


@pytest.mark.parametrize(
    "arguments, command",
    [
        (["--help"], "fab"),
        (["job", "--help"], "job"),
        (["job", "run", "--help"], "job run"),
        (["job", "--output_format", "json", "run", "--help"], "job run"),
        (["auth", "login", "--help"], "auth login"),
        (["acl", "dir", "--help"], "acl ls"),
        (["create", "--help"], "mkdir"),
        (["cls", "--help"], "clear"),
    ],
)
def test_json_help_command_paths(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    command: str,
) -> None:
    output = _json_help(parser, arguments + ["--output_format", "json"], capsys)
    assert output["command"] == command
    assert output["result"]["data"][0]["usage"].startswith(
        "fab" if command == "fab" else f"fab {command}"
    )


def test_json_help_uses_saved_configuration(
    parser: CustomArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    from fabric_cli.core import fab_state_config

    fab_state_config.set_config("output_format", "json")
    output = _json_help(parser, ["job", "run", "--help"], capsys)
    assert output["command"] == "job run"


@pytest.mark.parametrize(
    "arguments",
    [
        ["mkdir", "--help", "--output_format", "text"],
        ["--output_format=text", "mkdir", "--help"],
    ],
)
def test_text_help_overrides_saved_json(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    from fabric_cli.core import fab_state_config

    fab_state_config.set_config("output_format", "json")
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(arguments)
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert output.startswith("Usage: mkdir <path>")
    assert "Examples:" in output
    assert "Aliases:" in output


def test_json_help_does_not_leak_format_between_calls(
    parser: CustomArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    _json_help(parser, ["mkdir", "--help", "--output_format=json"], capsys)
    with pytest.raises(SystemExit):
        parser.parse_args(["mkdir", "--help"])
    assert capsys.readouterr().out.startswith("Usage: mkdir")


def test_text_leaf_help_is_unchanged(
    parser: CustomArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Text help continues to use the existing formatter."""
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    expected = subparsers.choices["mkdir"].format_help()
    with pytest.raises(SystemExit):
        parser.parse_args(["mkdir", "--help", "--output_format=text"])
    assert capsys.readouterr().out == expected


def test_parser_delegates_help_to_ui(parser: CustomArgumentParser) -> None:
    """The parser delegates rendering without selecting an output format."""
    stream = StringIO()
    with patch("fabric_cli.utils.fab_ui.print_help") as print_help:
        parser.print_help(file=stream)
    print_help.assert_called_once_with(parser, text_help=ANY)


def test_text_help_preserves_requested_stream(parser: CustomArgumentParser) -> None:
    """The UI's text callback preserves argparse's destination stream."""
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    leaf = subparsers.choices["mkdir"]
    stream = StringIO()
    leaf.print_help(file=stream)
    assert stream.getvalue() == leaf.format_help()


def test_direct_subparser_json_help(
    parser: CustomArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Interactive and -c parsing can request help without parsing the root."""
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    output = _json_help(
        subparsers.choices["job"],
        ["run", "--help", "--output_format=json"],
        capsys,
    )
    assert output["command"] == "job run"


def test_main_json_help_does_not_execute_commands(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI entry point exits successfully before command execution."""
    from fabric_cli import main

    monkeypatch.setattr(
        main, "get_global_parser_and_subparsers", lambda: (parser, None)
    )
    monkeypatch.setattr(
        "sys.argv", ["fab", "job", "run", "--help", "--output_format=json"]
    )
    with patch.object(main, "_execute_command") as execute:
        with patch("fabric_cli.core.fab_state_config.init_defaults") as initialize:
            with pytest.raises(SystemExit) as exc:
                main.main()
    assert exc.value.code == 0
    execute.assert_not_called()
    initialize.assert_not_called()
    assert json.loads(capsys.readouterr().out)["command"] == "job run"


@pytest.mark.parametrize(
    "command", ["fab", "job", "auth", "acl", "config", "table", "label"]
)
def test_text_group_help_is_preserved(
    parser: CustomArgumentParser, command: str
) -> None:
    arguments = [] if command == "fab" else [command]
    with patch("fabric_cli.utils.fab_ui.display_help") as display_help:
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(arguments + ["--help"])
    assert exc.value.code == 0
    display_help.assert_called_once()


def test_all_registered_commands_have_complete_help(
    parser: CustomArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    def check(current: argparse.ArgumentParser, path: list[str]) -> None:
        output = _json_help(parser, path + ["--help", "--output_format=json"], capsys)
        data = output["result"]["data"][0]
        assert set(data) == {
            "schema_version",
            "cli_version",
            "description",
            "usage",
            "args",
            "flags",
            "aliases",
            "subcommands",
            "examples",
            "notes",
            "learn_more",
        }
        assert data["schema_version"] == "1.0"
        assert data["description"].strip()
        for section in ("args", "flags"):
            for item in data[section]:
                assert item["name"]
                assert item["description"].strip()
                assert isinstance(item["required"], bool)
        for action in current._actions:
            if isinstance(action, argparse._SubParsersAction):
                seen = set()
                for name, child in action.choices.items():
                    if child not in seen:
                        seen.add(child)
                        check(child, path + [name])

    check(parser, [])


def test_help_metadata_preserves_parser_semantics() -> None:
    parser = CustomArgumentParser(prog="fab example")
    parser.add_argument("optional", nargs="?")
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--ratio", type=float)
    parser.add_argument("--entry", action="append")
    parser.add_argument("--hidden", help=argparse.SUPPRESS)
    data = build_help_data(parser)
    assert data["args"][0]["required"] is False
    assert data["args"][0]["description"]
    flags = {flag["name"]: flag for flag in data["flags"]}
    assert flags["--count"]["required"] is True
    assert flags["--count"]["type"] == "integer"
    assert flags["--ratio"]["type"] == "number"
    assert flags["--entry"]["repeat_behavior"] == "append"
    assert "--hidden" not in flags


def test_help_types_and_subcommand_aliases(parser: CustomArgumentParser) -> None:
    root = build_help_data(parser)
    commands = {command["name"]: command for command in root["subcommands"]}
    assert commands["mkdir"]["aliases"] == ["create"]
    assert commands["clear"]["aliases"] == ["cls"]
    assert "create" not in commands
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            job = action.choices["job"]
            for child_action in job._actions:
                if isinstance(child_action, argparse._SubParsersAction):
                    data = build_help_data(child_action.choices["run"])
                    flags = {flag["name"]: flag for flag in data["flags"]}
                    assert flags["--timeout"]["type"] == "integer"
                    assert flags["--polling_interval"]["type"] == "integer"
