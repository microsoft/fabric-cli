# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for the find command."""

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.commands.find import fab_find
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core.fab_exceptions import FabricCLIError


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

    def test_basic_query(self):
        """Test basic search query."""
        args = Namespace(query="sales report", type=None, limit=None)
        payload = fab_find._build_search_payload(args)

        assert payload["search"] == "sales report"
        assert "filter" not in payload
        assert "pageSize" not in payload

    def test_query_with_limit(self):
        """Test search with limit."""
        args = Namespace(query="data", type=None, limit=10)
        payload = fab_find._build_search_payload(args)

        assert payload["search"] == "data"
        assert payload["pageSize"] == 10

    def test_query_with_single_type(self):
        """Test search with single type filter (as list from nargs='+')."""
        args = Namespace(query="report", type=["Report"], limit=None)
        payload = fab_find._build_search_payload(args)

        assert payload["search"] == "report"
        assert payload["filter"] == "Type eq 'Report'"

    def test_query_with_multiple_types(self):
        """Test search with multiple type filters (as list from nargs='+')."""
        args = Namespace(query="data", type=["Lakehouse", "Warehouse"], limit=None)
        payload = fab_find._build_search_payload(args)

        assert payload["search"] == "data"
        assert "Type eq 'Lakehouse'" in payload["filter"]
        assert "Type eq 'Warehouse'" in payload["filter"]
        assert " or " in payload["filter"]

    def test_query_with_all_options(self):
        """Test search with all options."""
        args = Namespace(query="monthly", type=["Report", "Notebook"], limit=25)
        payload = fab_find._build_search_payload(args)

        assert payload["search"] == "monthly"
        assert payload["pageSize"] == 25
        assert "Type eq 'Report'" in payload["filter"]
        assert "Type eq 'Notebook'" in payload["filter"]


class TestDisplayResults:
    """Tests for _display_results function."""

    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_results_with_items(self, mock_print_format, mock_print_grey):
        """Test displaying results with items."""
        args = Namespace(detailed=False, output_format="text")
        response = MagicMock()
        response.text = json.dumps(SAMPLE_RESPONSE_WITH_RESULTS)

        fab_find._display_results(args, response)

        # Should print count message
        mock_print_grey.assert_called()
        count_call = mock_print_grey.call_args[0][0]
        assert "2 item(s) found" in count_call
        assert "(more available)" in count_call  # Has continuation token

        # Should call print_output_format with display items
        mock_print_format.assert_called_once()
        display_items = mock_print_format.call_args.kwargs["data"]
        assert len(display_items) == 2
        assert display_items[0]["name"] == "Monthly Sales Revenue"
        assert display_items[0]["type"] == "Report"
        assert display_items[0]["workspace"] == "Sales Department"
        assert display_items[0]["description"] == "Consolidated revenue report for the current fiscal year."

    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_results_empty(self, mock_print_format, mock_print_grey):
        """Test displaying empty results."""
        args = Namespace(detailed=False, output_format="text")
        response = MagicMock()
        response.text = json.dumps(SAMPLE_RESPONSE_EMPTY)

        fab_find._display_results(args, response)

        # Should print "No items found"
        mock_print_grey.assert_called_with("No items found.")
        mock_print_format.assert_not_called()

    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_results_detailed(self, mock_print_format, mock_print_grey):
        """Test displaying results with detailed flag."""
        args = Namespace(detailed=True, output_format="text")
        response = MagicMock()
        response.text = json.dumps(SAMPLE_RESPONSE_SINGLE)

        fab_find._display_results(args, response)

        # Should call print_output_format with detailed items
        mock_print_format.assert_called_once()
        display_items = mock_print_format.call_args.kwargs["data"]
        assert len(display_items) == 1

        # Detailed view should include id and workspace_id (snake_case)
        item = display_items[0]
        assert item["name"] == "Data Analysis"
        assert item["type"] == "Notebook"
        assert item["workspace"] == "Analytics Team"
        assert item["description"] == "Notebook for data analysis tasks."
        assert item["id"] == "abc12345-1234-5678-9abc-def012345678"
        assert item["workspace_id"] == "workspace-id-123"

    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_results_no_continuation_token(self, mock_print_format, mock_print_grey):
        """Test count message without continuation token."""
        args = Namespace(detailed=False, output_format="text")
        response = MagicMock()
        response.text = json.dumps(SAMPLE_RESPONSE_SINGLE)

        fab_find._display_results(args, response)

        # Should not show "(more available)"
        count_call = mock_print_grey.call_args[0][0]
        assert "1 item(s) found" in count_call
        assert "(more available)" not in count_call


