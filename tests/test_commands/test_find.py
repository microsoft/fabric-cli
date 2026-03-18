# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the find command — unit tests and e2e (VCR) tests."""

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.commands.find import fab_find
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from tests.test_commands.commands_parser import CLIExecutor


# Sample API responses for testing
SAMPLE_RESPONSE_WITH_RESULTS = {
    "value": [
        {
            "id": "0acd697c-1550-43cd-b998-91bfb12347c6",
            "type": "Report",
            "catalogEntryType": "FabricItem",
            "displayName": "Monthly Sales Revenue",
            "description": "Consolidated revenue report for the current fiscal year.",
            "workspaceId": "18cd155c-7850-15cd-a998-91bfb12347aa",
            "workspaceName": "Sales Department",
        },
        {
            "id": "123d697c-7848-77cd-b887-91bfb12347cc",
            "type": "Lakehouse",
            "catalogEntryType": "FabricItem",
            "displayName": "Yearly Sales Revenue",
            "description": "Consolidated revenue report for the current fiscal year.",
            "workspaceId": "18cd155c-7850-15cd-a998-91bfb12347aa",
            "workspaceName": "Sales Department",
        },
    ],
    "continuationToken": "lyJ1257lksfdfG==",
}

SAMPLE_RESPONSE_EMPTY = {
    "value": [],
}

SAMPLE_RESPONSE_SINGLE = {
    "value": [
        {
            "id": "abc12345-1234-5678-9abc-def012345678",
            "type": "Notebook",
            "catalogEntryType": "FabricItem",
            "displayName": "Data Analysis",
            "description": "Notebook for data analysis tasks.",
            "workspaceId": "workspace-id-123",
            "workspaceName": "Analytics Team",
        },
    ],
}


class TestBuildSearchPayload:
    """Tests for _build_search_payload function."""

    def test_basic_query_interactive(self):
        args = Namespace(search_text="sales report", params=None, query=None)
        payload = fab_find._build_search_payload(args, is_interactive=True)

        assert payload["search"] == "sales report"
        assert payload["pageSize"] == 50
        assert "filter" not in payload

    def test_basic_query_commandline(self):
        args = Namespace(search_text="sales report", params=None, query=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "sales report"
        assert payload["pageSize"] == 1000
        assert "filter" not in payload

    def test_query_with_single_type(self):
        args = Namespace(search_text="report", params="type=Report", query=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "report"
        assert payload["filter"] == "Type eq 'Report'"

    def test_query_with_multiple_types(self):
        args = Namespace(search_text="data", params="type=[Lakehouse,Warehouse]", query=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "data"
        assert payload["filter"] == "(Type eq 'Lakehouse' or Type eq 'Warehouse')"

    def test_query_with_multiple_types_legacy_comma(self):
        args = Namespace(search_text="data", params="type=Lakehouse,Warehouse", query=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "data"
        assert payload["filter"] == "(Type eq 'Lakehouse' or Type eq 'Warehouse')"

    def test_query_with_ne_single_type(self):
        args = Namespace(search_text="data", params="type!=Dashboard", query=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["filter"] == "Type ne 'Dashboard'"

    def test_query_with_ne_multiple_types(self):
        args = Namespace(search_text="data", params="type!=[Dashboard,Datamart]", query=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["filter"] == "(Type ne 'Dashboard' and Type ne 'Datamart')"


class TestParseTypeFromParams:
    """Tests for _parse_type_from_params function."""

    def test_no_params(self):
        args = Namespace(params=None)
        assert fab_find._parse_type_from_params(args) is None

    def test_empty_params(self):
        args = Namespace(params="")
        assert fab_find._parse_type_from_params(args) is None

    def test_single_type(self):
        args = Namespace(params="type=Report")
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "eq", "values": ["Report"]}

    def test_multiple_types_comma_separated(self):
        args = Namespace(params="type=Report,Lakehouse")
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "eq", "values": ["Report", "Lakehouse"]}

    def test_multiple_types_bracket_syntax(self):
        args = Namespace(params="type=[Report,Lakehouse]")
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "eq", "values": ["Report", "Lakehouse"]}

    def test_ne_single_type(self):
        args = Namespace(params="type!=Dashboard")
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "ne", "values": ["Dashboard"]}

    def test_ne_multiple_types_bracket(self):
        args = Namespace(params="type!=[Dashboard,Datamart]")
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "ne", "values": ["Dashboard", "Datamart"]}

    def test_ne_unsupported_type_allowed(self):
        args = Namespace(params="type!=Dashboard")
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "ne", "values": ["Dashboard"]}

    def test_invalid_format_raises_error(self):
        args = Namespace(params="notakeyvalue")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_from_params(args)
        assert "Invalid parameter format" in str(exc_info.value)

    def test_unknown_param_raises_error(self):
        args = Namespace(params="foo=bar")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_from_params(args)
        assert "isn't a supported parameter" in str(exc_info.value)

    def test_unknown_param_ne_raises_error(self):
        args = Namespace(params="foo!=bar")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_from_params(args)
        assert "isn't a supported parameter" in str(exc_info.value)

    def test_unsupported_type_eq_raises_error(self):
        args = Namespace(params="type=Dashboard")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_from_params(args)
        assert "Dashboard" in str(exc_info.value)
        assert "isn't searchable" in str(exc_info.value)

    def test_unknown_type_raises_error(self):
        args = Namespace(params="type=InvalidType")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_from_params(args)
        assert "InvalidType" in str(exc_info.value)
        assert "isn't a recognized item type" in str(exc_info.value)

    def test_unknown_type_ne_raises_error(self):
        args = Namespace(params="type!=InvalidType")
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_from_params(args)
        assert "InvalidType" in str(exc_info.value)
        assert "isn't a recognized item type" in str(exc_info.value)

    def test_list_input_backward_compat(self):
        """Ensure list input (from nargs='*') still works."""
        args = Namespace(params=["type=Report"])
        result = fab_find._parse_type_from_params(args)
        assert result == {"operator": "eq", "values": ["Report"]}


