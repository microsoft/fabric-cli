# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core.fab_types import ItemType
from tests.conftest import mock_questionary_print  # noqa: F401
from tests.test_commands.commands_parser import CLIExecutor

_DELTA_CLIENT = "fabric_cli.client.fab_delta_client"


class TestTablesSchemaIntegration:
    """Integration tests for table schema command - validates full dispatch stack."""

    def test_table_schema_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        mock_questionary_print.reset_mock()

        with patch(
            f"{_DELTA_CLIENT}.DeltaTable"
        ) as mock_dt, patch(
            f"{_DELTA_CLIENT}.FabAuth"
        ) as mock_auth:
            mock_auth.return_value.get_access_token.return_value = "mock_token"
            mock_table = MagicMock()
            mock_table.schema.return_value.to_json.return_value = json.dumps({
                "fields": [{"name": "id", "type": "integer", "nullable": False, "metadata": {}}]
            })
            mock_dt.return_value = mock_table

            cli_executor.exec_command(
                f"table schema {lakehouse.full_path}/Tables/my_table"
            )

        calls = mock_questionary_print.call_args_list
        assert any("Schema extracted successfully" in str(c) for c in calls)
