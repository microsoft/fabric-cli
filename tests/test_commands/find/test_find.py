# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for the find command."""

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.commands.find import fab_find
from fabric_cli.client.fab_api_types import ApiResponse


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
        result = json.loads(payload)

        assert result["search"] == "sales report"
        assert "filter" not in result
        assert "pageSize" not in result

    def test_query_with_limit(self):
        """Test search with limit."""
        args = Namespace(query="data", type=None, limit=10)
        payload = fab_find._build_search_payload(args)
        result = json.loads(payload)

        assert result["search"] == "data"
        assert result["pageSize"] == 10

    def test_query_with_single_type(self):
        """Test search with single type filter."""
        args = Namespace(query="report", type="Report", limit=None)
        payload = fab_find._build_search_payload(args)
        result = json.loads(payload)

        assert result["search"] == "report"
        assert result["filter"] == "Type eq 'Report'"

    def test_query_with_multiple_types(self):
        """Test search with multiple type filters."""
        args = Namespace(query="data", type="Lakehouse,Warehouse", limit=None)
        payload = fab_find._build_search_payload(args)
        result = json.loads(payload)

        assert result["search"] == "data"
        assert "Type eq 'Lakehouse'" in result["filter"]
        assert "Type eq 'Warehouse'" in result["filter"]
        assert " or " in result["filter"]

    def test_query_with_all_options(self):
        """Test search with all options."""
        args = Namespace(query="monthly", type="Report,Notebook", limit=25)
        payload = fab_find._build_search_payload(args)
        result = json.loads(payload)

        assert result["search"] == "monthly"
        assert result["pageSize"] == 25
        assert "Type eq 'Report'" in result["filter"]
        assert "Type eq 'Notebook'" in result["filter"]


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
        display_items = mock_print_format.call_args[0][1]
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
        display_items = mock_print_format.call_args[0][1]
        assert len(display_items) == 1

        # Detailed view should include id and workspaceId
        item = display_items[0]
        assert item["name"] == "Data Analysis"
        assert item["type"] == "Notebook"
        assert item["workspace"] == "Analytics Team"
        assert item["description"] == "Notebook for data analysis tasks."
        assert item["id"] == "abc12345-1234-5678-9abc-def012345678"
        assert item["workspaceId"] == "workspace-id-123"

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
    """Tests for type validation warnings."""

    @patch("fabric_cli.utils.fab_ui.print_warning")
    def test_unsupported_type_warning(self, mock_print_warning):
        """Test warning for unsupported item types."""
        args = Namespace(query="test", type="Dashboard", limit=None)
        fab_find._build_search_payload(args)

        mock_print_warning.assert_called()
        warning_msg = mock_print_warning.call_args[0][0]
        assert "Dashboard" in warning_msg
        assert "not supported" in warning_msg

    @patch("fabric_cli.utils.fab_ui.print_warning")
    def test_unknown_type_warning(self, mock_print_warning):
        """Test warning for unknown item types."""
        args = Namespace(query="test", type="InvalidType", limit=None)
        fab_find._build_search_payload(args)

        mock_print_warning.assert_called()
        warning_msg = mock_print_warning.call_args[0][0]
        assert "InvalidType" in warning_msg
        assert "Unknown" in warning_msg

    @patch("fabric_cli.utils.fab_ui.print_warning")
    def test_valid_type_no_warning(self, mock_print_warning):
        """Test no warning for valid item types."""
        args = Namespace(query="test", type="Report", limit=None)
        fab_find._build_search_payload(args)

        mock_print_warning.assert_not_called()