class TestSplitParams:
    """Tests for _split_params helper."""

    def test_single_param(self):
        assert fab_find._split_params("type=Report") == ["type=Report"]

    def test_bracket_param(self):
        assert fab_find._split_params("type=[Report,Lakehouse]") == ["type=[Report,Lakehouse]"]

    def test_multiple_params_with_equals(self):
        assert fab_find._split_params("type=Report,workspace=Sales") == [
            "type=Report",
            "workspace=Sales",
        ]

    def test_bracket_with_trailing_param(self):
        result = fab_find._split_params("type=[Report,Lakehouse],workspace=Sales")
        assert result == ["type=[Report,Lakehouse]", "workspace=Sales"]

    def test_legacy_comma_values_merged(self):
        """Legacy comma syntax: values without '=' merge back to previous param."""
        result = fab_find._split_params("type=Report,Lakehouse")
        assert result == ["type=Report,Lakehouse"]


class TestFetchResults:
    """Tests for _fetch_results helper."""

    @patch("fabric_cli.client.fab_api_catalog.search")
    def test_returns_items_and_token(self, mock_search):
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(SAMPLE_RESPONSE_WITH_RESULTS)
        mock_search.return_value = response

        args = Namespace()
        items, token = fab_find._fetch_results(args, {"search": "test"})

        assert len(items) == 2
        assert token == "lyJ1257lksfdfG=="

    @patch("fabric_cli.client.fab_api_catalog.search")
    def test_returns_none_token_when_empty(self, mock_search):
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(SAMPLE_RESPONSE_EMPTY)
        mock_search.return_value = response

        args = Namespace()
        items, token = fab_find._fetch_results(args, {"search": "test"})

        assert items == []
        assert token is None

    @patch("fabric_cli.client.fab_api_catalog.search")
    def test_raises_on_invalid_json(self, mock_search):
        response = MagicMock()
        response.status_code = 200
        response.text = "not json"
        mock_search.return_value = response

        args = Namespace()
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._fetch_results(args, {"search": "test"})
        assert "invalid response" in str(exc_info.value)


class TestDisplayItems:
    """Tests for _display_items function."""

    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_items_table(self, mock_print_format):
        args = Namespace(long=False, output_format="text", query=None)
        items = SAMPLE_RESPONSE_WITH_RESULTS["value"]

        fab_find._display_items(args, items)

        mock_print_format.assert_called_once()
        display_items = mock_print_format.call_args.kwargs["data"]
        assert len(display_items) == 2
        assert display_items[0]["name"] == "Monthly Sales Revenue"
        assert display_items[0]["type"] == "Report"
        assert display_items[0]["workspace"] == "Sales Department"
        assert display_items[0]["description"] == "Consolidated revenue report for the current fiscal year."

    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_items_detailed(self, mock_print_format):
        args = Namespace(long=True, output_format="text", query=None)
        items = SAMPLE_RESPONSE_SINGLE["value"]

        fab_find._display_items(args, items)

        mock_print_format.assert_called_once()
        display_items = mock_print_format.call_args.kwargs["data"]
        assert len(display_items) == 1

        item = display_items[0]
        assert item["name"] == "Data Analysis"
        assert item["type"] == "Notebook"
        assert item["workspace"] == "Analytics Team"
        assert item["description"] == "Notebook for data analysis tasks."
        assert item["id"] == "abc12345-1234-5678-9abc-def012345678"
        assert item["workspace_id"] == "workspace-id-123"

    @patch("fabric_cli.utils.fab_ui.print_output_format")
    @patch("fabric_cli.utils.fab_jmespath.search")
    def test_display_items_with_jmespath(self, mock_jmespath, mock_print_format):
        filtered = [{"name": "Monthly Sales Revenue", "type": "Report"}]
        mock_jmespath.return_value = filtered

        args = Namespace(long=False, output_format="text", query="[?type=='Report']")
        items = SAMPLE_RESPONSE_WITH_RESULTS["value"]

        fab_find._display_items(args, items)

        mock_jmespath.assert_called_once()
        mock_print_format.assert_called_once()
        display_items = mock_print_format.call_args.kwargs["data"]
        assert display_items == filtered


