# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from unittest.mock import MagicMock

from fabric_cli.core.hiearchy.fab_onelake_element import OneLakeItem
from fabric_cli.utils import fab_cmd_table_utils as utils_table


def _make_context(local_path: str) -> MagicMock:
    context = MagicMock()
    context.__class__ = OneLakeItem  # make isinstance(context, OneLakeItem) pass
    context.local_path = local_path
    return context


class TestAddTablePropsToArgs:
    """Unit tests for add_table_props_to_args path normalization."""

    def test_shortcut_suffix_stripped_from_table_name(self):
        """Regression: .Shortcut must not appear in args.table_name (used in REST URIs)."""
        args = Namespace()
        utils_table.add_table_props_to_args(args, _make_context("Tables/my_table.Shortcut"))
        assert args.table_name == "my_table"

    def test_shortcut_suffix_stripped_from_table_local_path(self):
        """Regression: .Shortcut must not appear in args.table_local_path."""
        args = Namespace()
        utils_table.add_table_props_to_args(args, _make_context("Tables/my_table.Shortcut"))
        assert args.table_local_path == "Tables/my_table"

    def test_shortcut_suffix_stripped_from_schema_qualified_path(self):
        """Regression: .Shortcut must not appear in schema-qualified table_local_path."""
        args = Namespace()
        utils_table.add_table_props_to_args(args, _make_context("Tables/dbo/my_table.Shortcut"))
        assert args.table_local_path == "Tables/dbo/my_table"

    def test_normal_path_unchanged(self):
        args = Namespace()
        utils_table.add_table_props_to_args(args, _make_context("Tables/my_table"))
        assert args.table_local_path == "Tables/my_table"

    def test_schema_qualified_path_unchanged(self):
        args = Namespace()
        utils_table.add_table_props_to_args(args, _make_context("Tables/dbo/my_table"))
        assert args.table_local_path == "Tables/dbo/my_table"
