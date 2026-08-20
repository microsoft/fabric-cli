# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the auth parser module — verifies argparse flag mapping."""

import argparse

from fabric_cli.core.fab_parser_setup import CustomArgumentParser
from fabric_cli.parsers import fab_auth_parser


def _build_auth_parser():
    """Build a parser with auth subcommands registered."""
    parser = CustomArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    fab_auth_parser.register_parser(subparsers)
    return parser


class TestAuthParserAzureCli:
    """Verify --azure-cli flag is parsed correctly."""

    def test_azure_cli_flag_sets_attribute(self):
        """--azure-cli should map to args.azure_cli=True."""
        parser = _build_auth_parser()
        args = parser.parse_args(["auth", "login", "--azure-cli"])
        assert args.azure_cli is True

    def test_azure_cli_flag_with_tenant(self):
        """--azure-cli --tenant should set both attributes."""
        parser = _build_auth_parser()
        args = parser.parse_args(
            ["auth", "login", "--azure-cli", "--tenant", "my-tenant-id"]
        )
        assert args.azure_cli is True
        assert args.tenant == "my-tenant-id"

    def test_azure_cli_flag_absent_defaults_false(self):
        """Without --azure-cli, azure_cli should be falsy."""
        parser = _build_auth_parser()
        args = parser.parse_args(["auth", "login"])
        assert not args.azure_cli

    def test_tenant_flag_without_azure_cli(self):
        """--tenant alone should work (used by other auth modes)."""
        parser = _build_auth_parser()
        args = parser.parse_args(["auth", "login", "--tenant", "some-tenant"])
        assert args.tenant == "some-tenant"
        assert not args.azure_cli