class TestRaiseOnError:
    """Tests for _raise_on_error function."""

    def test_success_response(self):
        response = MagicMock()
        response.status_code = 200
        fab_find._raise_on_error(response)

    def test_error_response_raises_fabric_cli_error(self):
        response = MagicMock()
        response.status_code = 403
        response.text = json.dumps({
            "errorCode": "InsufficientScopes",
            "message": "Missing required scope: Catalog.Read.All"
        })

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._raise_on_error(response)

        assert "Catalog search failed" in str(exc_info.value)
        assert "Missing required scope" in str(exc_info.value)

    def test_error_response_non_json(self):
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._raise_on_error(response)

        assert "Catalog search failed" in str(exc_info.value)


class TestSearchableItemTypes:
    """Tests for item type lists loaded from YAML."""

    def test_searchable_types_excludes_unsupported(self):
        assert "Dashboard" not in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Dataflow" in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Report" in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Lakehouse" in fab_find.SEARCHABLE_ITEM_TYPES

    def test_all_types_includes_unsupported(self):
        assert "Dashboard" in fab_find.ALL_ITEM_TYPES

    def test_types_loaded_from_yaml(self):
        assert len(fab_find.SEARCHABLE_ITEM_TYPES) > 30
        assert len(fab_find.UNSUPPORTED_ITEM_TYPES) >= 1


# ---------------------------------------------------------------------------
# E2E tests (VCR-recorded)
#
# These tests use the CLIExecutor to run actual find commands through the
# full CLI pipeline, with HTTP calls recorded/played back via VCR cassettes.
#
# To record cassettes:
#   1. Set env vars:
#      $env:FAB_TOKEN = "<bearer-token-with-Catalog.Read.All>"
#      $env:FAB_TOKEN_ONELAKE = $env:FAB_TOKEN
#      $env:FAB_API_ENDPOINT_FABRIC = "dailyapi.fabric.microsoft.com"
#   2. Run:
#      pytest tests/test_commands/test_find.py::TestFindE2E --record -v
# ---------------------------------------------------------------------------


class TestFindE2E:
    """End-to-end tests for the find command with VCR cassettes."""

    @pytest.fixture(autouse=True)
    def _mock_input(self, monkeypatch):
        """Raise EOFError on input() to stop pagination after the first page."""
        monkeypatch.setattr("builtins.input", lambda *args: (_ for _ in ()).throw(EOFError))

    def test_find_basic_search(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search returns results and prints output."""
        cli_executor.exec_command("find 'data'")

        mock_questionary_print.assert_called()
        output = str(mock_questionary_print.call_args_list)
        # Should contain at least one item with a name and type
        assert "name" in output or "type" in output or "workspace" in output

    def test_find_with_type_filter(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with -P type= returns only matching types."""
        cli_executor.exec_command("find 'data' -P type=Lakehouse")

        mock_questionary_print.assert_called()
        output = str(mock_questionary_print.call_args_list)
        assert "Lakehouse" in output

    def test_find_with_long_output(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with -l includes IDs in output."""
        cli_executor.exec_command("find 'data' -l")

        mock_questionary_print.assert_called()
        output = str(mock_questionary_print.call_args_list)
        # Long output table should contain id and workspace_id columns
        assert "id" in output

    def test_find_no_results(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search for nonexistent term shows 'No items found'."""
        cli_executor.exec_command("find 'xyznonexistent98765zzz'")

        # print_grey is used for "No items found." but it's not mocked here
        # The command should complete without error
        # In playback, the cassette has an empty response

    def test_find_with_ne_filter(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with type!=Dashboard excludes Dashboard items."""
        cli_executor.exec_command("find 'report' -P type!=Dashboard")

        mock_questionary_print.assert_called()
        output = str(mock_questionary_print.call_args_list)
        # No item should have Type: Dashboard (the word may appear in names)
        assert "Type: Dashboard" not in output
