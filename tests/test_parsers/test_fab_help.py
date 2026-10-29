# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Parser-derived help metadata and help-control boundary tests."""

import argparse
import json
from typing import Any, Iterator

import pytest

from fabric_cli import __version__
from fabric_cli.core.fab_help import (
    build_help_data,
    canonical_command,
    child_parsers,
    resolve_help,
)
from fabric_cli.core.fab_parser_setup import (
    CustomArgumentParser,
    create_parser_and_subparsers,
)


def _nodes(
    parser: argparse.ArgumentParser,
) -> Iterator[argparse.ArgumentParser]:
    yield parser
    for _, child, _, _ in child_parsers(parser):
        yield from _nodes(child)


@pytest.fixture
def parser() -> CustomArgumentParser:
    return create_parser_and_subparsers()[0]


@pytest.mark.parametrize(
    ("prog", "expected"),
    [
        ("fab", "fab"),
        ("fab job", "job"),
        ("job", "job"),
        ("fab job run", "job run"),
        ("job run", "job run"),
    ],
)
def test_canonical_command_prefix_success(prog: str, expected: str) -> None:
    assert canonical_command(argparse.ArgumentParser(prog=prog)) == expected


def test_all_public_nodes_match_contract_success(parser: CustomArgumentParser) -> None:
    for node in _nodes(parser):
        data = build_help_data(node)
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
        assert data["cli_version"] == __version__
        assert data["schema_version"] == "1.0"
        assert len(data["examples"]) == sum(
            1
            for example in getattr(node, "fab_examples", [])
            if example.strip() and not example.strip().startswith("#")
        )
        assert "--skill" not in [flag["name"] for flag in data["flags"]]
        assert len(data["flags"]) == len({flag["name"] for flag in data["flags"]})
        for flag in data["flags"]:
            if flag["required"]:
                assert flag["name"] in data["usage"].removesuffix(" [flags]").split()
        expected = [
            action.dest
            for action in node._actions
            if not action.option_strings
            and not isinstance(action, argparse._SubParsersAction)
            and action.help != argparse.SUPPRESS
        ]
        assert [entry["name"] for entry in data["args"]] == expected
        spellings = {
            spelling
            for flag in data["flags"]
            for spelling in [flag["name"], *flag["aliases"]]
        }
        assert spellings == {
            spelling
            for action in node._actions
            if action.help != argparse.SUPPRESS
            for spelling in action.option_strings
        }


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (
            "fab",
            {
                "description": "Work seamlessly with Fabric from the command line.",
                "usage": "fab <command> [flags]",
                "args": [],
                "aliases": [],
            },
        ),
        (
            "job",
            {
                "description": "Manage and schedule jobs.",
                "usage": "fab job <command> [flags]",
                "args": [],
                "aliases": [],
            },
        ),
        (
            "mkdir",
            {
                "description": "Create a workspace, item, or directory.",
                "usage": "fab mkdir <path> [flags]",
                "args": [
                    {
                        "name": "path",
                        "type": "string",
                        "required": True,
                        "description": "Directory path",
                    },
                ],
                "aliases": ["create"],
                "examples": [
                    {
                        "description": "create an empty notebook",
                        "command": "fab mkdir ws1.Workspace/nb1.Notebook",
                    },
                    {
                        "description": "create a directory (Lakehouse only)",
                        "command": "fab mkdir ws1.Workspace/lh1.Lakehouse/Files/fabdir",
                    },
                ],
            },
        ),
        (
            "job run",
            {
                "description": "Run an item",
                "usage": "fab job run <path> [flags]",
                "args": [
                    {
                        "name": "path",
                        "type": "string",
                        "required": True,
                        "description": "Path to the item",
                    },
                ],
                "aliases": [],
            },
        ),
    ],
)
def test_representative_help_values_success(
    parser: CustomArgumentParser, command: str, expected: dict[str, Any]
) -> None:
    node = next(node for node in _nodes(parser) if canonical_command(node) == command)
    data = build_help_data(node)
    assert {field: data[field] for field in expected} == expected


