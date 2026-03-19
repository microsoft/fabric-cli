# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the find command — unit tests and e2e (VCR) tests."""

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.commands.find import fab_find
from fabric_cli.core.fab_exceptions import FabricCLIError
from tests.test_commands.commands_parser import CLIExecutor


def _assert_strings_in_mock_calls(
    strings: list[str],
    should_exist: bool,
    mock_calls,
    require_all_in_same_args: bool = False,
):
    """Assert that specified strings are present or absent in mock calls."""
    if require_all_in_same_args:
        match_found = any(
            all(string in str(call) for string in strings) for call in mock_calls
        )
    else:
        match_found = all(
            any(string in str(call) for call in mock_calls) for string in strings
        )

    if should_exist:
        assert match_found, f"Expected strings {strings} to {'all be present together' if require_all_in_same_args else 'be present'} in mock calls, but not found."
    else:
        assert not match_found, f"Expected strings {strings} to {'not all be present together' if require_all_in_same_args else 'not be present'} in mock calls, but found."


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


class TestParseTypeFromParams:
    """Tests for _parse_type_from_params function."""

    def test_no_params(self):
        args = Namespace(params=None)
        assert fab_find._parse_type_from_params(args) is None

    def test_empty_params(self):
        args = Namespace(params="")
        assert fab_find._parse_type_from_params(args) is None

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

    def test_find_basic_search_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search returns results and prints output."""
        cli_executor.exec_command("find 'data'")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["name", "type", "workspace"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_with_type_filter_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with -P type= returns only matching types."""
        cli_executor.exec_command("find 'data' -P type=Lakehouse")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Lakehouse"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_type_case_insensitive_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with lowercase type=lakehouse returns same results."""
        cli_executor.exec_command("find 'data' -P type=lakehouse")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Lakehouse"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_with_long_output_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with -l includes IDs in output."""
        cli_executor.exec_command("find 'data' -l")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["id"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_no_results_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
    ):
        """Search for nonexistent term shows 'No items found'."""
        cli_executor.exec_command("find 'xyznonexistent98765zzz'")

        grey_output = " ".join(str(c) for c in mock_print_grey.call_args_list)
        assert "No items found" in grey_output

    def test_find_with_ne_filter_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with type!=Dashboard excludes Dashboard items."""
        cli_executor.exec_command("find 'report' -P type!=Dashboard")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Type: Dashboard"],
            should_exist=False,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_ne_multi_type_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with type!=[Report,Notebook] excludes both types."""
        cli_executor.exec_command("find 'data' -P type!=[Report,Notebook]")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Type: Report"],
            should_exist=False,
            mock_calls=mock_questionary_print.call_args_list,
        )
        _assert_strings_in_mock_calls(
            ["Type: Notebook"],
            should_exist=False,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_unknown_type_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_fab_ui_print_error,
    ):
        """Search with unknown type shows error."""
        cli_executor.exec_command("find 'data' -P type=FakeType123")

        all_output = (
            str(mock_questionary_print.call_args_list)
            + str(mock_print_grey.call_args_list)
            + str(mock_fab_ui_print_error.call_args_list)
        )
        assert "FakeType123" in all_output
        assert "recognized item type" in all_output

    def test_find_unsupported_type_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_fab_ui_print_error,
    ):
        """Search with unsupported type shows error."""
        cli_executor.exec_command("find 'data' -P type=Dashboard")

        all_output = (
            str(mock_questionary_print.call_args_list)
            + str(mock_print_grey.call_args_list)
            + str(mock_fab_ui_print_error.call_args_list)
        )
        assert "Dashboard" in all_output
        assert "not supported" in all_output

    def test_find_invalid_param_format_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_fab_ui_print_error,
    ):
        """Search with malformed -P value shows error."""
        cli_executor.exec_command("find 'data' -P notakeyvalue")

        all_output = (
            str(mock_questionary_print.call_args_list)
            + str(mock_print_grey.call_args_list)
            + str(mock_fab_ui_print_error.call_args_list)
        )
        assert "Invalid parameter" in all_output

    def test_find_unsupported_param_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_fab_ui_print_error,
    ):
        """Search with unknown param key shows error."""
        cli_executor.exec_command("find 'data' -P foo=bar")

        all_output = (
            str(mock_questionary_print.call_args_list)
            + str(mock_print_grey.call_args_list)
            + str(mock_fab_ui_print_error.call_args_list)
        )
        assert "foo" in all_output
        assert "supported parameter" in all_output

    def test_find_unsupported_param_ne_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_fab_ui_print_error,
    ):
        """Search with unknown param key using != shows error."""
        cli_executor.exec_command("find 'data' -P foo!=bar")

        all_output = (
            str(mock_questionary_print.call_args_list)
            + str(mock_print_grey.call_args_list)
            + str(mock_fab_ui_print_error.call_args_list)
        )
        assert "foo" in all_output
        assert "supported parameter" in all_output

    def test_find_with_jmespath_query_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with -q JMESPath query filters results locally."""
        cli_executor.exec_command("""find 'data' -q "[?type=='Report']" """)

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Report"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_multi_type_eq_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with type=[Report,Lakehouse] returns both types."""
        cli_executor.exec_command("find 'data' -P type=[Report,Lakehouse]")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Report"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )
        _assert_strings_in_mock_calls(
            ["Lakehouse"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_json_output_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Search with --output_format json returns valid JSON."""
        cli_executor.exec_command("find 'data' --output_format json")

        mock_questionary_print.assert_called()
        # Find the JSON call (skip summary lines printed via print_grey → questionary.print)
        json_output = None
        for call in mock_questionary_print.call_args_list:
            try:
                json_output = json.loads(call.args[0])
                break
            except (json.JSONDecodeError, IndexError):
                continue
        assert json_output is not None, "No valid JSON found in output"
        assert "result" in json_output
        assert "data" in json_output["result"]
        assert len(json_output["result"]["data"]) > 0

    def test_find_search_summary_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
    ):
        """Search with results prints summary with item count."""
        cli_executor.exec_command("find 'data'")

        grey_output = " ".join(str(c) for c in mock_print_grey.call_args_list)
        assert "item(s) found" in grey_output
        assert "more available" in grey_output
