# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests that every registered parser can render its help output."""

import argparse
from typing import Iterator, Tuple

import pytest

from fabric_cli.core import fab_parser_setup

# Flags injected into every parser by `fab_global_params.add_global_flags`.
_GLOBAL_FLAG_DESTS = {"help", "output_format"}


def _walk_parsers(
    parser: argparse.ArgumentParser, prog: str
) -> Iterator[Tuple[str, argparse.ArgumentParser, bool]]:
    """Yield (command, parser, is_group) for a parser and all of its subparsers."""
    subparser_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    yield prog, parser, bool(subparser_actions)

    for action in subparser_actions:
        visited: set[int] = set()
        for name, subparser in action.choices.items():
            # Aliases point at the same parser instance; only walk it once.
            if id(subparser) in visited:
                continue
            visited.add(id(subparser))
            yield from _walk_parsers(subparser, f"{prog} {name}")


def _all_parsers() -> list[Tuple[str, argparse.ArgumentParser, bool]]:
    parser, _ = fab_parser_setup.create_parser_and_subparsers()
    return list(_walk_parsers(parser, "fab"))


def _declares_own_arguments(parser: argparse.ArgumentParser) -> bool:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        if action.dest in _GLOBAL_FLAG_DESTS:
            continue
        return True
    return False


_PARSERS = _all_parsers()


@pytest.fixture
def narrow_terminal(monkeypatch):
    """Force argparse to wrap usage lines.

    `argparse.HelpFormatter` derives its width from `shutil.get_terminal_size()`,
    which honours `COLUMNS`. The #277 crash only happens on the wrapping path, so a
    wide test terminal would hide it.
    """
    monkeypatch.setenv("COLUMNS", "60")


@pytest.mark.parametrize(
    "command, parser",
    [(command, parser) for command, parser, _ in _PARSERS],
    ids=[command for command, _, _ in _PARSERS],
)
def test_format_help_does_not_raise(command, parser, narrow_terminal):
    """`<command> --help` must render instead of crashing.

    Regression test for #277: `job run-update` had no explicit `usage`, so argparse
    built and wrapped one itself. A required flag with an empty metavar produced a
    double space in the usage string, tripping the internal assertion in
    `argparse.HelpFormatter._format_usage` (Python <= 3.12).
    """
    assert parser.format_help()


@pytest.mark.parametrize(
    "command, parser",
    [(command, parser) for command, parser, is_group in _PARSERS if not is_group],
    ids=[command for command, _, is_group in _PARSERS if not is_group],
)
def test_leaf_parsers_declaring_arguments_set_explicit_usage(command, parser):
    """Leaf commands with their own arguments must set `usage` explicitly.

    Relying on argparse's generated usage is what triggered #277. This check is
    Python-version independent, unlike the crash itself.
    """
    if not _declares_own_arguments(parser):
        pytest.skip(f"'{command}' declares no arguments of its own")

    assert parser.usage, f"'{command}' must set an explicit usage string"


def _find_parser(command: str) -> argparse.ArgumentParser:
    for name, parser, _ in _PARSERS:
        if name == command:
            return parser
    raise AssertionError(f"parser '{command}' not found")


def test_job_run_update_help_lists_flags():
    """Regression test for #277."""
    run_update = _find_parser("fab job run-update")

    help_message = run_update.format_help()

    assert "Usage: job run-update <path>" in help_message
    for flag in ("--id", "--input", "--enable", "--disable", "--type", "--days"):
        assert flag in help_message
