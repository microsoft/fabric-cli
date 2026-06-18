# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest
from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import DeltaError, TableNotFoundError

from fabric_cli.commands.tables import fab_tables_schema
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError

_DELTA_CLIENT = "fabric_cli.client.fab_delta_client"


class TestDeltaClientSchemaUnit:
    """Unit tests for fab_delta_client schema extraction — no network, no VCR."""

    @pytest.fixture
    def mock_auth(self):
        with patch(f"{_DELTA_CLIENT}.FabAuth") as mock:
            instance = MagicMock()
            instance.get_access_token.return_value = "mock_token"
            mock.return_value = instance
            yield mock

    @pytest.fixture
    def mock_delta_table(self):
        with patch(f"{_DELTA_CLIENT}.DeltaTable") as mock:
            yield mock

    def _make_delta_table_mock(self, mock_delta_table, schema_json):
        mock_arrow_schema = MagicMock()
        mock_arrow_schema.to_json.return_value = schema_json
        mock_table_instance = MagicMock()
        mock_table_instance.schema.return_value = mock_arrow_schema
        mock_delta_table.return_value = mock_table_instance

    def test_auth_token_none_raises_authentication_error(self):
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t")
        with patch(f"{_DELTA_CLIENT}.FabAuth") as mock_auth:
            mock_auth.return_value.get_access_token.return_value = None
            with pytest.raises(FabricCLIError) as exc_info:
                fab_tables_schema._get_table_schema(args)
        assert exc_info.value.status_code == fab_constant.ERROR_AUTHENTICATION_FAILED

    def test_get_table_schema_success(self, mock_auth, mock_delta_table):
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_local_path="Tables/test_table",
        )
        mock_schema = {
            "fields": [
                {"name": "id", "type": "integer", "nullable": False, "metadata": {}},
                {"name": "name", "type": "string", "nullable": True, "metadata": {}},
            ]
        }
        self._make_delta_table_mock(mock_delta_table, json.dumps(mock_schema))

        result = fab_tables_schema._get_table_schema(args)

        assert len(result) == 2
        assert result[0] == {"name": "id", "type": "integer", "nullable": False, "metadata": {}}
        assert result[1] == {"name": "name", "type": "string", "nullable": True, "metadata": {}}

        call_args = mock_delta_table.call_args
        assert "test-lakehouse-id" in call_args[0][0]
        assert "Tables/test_table" in call_args[0][0]
        assert call_args[1]["storage_options"]["bearer_token"] == "mock_token"
        assert call_args[1]["storage_options"]["use_fabric_endpoint"] == "true"

    def test_get_table_schema_with_schema_namespace(self, mock_auth, mock_delta_table):
        """Schema-qualified path (e.g. Tables/dbo/table) passes the full path to DeltaTable."""
        args = Namespace(
            ws_id="test-ws-id",
            lakehouse_id="test-lakehouse-id",
            table_local_path="Tables/dbo/test_table",
        )
        self._make_delta_table_mock(
            mock_delta_table,
            json.dumps({"fields": [{"name": "col1", "type": "long", "nullable": True, "metadata": {}}]}),
        )

        result = fab_tables_schema._get_table_schema(args)

        assert mock_delta_table.call_args[0][0].endswith("Tables/dbo/test_table")
        assert result[0]["name"] == "col1"

    def test_abfss_uri_format(self, mock_auth, mock_delta_table):
        """DeltaTable must be called with a well-formed abfss:// URI."""
        args = Namespace(
            ws_id="workspace-guid-123",
            lakehouse_id="lakehouse-guid-456",
            table_local_path="Tables/my_table",
        )
        self._make_delta_table_mock(
            mock_delta_table,
            json.dumps({"fields": [{"name": "c", "type": "string", "nullable": True, "metadata": {}}]}),
        )

        fab_tables_schema._get_table_schema(args)

        uri = mock_delta_table.call_args[0][0]
        assert uri.startswith("abfss://workspace-guid-123@")
        assert "lakehouse-guid-456" in uri
        assert "Tables/my_table" in uri
        opts = mock_delta_table.call_args[1]["storage_options"]
        assert opts["bearer_token"] == "mock_token"
        assert opts["use_fabric_endpoint"] == "true"

    @pytest.mark.parametrize("error_cls", [TableNotFoundError, DeltaError])
    def test_delta_exceptions_map_to_fabric_cli_error(self, mock_auth, mock_delta_table, error_cls):
        args = Namespace(
            ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t"
        )
        mock_delta_table.side_effect = error_cls("error")

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE
        assert "Failed to extract the table schema" in exc_info.value.message

    def test_invalid_json_maps_to_fabric_cli_error(self, mock_auth, mock_delta_table):
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t")
        self._make_delta_table_mock(mock_delta_table, "invalid json {")

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE

    def test_missing_fields_key_maps_to_fabric_cli_error(self, mock_auth, mock_delta_table):
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t")
        self._make_delta_table_mock(mock_delta_table, json.dumps({"other": "value"}))

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE

    def test_fields_not_list_maps_to_fabric_cli_error(self, mock_auth, mock_delta_table):
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t")
        self._make_delta_table_mock(mock_delta_table, json.dumps({"fields": "not a list"}))

        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_DELTA_TABLE

    def test_complex_schema_field_contract(self, mock_auth, mock_delta_table):
        """Lock the exact JSON shape returned for complex Delta types.

        delta-rs serialises Arrow → Delta-protocol JSON via Schema.to_json().
        The mapping below was validated against the installed deltalake wheel
        and must be stable for users who pipe --output_format json into scripts.

        Verified mappings:
          pyarrow int64           → "long"          (NOT "integer")
          pyarrow decimal128      → "decimal(10,2)" (compact string, NOT an object)
          pyarrow timestamp('us') → "timestamp_ntz" (NOT "timestamp")
          map / struct            → nested objects with keyType/valueType/fields
        """
        complex_schema_json = {
            "type": "struct",
            "fields": [
                {"name": "id",         "type": "long",          "nullable": False, "metadata": {}},
                {"name": "price",      "type": "decimal(10,2)", "nullable": True,  "metadata": {}},
                {"name": "created_at", "type": "timestamp_ntz", "nullable": True,  "metadata": {}},
                {
                    "name": "tags",
                    "type": {"type": "map", "keyType": "string", "valueType": "string", "valueContainsNull": True},
                    "nullable": True,
                    "metadata": {},
                },
                {
                    "name": "address",
                    "type": {
                        "type": "struct",
                        "fields": [
                            {"name": "street", "type": "string", "nullable": True, "metadata": {}},
                            {"name": "city",   "type": "string", "nullable": True, "metadata": {}},
                        ],
                    },
                    "nullable": True,
                    "metadata": {},
                },
            ],
        }
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/complex_table")
        self._make_delta_table_mock(mock_delta_table, json.dumps(complex_schema_json))

        fields = fab_tables_schema._get_table_schema(args)

        assert len(fields) == 5
        assert fields[0] == {"name": "id", "type": "long", "nullable": False, "metadata": {}}
        assert fields[1] == {"name": "price", "type": "decimal(10,2)", "nullable": True, "metadata": {}}
        assert fields[2] == {"name": "created_at", "type": "timestamp_ntz", "nullable": True, "metadata": {}}
        assert fields[3] == {
            "name": "tags",
            "type": {"type": "map", "keyType": "string", "valueType": "string", "valueContainsNull": True},
            "nullable": True,
            "metadata": {},
        }
        assert fields[4] == {
            "name": "address",
            "type": {
                "type": "struct",
                "fields": [
                    {"name": "street", "type": "string", "nullable": True, "metadata": {}},
                    {"name": "city",   "type": "string", "nullable": True, "metadata": {}},
                ],
            },
            "nullable": True,
            "metadata": {},
        }


