# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the usage-string helper shared by every parser."""

import argparse

import pytest

from fabric_cli.utils import fab_error_parser as utils_error_parser


def _parser(prog: str = "fab demo") -> argparse.ArgumentParser:
    """Build a bare parser without argparse's implicit help flag."""
    return argparse.ArgumentParser(prog=prog, add_help=False)


def test_required_flags_render_unbracketed() -> None:
    parser = _parser()
    parser.add_argument("--config", metavar="", required=True)

    assert utils_error_parser.get_usage_prog(parser) == "demo --config"


def test_optional_flags_render_bracketed() -> None:
    parser = _parser()
    parser.add_argument("--force", metavar="", required=False)

    assert utils_error_parser.get_usage_prog(parser) == "demo [--force]"


def test_short_form_is_preferred_when_declared_first() -> None:
    """`option_strings[0]` wins, so declaration order decides the rendering."""
    parser = _parser()
    parser.add_argument("-o", "--output", metavar="", required=True)
    parser.add_argument("--format", "-F", metavar="", required=False)

    assert utils_error_parser.get_usage_prog(parser) == "demo -o [--format]"


def test_positionals_precede_flags() -> None:
    parser = _parser()
    parser.add_argument("path")
    parser.add_argument("-f", metavar="", required=False)

    assert utils_error_parser.get_usage_prog(parser) == "demo <path> [-f]"


def test_no_positionals_does_not_produce_a_double_space() -> None:
    """A double space is exactly what breaks argparse's usage round-trip."""
    parser = _parser()
    parser.add_argument("--config", metavar="", required=True)

    usage = utils_error_parser.get_usage_prog(parser)

    assert "  " not in usage


def test_parser_without_arguments_renders_only_the_command() -> None:
    assert utils_error_parser.get_usage_prog(_parser("fab auth status")) == (
        "auth status"
    )


@pytest.mark.parametrize(
    "prog, expected",
    [("fab demo", "demo"), ("fab job run-update", "job run-update")],
)
def test_root_program_name_is_stripped(prog: str, expected: str) -> None:
    assert utils_error_parser.get_usage_prog(_parser(prog)) == expected


def test_mixed_arguments_render_in_declaration_order() -> None:
    parser = _parser("fab acl set")
    parser.add_argument("path")
    parser.add_argument("-I", metavar="", required=True)
    parser.add_argument("-R", metavar="", required=True)
    parser.add_argument("-f", metavar="", required=False)

    assert utils_error_parser.get_usage_prog(parser) == "acl set <path> -I -R [-f]"
