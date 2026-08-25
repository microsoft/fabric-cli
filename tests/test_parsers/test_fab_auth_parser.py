# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for authentication argument parsing."""

from fabric_cli.core.fab_parser_setup import CustomArgumentParser
from fabric_cli.parsers import fab_auth_parser


def _build_auth_parser() -> CustomArgumentParser:
    """Build a parser with auth subcommands registered."""
    parser = CustomArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    fab_auth_parser.register_parser(subparsers)
    return parser


class TestAuthParserAzureCli:
    """Verify --azure-cli flag is parsed correctly."""

    def test_azure_cli_flag_sets_attribute(self) -> None:
        """--azure-cli should map to args.azure_cli=True."""
        parser = _build_auth_parser()
        args = parser.parse_args(["auth", "login", "--azure-cli"])
        assert args.azure_cli is True

    def test_azure_cli_flag_absent_defaults_false(self) -> None:
        """Without --azure-cli, azure_cli should be falsy."""
        parser = _build_auth_parser()
        args = parser.parse_args(["auth", "login"])
        assert args.azure_cli is False
