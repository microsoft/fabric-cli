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

    @pytest.fixture
    def mock_auth(self):
        with patch("fabric_cli.commands.tables.fab_tables_schema.FabAuth") as mock:
            instance = MagicMock()
            instance.get_access_token.return_value = "mock_token"
            mock.return_value = instance
            yield mock

    @pytest.fixture
    def mock_delta_table(self):
        with patch("fabric_cli.commands.tables.fab_tables_schema.DeltaTable") as mock:
            yield mock

    def _make_delta_table_mock(self, mock_delta_table, schema_json):
        mock_arrow_schema = MagicMock()
        mock_arrow_schema.to_json.return_value = schema_json
        mock_table_instance = MagicMock()
        mock_table_instance.schema.return_value = mock_arrow_schema
        mock_delta_table.return_value = mock_table_instance

    def test_get_table_schema_success(self, mock_auth, mock_delta_table):
        """Test successful schema extraction."""
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
        self._make_delta_table_mock(mock_delta_table, json.dumps(mock_schema))

        result = fab_tables_schema._get_table_schema(args)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "id"
        assert result[0]["type"] == "integer"
        assert result[1]["name"] == "name"
        assert result[1]["type"] == "string"

        mock_delta_table.assert_called_once()
        call_args = mock_delta_table.call_args
        assert "test-lakehouse-id" in call_args[0][0]
        assert "Tables/test_table" in call_args[0][0]
        assert call_args[1]["storage_options"]["bearer_token"] == "mock_token"
        assert call_args[1]["storage_options"]["use_fabric_endpoint"] == "true"

    def test_get_table_schema_with_explicit_schema_success(self, mock_auth, mock_delta_table):
        """Test schema extraction with explicit schema name (e.g., dbo)."""
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
        self._make_delta_table_mock(mock_delta_table, json.dumps(mock_schema))

        result = fab_tables_schema._get_table_schema(args)

        call_args = mock_delta_table.call_args
        assert "Tables/dbo/test_table" in call_args[0][0]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "col1"

    def test_get_table_schema_table_not_found_error(self, mock_auth, mock_delta_table):
        """Test TableNotFoundError is mapped to FabricCLIError."""
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="nonexistent",
            schema=None,
        )

        mock_delta_table.side_effect = TableNotFoundError("Table not found")

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
        assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_delta_error(self, mock_auth, mock_delta_table):
        """Test generic DeltaError is mapped to FabricCLIError."""
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        mock_delta_table.side_effect = DeltaError("Generic delta error")

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
        assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_invalid_json_error(self, mock_auth, mock_delta_table):
        """Test invalid JSON in schema is handled."""
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        self._make_delta_table_mock(mock_delta_table, "invalid json {")

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
        assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_missing_fields_key(self, mock_auth, mock_delta_table):
        """Test schema JSON without 'fields' key is handled."""
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        self._make_delta_table_mock(mock_delta_table, json.dumps({"some_other_key": "value"}))

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
        assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_fields_not_list(self, mock_auth, mock_delta_table):
        """Test schema JSON with 'fields' not being a list is handled."""
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_name="test_table",
            schema=None,
        )

        self._make_delta_table_mock(mock_delta_table, json.dumps({"fields": "not a list"}))

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
        assert "Failed to extract the table schema" in exc_info.value.message

    def test_get_table_schema_verifies_abfss_uri_format(self, mock_auth, mock_delta_table):
        """Test that table URI is correctly formatted with ABFSS protocol."""
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
        self._make_delta_table_mock(mock_delta_table, json.dumps(mock_schema))

        result = fab_tables_schema._get_table_schema(args)

        call_args = mock_delta_table.call_args
        table_uri = call_args[0][0]

        assert table_uri.startswith("abfss://workspace-guid-123@")
        assert "lakehouse-guid-456" in table_uri
        assert "Tables/my_table" in table_uri

        storage_options = call_args[1]["storage_options"]
        assert storage_options["bearer_token"] == "mock_token"
        assert storage_options["use_fabric_endpoint"] == "true"

        assert isinstance(result, list)
        assert len(result) == 1