class TestDeltaItemTypeValidation:
    """Only item types with a Delta-compatible Tables/ folder are accepted."""

    @pytest.fixture
    def mock_auth(self):
        with patch(f"{_DELTA_CLIENT}.FabAuth") as mock:
            mock.return_value.get_access_token.return_value = "mock_token"
            yield mock

    @pytest.fixture
    def mock_delta_table(self):
        with patch(f"{_DELTA_CLIENT}.DeltaTable") as mock:
            schema = MagicMock()
            schema.to_json.return_value = json.dumps({"fields": []})
            mock.return_value.schema.return_value = schema
            yield mock

    @pytest.mark.parametrize("item_type", [
        "Lakehouse", "Warehouse", "KQLDatabase", "MirroredDatabase", "SQLDatabase",
    ])
    def test_supported_item_types_pass_validation(self, mock_auth, mock_delta_table, item_type):
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t", item_type=item_type)
        fab_tables_schema._get_table_schema(args)  # must not raise

    def test_semantic_model_raises_clear_error(self, mock_auth, mock_delta_table):
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t", item_type="SemanticModel")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_tables_schema._get_table_schema(args)
        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE
        assert "SemanticModel" in exc_info.value.message
        assert "Delta" in exc_info.value.message

    def test_missing_item_type_does_not_raise(self, mock_auth, mock_delta_table):
        """item_type may be absent when called directly in unit tests."""
        args = Namespace(ws_id="ws", lakehouse_id="lh", table_local_path="Tables/t")
        fab_tables_schema._get_table_schema(args)  # must not raise


