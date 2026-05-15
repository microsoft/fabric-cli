# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest
from deltalake.exceptions import DeltaError, TableNotFoundError

from fabric_cli.commands.tables import fab_tables_schema
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError


class TestTablesSchemaUnit:
    """Unit tests for table schema command - direct function calls without VCR."""

    def test_get_table_schema_success(self):
        """Test successful schema extraction."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        mock_schema = {
            "fields": [
                {"name": "id", "type": "integer", "nullable": False, "metadata": {}},
                {"name": "name", "type": "string", "nullable": True, "metadata": {}},
            ]
        }

        # Mock DeltaTable
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            # Configure mocks
            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_table_instance = MagicMock()
            mock_arrow_schema = MagicMock()
            mock_arrow_schema.to_json.return_value = json.dumps(mock_schema)
            mock_table_instance.schema.return_value = mock_arrow_schema
            mock_delta_table.return_value = mock_table_instance

            # Call function
            result = fab_tables_schema._get_table_schema(args)

            # Assert
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["name"] == "id"
            assert result[0]["type"] == "integer"
            assert result[1]["name"] == "name"
            assert result[1]["type"] == "string"

            # Verify DeltaTable was called correctly
            mock_delta_table.assert_called_once()
            call_args = mock_delta_table.call_args
            assert "test-lakehouse-id" in call_args[0][0]
            assert "Tables/test_table" in call_args[0][0]
            assert call_args[1]["storage_options"]["bearer_token"] == "mock_token"
            assert call_args[1]["storage_options"]["use_fabric_endpoint"] == "true"

    def test_get_table_schema_with_explicit_schema_success(self):
        """Test schema extraction with explicit schema name (e.g., dbo)."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema="dbo",
        )

        mock_schema = {
            "fields": [
                {"name": "col1", "type": "long", "nullable": True, "metadata": {}},
            ]
        }

        # Mock DeltaTable
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            # Configure mocks
            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_table_instance = MagicMock()
            mock_arrow_schema = MagicMock()
            mock_arrow_schema.to_json.return_value = json.dumps(mock_schema)
            mock_table_instance.schema.return_value = mock_arrow_schema
            mock_delta_table.return_value = mock_table_instance

            # Call function
            result = fab_tables_schema._get_table_schema(args)

            # Verify table URI includes schema path
            call_args = mock_delta_table.call_args
            assert "Tables/dbo/test_table" in call_args[0][0]

            # Assert result
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["name"] == "col1"

    def test_get_table_schema_table_not_found_error(self):
        """Test TableNotFoundError is mapped to FabricCLIError."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="nonexistent",
            schema=None,
        )

        # Mock DeltaTable to raise TableNotFoundError
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_delta_table.side_effect = TableNotFoundError("Table not found")

            # Call function and expect error
            with pytest.raises(FabricCLIError) as exc_info:
                fab_tables_schema._get_table_schema(args)

            # Assert error details
            assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
            assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_delta_error(self):
        """Test generic DeltaError is mapped to FabricCLIError."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        # Mock DeltaTable to raise DeltaError
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_delta_table.side_effect = DeltaError("Generic delta error")

            # Call function and expect error
            with pytest.raises(FabricCLIError) as exc_info:
                fab_tables_schema._get_table_schema(args)

            # Assert error details
            assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
            assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_invalid_json_error(self):
        """Test invalid JSON in schema is handled."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        # Mock DeltaTable to return invalid JSON
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_table_instance = MagicMock()
            mock_arrow_schema = MagicMock()
            mock_arrow_schema.to_json.return_value = "invalid json {"
            mock_table_instance.schema.return_value = mock_arrow_schema
            mock_delta_table.return_value = mock_table_instance

            # Call function and expect error
            with pytest.raises(FabricCLIError) as exc_info:
                fab_tables_schema._get_table_schema(args)

            # Assert error details
            assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
            assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_missing_fields_key(self):
        """Test schema JSON without 'fields' key is handled."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        mock_schema = {"some_other_key": "value"}

        # Mock DeltaTable
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_table_instance = MagicMock()
            mock_arrow_schema = MagicMock()
            mock_arrow_schema.to_json.return_value = json.dumps(mock_schema)
            mock_table_instance.schema.return_value = mock_arrow_schema
            mock_delta_table.return_value = mock_table_instance

            # Call function and expect error
            with pytest.raises(FabricCLIError) as exc_info:
                fab_tables_schema._get_table_schema(args)

            # Assert error details
            assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
            assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_fields_not_list(self):
        """Test schema JSON with 'fields' not being a list is handled."""
        # Setup
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        mock_schema = {"fields": "not a list"}

        # Mock DeltaTable
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "mock_token"
            mock_auth.return_value = mock_auth_instance

            mock_table_instance = MagicMock()
            mock_arrow_schema = MagicMock()
            mock_arrow_schema.to_json.return_value = json.dumps(mock_schema)
            mock_table_instance.schema.return_value = mock_arrow_schema
            mock_delta_table.return_value = mock_table_instance

            # Call function and expect error
            with pytest.raises(FabricCLIError) as exc_info:
                fab_tables_schema._get_table_schema(args)

            # Assert error details
            assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
            assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_verifies_abfss_uri_format(self):
        """Test that table URI is correctly formatted with ABFSS protocol."""
        # Setup
        args = Namespace(
            ws_id="workspace-guid-123",
            lakehouse_id="lakehouse-guid-456",
            table_name="my_table",
            schema=None,
        )

        mock_schema = {
            "fields": [
                {"name": "col1", "type": "string", "nullable": True, "metadata": {}}
            ]
        }

        # Mock DeltaTable
        with patch(
            "fabric_cli.commands.tables.fab_tables_schema.DeltaTable"
        ) as mock_delta_table, patch(
            "fabric_cli.commands.tables.fab_tables_schema.FabAuth"
        ) as mock_auth:

            mock_auth_instance = MagicMock()
            mock_auth_instance.get_access_token.return_value = "test_token_123"
            mock_auth.return_value = mock_auth_instance

            mock_table_instance = MagicMock()
            mock_arrow_schema = MagicMock()
            mock_arrow_schema.to_json.return_value = json.dumps(mock_schema)
            mock_table_instance.schema.return_value = mock_arrow_schema
            mock_delta_table.return_value = mock_table_instance

            # Call function
            result = fab_tables_schema._get_table_schema(args)

            # Verify DeltaTable was called with correct URI format
            call_args = mock_delta_table.call_args
            table_uri = call_args[0][0]

            # Verify ABFSS format
            assert table_uri.startswith("abfss://workspace-guid-123@")
            assert "lakehouse-guid-456" in table_uri
            assert "Tables/my_table" in table_uri

            # Verify storage options
            storage_options = call_args[1]["storage_options"]
            assert storage_options["bearer_token"] == "test_token_123"
            assert storage_options["use_fabric_endpoint"] == "true"

            # Verify result
            assert isinstance(result, list)
            assert len(result) == 1