@pytest.mark.parametrize(
    ("tokens", "expected"),
    [
        (["deploy"], "fab deploy --config <config> [flags]"),
        (
            ["export"],
            "fab export <path> --output <output> [<output> ...] [flags]",
        ),
        (
            ["import"],
            "fab import <path> --input <input> [<input> ...] [flags]",
        ),
        (
            ["table", "load"],
            "fab table load <path> --file <file> [<file> ...] [flags]",
        ),
        (
            ["set"],
            "fab set <path> --query <query> --input <input> [<input> ...] [flags]",
        ),
    ],
)
def test_required_flags_json_usage_success(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    tokens: list[str],
    expected: str,
) -> None:
    node = next(
        node for node in _nodes(parser) if canonical_command(node) == " ".join(tokens)
    )
    text_help = node.format_help()
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args([*tokens, "--help", "--output_format=json"])
    assert exit_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["result"]["data"][0]["usage"] == expected
    assert node.format_help() == text_help


@pytest.mark.parametrize(
    ("nargs", "expected"),
    [
        (None, "--value <value>"),
        ("?", "--value [<value>]"),
        ("*", "--value [<value> ...]"),
        ("+", "--value <value> [<value> ...]"),
        (2, "--value <value> <value>"),
    ],
)
def test_required_flag_value_arity_usage_success(
    nargs: str | int | None, expected: str
) -> None:
    parser = CustomArgumentParser(prog="fab example")
    parser.add_argument("--value", required=True, nargs=nargs)
    parser.add_argument("--optional")
    assert build_help_data(parser)["usage"] == f"fab example {expected} [flags]"


def test_required_boolean_flag_usage_success() -> None:
    parser = CustomArgumentParser(prog="fab example")
    parser.add_argument("-f", "--force", required=True, action="store_true")
    assert build_help_data(parser)["usage"] == "fab example --force [flags]"


def test_metadata_semantics_success(parser: CustomArgumentParser) -> None:
    nodes = {canonical_command(node): build_help_data(node) for node in _nodes(parser)}
    root = nodes["fab"]
    children = {entry["name"]: entry for entry in root["subcommands"]}
    assert "deploy" in children
    assert children["mkdir"]["aliases"] == ["create"]
    assert "create" not in children
    flags = {flag["name"]: flag for flag in root["flags"]}
    assert flags["--command"]["repeat_behavior"] == "append"
    for name, data in nodes.items():
        if name != "fab":
            assert "--command" not in {flag["name"] for flag in data["flags"]}
    mkdir = nodes["mkdir"]
    assert mkdir["usage"] == "fab mkdir <path> [flags]"
    assert mkdir["args"][0]["required"] is True
    flags = {flag["name"]: flag for flag in mkdir["flags"]}
    assert flags["--help"]["aliases"] == ["-h", "-help"]
    assert flags["--params"]["value_optional"] is True
    assert "default" not in flags["--params"]
    assert "default" not in flags["--output_format"]
    assert all(link.startswith("https://") for link in mkdir["learn_more"])
    assert "target-specific" in " ".join(mkdir["notes"])
    flags = {flag["name"]: flag for flag in nodes["job run"]["flags"]}
    assert flags["--polling_interval"]["type"] == "integer"
    assert flags["--polling_interval"]["minimum"] == 1
    assert flags["--timeout"]["type"] == "integer"
    assert flags["--params"]["repeat_behavior"] == "replace"
    assert flags["--input"]["repeat_behavior"] == "replace"
    assert "--input cannot be combined" in " ".join(nodes["job run"]["notes"])
    flags = {flag["name"]: flag for flag in nodes["import"]["flags"]}
    assert flags["--input"]["required"] is True
    assert "placeholder" in " ".join(nodes["extension"]["notes"])


def test_every_command_alias_resolves_success(parser: CustomArgumentParser) -> None:
    def check(parent: argparse.ArgumentParser, prefix: list[str]) -> None:
        for name, child, aliases, _ in child_parsers(parent):
            assert build_help_data(child)["aliases"] == aliases
            for spelling in [name, *aliases]:
                request = resolve_help(
                    parser, [*prefix, spelling, "--help", "--output_format=json"]
                )
                assert request is not None
                assert request.parser is child
                assert request.error is None
            check(child, [*prefix, name])

    check(parser, [])


