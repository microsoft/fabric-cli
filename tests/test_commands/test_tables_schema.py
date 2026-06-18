# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import MagicMock, patch

from tests.test_commands.commands_parser import CLIExecutor

_SCHEMA_COMMAND = "fabric_cli.commands.tables.fab_tables.schema_command"


class TestTablesSchemaIntegration:
    """Dispatch test: verifies the parser routes 'table schema <path>' to schema_command."""

    def test_table_schema_dispatches_to_schema_command(self, cli_executor: CLIExecutor):
        with patch(_SCHEMA_COMMAND) as mock_cmd:
            cli_executor.exec_command("table schema /ws.Workspace/lh.Lakehouse/Tables/my_table")

        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert args.path == ["/ws.Workspace/lh.Lakehouse/Tables/my_table"]

    def test_table_schema_dispatches_with_schema_namespace(self, cli_executor: CLIExecutor):
        with patch(_SCHEMA_COMMAND) as mock_cmd:
            cli_executor.exec_command("table schema /ws.Workspace/lh.Lakehouse/Tables/dbo/my_table")

        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert args.path == ["/ws.Workspace/lh.Lakehouse/Tables/dbo/my_table"]
