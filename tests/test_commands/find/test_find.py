# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for the find command."""

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.commands.find import fab_find
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant
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

    def test_basic_query_interactive(self):
        """Test basic search query in interactive mode."""
        args = Namespace(query="sales report", params=None)
        payload = fab_find._build_search_payload(args, is_interactive=True)

        assert payload["search"] == "sales report"
        assert payload["pageSize"] == 50
        assert "filter" not in payload

    def test_basic_query_commandline(self):
        """Test basic search query in command-line mode."""
        args = Namespace(query="sales report", params=None)
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "sales report"
        assert payload["pageSize"] == 1000
        assert "filter" not in payload

    def test_query_with_single_type(self):
        """Test search with single type filter via -P."""
        args = Namespace(query="report", params=["type=Report"])
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "report"
        assert payload["filter"] == "Type eq 'Report'"

    def test_query_with_multiple_types(self):
        """Test search with multiple type filters via -P."""
        args = Namespace(query="data", params=["type=Lakehouse,Warehouse"])
        payload = fab_find._build_search_payload(args, is_interactive=False)

        assert payload["search"] == "data"
        assert "Type eq 'Lakehouse'" in payload["filter"]
        assert "Type eq 'Warehouse'" in payload["filter"]
        assert " or " in payload["filter"]


class TestParseTypeParam:
    """Tests for _parse_type_param function."""

    def test_no_params(self):
        """Test with no params."""
        args = Namespace(params=None)
        assert fab_find._parse_type_param(args) == []

    def test_empty_params(self):
        """Test with empty params list."""
        args = Namespace(params=[])
        assert fab_find._parse_type_param(args) == []

    def test_single_type(self):
        """Test single type value."""
        args = Namespace(params=["type=Report"])
        assert fab_find._parse_type_param(args) == ["Report"]

    def test_multiple_types_comma_separated(self):
        """Test comma-separated types."""
        args = Namespace(params=["type=Report,Lakehouse"])
        result = fab_find._parse_type_param(args)
        assert result == ["Report", "Lakehouse"]

    def test_invalid_format_raises_error(self):
        """Test invalid param format raises error."""
        args = Namespace(params=["notakeyvalue"])
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_param(args)
        assert "Invalid parameter format" in str(exc_info.value)

    def test_unknown_param_raises_error(self):
        """Test unknown param key raises error."""
        args = Namespace(params=["foo=bar"])
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_param(args)
        assert "Unknown parameter" in str(exc_info.value)

    def test_unsupported_type_raises_error(self):
        """Test error for unsupported item types like Dashboard."""
        args = Namespace(params=["type=Dashboard"])
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_param(args)
        assert "Dashboard" in str(exc_info.value)
        assert "not searchable" in str(exc_info.value)

    def test_unknown_type_raises_error(self):
        """Test error for unknown item types."""
        args = Namespace(params=["type=InvalidType"])
        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._parse_type_param(args)
        assert "InvalidType" in str(exc_info.value)
        assert "Unknown item type" in str(exc_info.value)


class TestDisplayItems:
    """Tests for _display_items function."""

    @patch("fabric_cli.utils.fab_ui.print_output_format")
    def test_display_items_table(self, mock_print_format):
        """Test displaying items in table mode."""
        args = Namespace(long=False, output_format="text")
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
        """Test displaying items with long flag."""
        args = Namespace(long=True, output_format="text")
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


class TestRaiseOnError:
    """Tests for _raise_on_error function."""

    def test_success_response(self):
        """Test successful response does not raise."""
        response = MagicMock()
        response.status_code = 200
        fab_find._raise_on_error(response)  # Should not raise

    def test_error_response_raises_fabric_cli_error(self):
        """Test error response raises FabricCLIError."""
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
        """Test error response with non-JSON body."""
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"

        with pytest.raises(FabricCLIError) as exc_info:
            fab_find._raise_on_error(response)

        assert "Catalog search failed" in str(exc_info.value)


class TestFindCommandline:
    """Tests for _find_commandline function."""

    @patch("fabric_cli.utils.fab_ui.print_output_format")
    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.client.fab_api_catalog.catalog_search")
    def test_displays_results(self, mock_search, mock_print_grey, mock_print_format):
        """Test command-line mode displays results."""
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(SAMPLE_RESPONSE_SINGLE)
        mock_search.return_value = response

        args = Namespace(long=False, output_format="text")
        payload = {"search": "test", "pageSize": 1000}

        fab_find._find_commandline(args, payload)

        mock_search.assert_called_once()
        mock_print_format.assert_called_once()

    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.client.fab_api_catalog.catalog_search")
    def test_empty_results(self, mock_search, mock_print_grey):
        """Test command-line mode with no results."""
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(SAMPLE_RESPONSE_EMPTY)
        mock_search.return_value = response

        args = Namespace(long=False, output_format="text")
        payload = {"search": "nothing", "pageSize": 1000}

        fab_find._find_commandline(args, payload)

        mock_print_grey.assert_called_with("No items found.")


class TestFindInteractive:
    """Tests for _find_interactive function."""

    @patch("builtins.input", return_value="")
    @patch("fabric_cli.utils.fab_ui.print_output_format")
    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.client.fab_api_catalog.catalog_search")
    def test_pages_through_results(self, mock_search, mock_print_grey, mock_print_format, mock_input):
        """Test interactive mode pages through multiple responses."""
        # First page has continuation token, second page does not
        page1 = MagicMock()
        page1.status_code = 200
        page1.text = json.dumps(SAMPLE_RESPONSE_WITH_RESULTS)

        page2 = MagicMock()
        page2.status_code = 200
        page2.text = json.dumps(SAMPLE_RESPONSE_SINGLE)

        mock_search.side_effect = [page1, page2]

        args = Namespace(long=False, output_format="text")
        payload = {"search": "sales", "pageSize": 50}

        fab_find._find_interactive(args, payload)

        assert mock_search.call_count == 2
        assert mock_print_format.call_count == 2
        mock_input.assert_called_once_with("Press any key to continue... (Ctrl+C to stop)")

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    @patch("fabric_cli.utils.fab_ui.print_output_format")
    @patch("fabric_cli.utils.fab_ui.print_grey")
    @patch("fabric_cli.client.fab_api_catalog.catalog_search")
    def test_ctrl_c_stops_pagination(self, mock_search, mock_print_grey, mock_print_format, mock_input):
        """Test Ctrl+C stops pagination."""
        response = MagicMock()
        response.status_code = 200
        response.text = json.dumps(SAMPLE_RESPONSE_WITH_RESULTS)
        mock_search.return_value = response

        args = Namespace(long=False, output_format="text")
        payload = {"search": "sales", "pageSize": 50}

        fab_find._find_interactive(args, payload)

        # Should only fetch one page (stopped by Ctrl+C)
        assert mock_search.call_count == 1
        assert mock_print_format.call_count == 1


class TestSearchableItemTypes:
    """Tests for item type lists."""

    def test_searchable_types_excludes_unsupported(self):
        """Test SEARCHABLE_ITEM_TYPES excludes unsupported types."""
        assert "Dashboard" not in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Dataflow" in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Report" in fab_find.SEARCHABLE_ITEM_TYPES
        assert "Lakehouse" in fab_find.SEARCHABLE_ITEM_TYPES