@pytest.mark.parametrize(
    ("tokens", "command", "aliases"),
    [
        (["clear"], "clear", ["cls"]),
        (["cls"], "clear", ["cls"]),
        (["config", "ls"], "config ls", ["dir"]),
        (["config", "dir"], "config ls", ["dir"]),
    ],
)
def test_registered_leaf_aliases_json_help_success(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    tokens: list[str],
    command: str,
    aliases: list[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args([*tokens, "--help", "--output_format=json"])
    assert exit_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["command"] == command
    assert output["result"]["data"][0]["aliases"] == aliases


@pytest.mark.parametrize(
    ("tokens", "command"),
    [
        (["--help", "--output_format", "json"], "fab"),
        (["job", "--output_format=json", "-h"], "job"),
        (["--output_format", "json", "job", "run", "-help"], "job run"),
        (["create", "--help", "--output_format=json"], "mkdir"),
        (["import", "--help"], "import"),
        (["job", "run", "--timeout", "not-an-int", "--help"], "job run"),
        (["mkdir", "-P", "--help"], "mkdir"),
    ],
)
def test_resolve_help_success(
    parser: CustomArgumentParser, tokens: list[str], command: str
) -> None:
    request = resolve_help(parser, tokens)
    assert request is not None
    assert canonical_command(request.parser) == command
    assert request.error is None


@pytest.mark.parametrize(
    "tokens",
    [
        ["ls", "-la", "--help", "--output_format=json"],
        ["ls", "--out=json", "--help"],
        ["ls", "-lh", "--output_format=json"],
        ["ls", "-alh", "--out", "json"],
        ["ls", "-lqname", "--help", "--out=json"],
        ["ls", "-lq--help", "--he", "--out=json"],
        ["ls", "-la", "--out", "json", "--he"],
    ],
)
def test_argparse_option_spellings_json_help_success(
    parser: CustomArgumentParser,
    capsys: pytest.CaptureFixture[str],
    tokens: list[str],
) -> None:
    request = resolve_help(parser, tokens)
    assert request is not None
    assert request.error is None
    assert request.selectors == ["json"]
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(tokens)
    assert exit_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["command"] == "ls"
    assert output["status"] == "Success"


@pytest.mark.parametrize(
    "tokens",
    [
        ["ls", "-q--help"],
        ["ls", "-lq--help"],
        ["ls", "--que=--help"],
        ["--comm=job --help"],
        ["ls", "--", "-lh"],
    ],
)
def test_argparse_option_value_boundaries_success(
    parser: CustomArgumentParser, tokens: list[str]
) -> None:
    assert resolve_help(parser, tokens) is None


def test_ambiguous_option_abbreviation_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = CustomArgumentParser(prog="fab example")
    parser.add_argument("--other")
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(["--o=json", "--help", "--output_format=json"])
    assert exit_info.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "Failure"


def test_disabled_option_abbreviation_failure() -> None:
    parser = CustomArgumentParser(prog="fab example", allow_abbrev=False)
    request = resolve_help(parser, ["--out=json", "--help"])
    assert request is not None
    assert request.error is not None


@pytest.mark.parametrize("token", ["-lx", "-la=yes", "-lhx"])
def test_invalid_combined_options_failure(
    parser: CustomArgumentParser, token: str
) -> None:
    request = resolve_help(parser, ["ls", token, "--help", "--output_format=json"])
    assert request is not None
    assert request.error is not None


@pytest.mark.parametrize(
    "tokens",
    [
        ["api", "--input", '{"value": "--help"}'],
        ["api", "--input=--help"],
        ["-c", "mkdir --help"],
        ["-c", "--help"],
        ["-cmkdir --help"],
        ["mkdir", "--", "--help"],
        ["find", "text containing --help"],
    ],
)
def test_literal_help_tokens_success(
    parser: CustomArgumentParser, tokens: list[str]
) -> None:
    assert resolve_help(parser, tokens) is None


def test_literal_values_use_normal_parser_success(
    parser: CustomArgumentParser,
) -> None:
    args = parser.parse_args(["api", "v1/workspaces", "--input=--help"])
    assert args.input == ["--help"]
    args = parser.parse_args(["mkdir", "--", "--help"])
    assert args.path == ["--help"]


@pytest.mark.parametrize(
    "tokens",
    [
        ["unknown", "--help"],
        ["job", "unknown", "--help"],
        ["mkdir", "--unknown", "--help"],
        ["mkdir", "--help", "--output_format"],
        ["job", "run", "--timeout", "--help"],
        ["--help", "mkdir"],
        ["mkdir", "--help=yes"],
        ["ls", "--long=yes", "--help"],
    ],
)
def test_invalid_help_structure_failure(
    parser: CustomArgumentParser, tokens: list[str]
) -> None:
    request = resolve_help(parser, tokens)
    assert request is not None
    assert request.error is not None


def test_parser_selector_and_singleton_reuse_success(
    parser: CustomArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    args = parser.parse_args(["--output_format", "json", "mkdir", "x.Notebook"])
    assert args.output_format == "json"
    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(["mkdir", "--help", "--output_format=json"])
    assert exit_info.value.code == 0
    assert json.loads(capsys.readouterr().out)["command"] == "mkdir"
    args = parser.parse_args(["mkdir", "x.Notebook"])
    assert args.output_format is None
    args = parser.parse_args(["job", "--output_format=json", "run", "x.Notebook"])
    assert args.output_format == "json"
    args = parser.parse_args(["-c", "pwd", "-c", "ls"])
    assert args.command == ["pwd", "ls"]


def test_examples_preserve_payload_quoting_success() -> None:
    parser = CustomArgumentParser(
        prog="fab example",
        fab_examples=["# Pass JSON", """$ example --input '{"key": "--help"}'"""],
    )
    examples: list[dict[str, Any]] = build_help_data(parser)["examples"]
    assert examples == [
        {
            "description": "Pass JSON",
            "command": """fab example --input '{"key": "--help"}'""",
        }
    ]


@pytest.mark.parametrize("operation", ["login", "logout", "status"])
def test_auth_examples_preserve_modes_success(
    parser: CustomArgumentParser, operation: str
) -> None:
    node = next(
        node
        for node in _nodes(parser)
        if canonical_command(node) == f"auth {operation}"
    )
    expected = [
        {
            "description": "interactive mode",
            "command": f"auth {operation}",
        },
        {
            "description": "command_line mode",
            "command": f"fab auth {operation}",
        },
    ]
    if operation == "login":
        expected.extend(
            [
                {
                    "description": "command_line mode using Azure CLI auth",
                    "command": "fab auth login --azure-cli",
                },
                {
                    "description": "command_line mode using service principal auth",
                    "command": "fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>",
                },
                {
                    "description": "command_line mode using system assigned managed identity auth",
                    "command": "fab auth login --identity",
                },
                {
                    "description": "command_line mode using user assigned managed identity auth",
                    "command": "fab auth login -i -u <client_id>",
                },
            ]
        )
    assert build_help_data(node)["examples"] == expected
    assert getattr(node, "fab_examples")[:2] == [
        "# interactive mode",
        f"$ auth {operation}\n",
    ]


@pytest.mark.parametrize(
    ("description", "invocation", "expected"),
    [
        ("interactive mode", "example", "example"),
        ("interactive mode", "fab example", "example"),
        ("command_line mode", "example", "fab example"),
        ("command_line mode", "fab example", "fab example"),
        ("List items", "ls -l", "fab ls -l"),
        ("List items", "fab ls -l", "fab ls -l"),
    ],
)
def test_example_prefix_matches_mode_success(
    description: str, invocation: str, expected: str
) -> None:
    parser = CustomArgumentParser(
        prog="fab example",
        fab_examples=[f"# {description}", f"$ {invocation}"],
    )
    assert build_help_data(parser)["examples"] == [
        {"description": description, "command": expected}
    ]