class TestTypeValidation:
    """Tests for type validation errors."""

    def test_unsupported_type_raises_error(self):
        """Test error for unsupported item types like Dashboard."""
        args = Namespace(query="test", type=["Dashboard"], limit=None)

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._build_search_payload(args)

        assert "Dashboard" in str(exc_info.value)
        assert "not searchable" in str(exc_info.value)

    def test_unknown_type_raises_error(self):
        """Test error for unknown item types."""
        args = Namespace(query="test", type=["InvalidType"], limit=None)

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._build_search_payload(args)

        assert "InvalidType" in str(exc_info.value)
        assert "Unknown" in str(exc_info.value)

    def test_valid_type_builds_filter(self):
        """Test valid type builds correct filter."""
        args = Namespace(query="test", type=["Report"], limit=None)
        payload = fab_find._build_search_payload(args)
        assert payload["filter"] == "Type eq 'Report'"

    def test_multiple_types_build_or_filter(self):
        """Test multiple types build OR filter."""
        args = Namespace(query="test", type=["Report", "Lakehouse"], limit=None)
        payload = fab_find._build_search_payload(args)
        assert "Type eq 'Report'" in payload["filter"]
        assert "Type eq 'Lakehouse'" in payload["filter"]
        assert " or " in payload["filter"]

    def test_searchable_types_list(self):
        """Test SEARCHABLE_ITEM_TYPES excludes unsupported types."""
        assert "Dashboard" not in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Dataflow" not in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Report" in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Lakehouse" in fab_find.SEARCHABLE_ITEM_TYPES


class TestCompleteItemTypes:
    """Tests for the item type completer."""

    def test_complete_with_prefix(self):
        """Test completion with a prefix."""
        result = fab_find.complete_item_types("Lake")
        assert "Lakehouse" in result

    def test_complete_case_insensitive(self):
        """Test completion is case-insensitive."""
        result = fab_find.complete_item_types("report")
        assert "Report" in result

    def test_complete_multiple_matches(self):
        """Test completion returns multiple matches."""
        result = fab_find.complete_item_types("Data")
        assert "Datamart" in result
        assert "DataPipeline" in result

    def test_complete_excludes_unsupported_types(self):
        """Test completion excludes unsupported types like Dashboard."""
        result = fab_find.complete_item_types("Da")
        assert "Dashboard" not in result
        assert "Dataflow" not in result
        assert "Datamart" in result

    def test_complete_empty_prefix(self):
        """Test completion with empty prefix returns all searchable types."""
        result = fab_find.complete_item_types("")
        assert len(result) == len(fab_find.SEARCHABLE_ITEM_TYPES)
        assert "Dashboard" not in result


class TestHandleResponse:
    """Tests for _handle_response function."""

    @patch("fabric_cli.commands.find.fab_find._display_results")
    def test_success_response(self, mock_display):
        """Test successful response handling."""
        args = Namespace(detailed=False)
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(SAMPLE_RESPONSE_WITH_RESULTS)

        fab_find._handle_response(args, response)

        mock_display.assert_called_once_with(args, response)

    def test_error_response_raises_fabric_cli_error(self):
        """Test error response raises FabricCLIError."""
        args = Namespace(detailed=False)
        response = MagicMock()
        response.status_code = 403
        response.text = json.dumps({
            "errorCode": "InsufficientScopes",
            "message": "Missing required scope: Catalog.Read.All"
        })

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._handle_response(args, response)

        assert "Catalog search failed" in str(exc_info.value)
        assert "Missing required scope" in str(exc_info.value)

    def test_error_response_non_json(self):
        """Test error response with non-JSON body."""
        args = Namespace(detailed=False)
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._handle_response(args, response)

        assert "Catalog search failed" in str(exc_info.value)