class TestTablesSchemaCheckpointRegression:
    """Regression for #228: schema must be readable when only a checkpoint exists.

    The old implementation walked _delta_log/*.json manually; after log compaction
    those files are removed and only *.checkpoint.parquet + _last_checkpoint remain.
    The new implementation delegates to DeltaTable.schema(), which uses delta-rs's
    native reader that prefers checkpoints over JSON logs.
    """

    @pytest.fixture
    def checkpointed_delta_table(self, tmp_path):
        """Real local Delta table: checkpoint written, JSON commit log removed."""
        table_path = tmp_path / "test_table"
        df = pa.table({
            "id":         pa.array([1, 2], pa.int64()),
            "price":      pa.array([Decimal("9.99"), Decimal("19.99")], pa.decimal128(10, 2)),
            "created_at": pa.array([1_000_000, 2_000_000], pa.timestamp("us")),
        })
        write_deltalake(str(table_path), df)

        dt = DeltaTable(str(table_path))
        dt.create_checkpoint()

        for json_log in (table_path / "_delta_log").glob("*.json"):
            json_log.unlink()

        log_files = list((table_path / "_delta_log").iterdir())
        assert not any(f.suffix == ".json" for f in log_files), (
            "fixture must leave no JSON logs — only checkpoint parquet"
        )
        return table_path

    def test_schema_readable_after_log_compaction(self, checkpointed_delta_table):
        """Schema extraction succeeds when only a checkpoint parquet file exists."""
        real_dt = DeltaTable(str(checkpointed_delta_table))
        args = Namespace(ws_id="ws-id", lakehouse_id="lh-id", table_local_path="Tables/test_table")

        with patch(f"{_DELTA_CLIENT}.FabAuth") as mock_auth, \
             patch(f"{_DELTA_CLIENT}.DeltaTable", return_value=real_dt):
            mock_auth.return_value.get_access_token.return_value = "mock_token"
            fields = fab_tables_schema._get_table_schema(args)

        assert [f["name"] for f in fields] == ["id", "price", "created_at"]
        assert fields[0]["type"] == "long"
        assert fields[1]["type"] == "decimal(10,2)"
        assert fields[2]["type"] == "timestamp_ntz"
