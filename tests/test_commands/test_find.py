# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the find command — e2e (VCR) tests."""

import json
import time

import pytest

from fabric_cli.core.fab_types import ItemType
from fabric_cli.errors import ErrorMessages
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
        assert (
            match_found
        ), f"Expected strings {strings} to {'all be present together' if require_all_in_same_args else 'be present'} in mock calls, but not found."
    else:
        assert (
            not match_found
        ), f"Expected strings {strings} to {'not all be present together' if require_all_in_same_args else 'not be present'} in mock calls, but found."


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
        monkeypatch.setattr(
            "builtins.input", lambda *args: (_ for _ in ()).throw(EOFError)
        )

    def test_find_with_type_filter_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Lakehouse, search with -P type=Lakehouse, verify found."""
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(f"find '{lakehouse.display_name}' -P type=Lakehouse")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [lakehouse.display_name, "Lakehouse"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_basic_search_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Notebook, search by name with type filter, verify in results and summary."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(f"find '{notebook.display_name}' -P type=Notebook")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )
        output = " ".join(str(c) for c in mock_questionary_print.call_args_list)
        assert "found" in output

    def test_find_type_case_insensitive_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Lakehouse, search with lowercase type=lakehouse."""
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(f"find '{lakehouse.display_name}' -P type=lakehouse")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [lakehouse.display_name, "Lakehouse"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_with_long_output_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Notebook, search with -l, verify IDs in output."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(f"find '{notebook.display_name}' -l")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, "id"],
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
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_time_sleep,
    ):
        """Create a Notebook, search excluding Notebook type."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        mock_print_grey.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(f"find '{notebook.display_name}' -P type!=Notebook")

        all_output = " ".join(str(c) for c in mock_questionary_print.call_args_list)
        assert "Notebook" not in all_output or "No items found" in " ".join(
            str(c) for c in mock_print_grey.call_args_list
        )

    def test_find_ne_multi_type_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        mock_time_sleep,
    ):
        """Create a Notebook, search excluding Notebook and Report."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        mock_print_grey.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(
            f"find '{notebook.display_name}' -P type!=[Notebook,Report]"
        )

        all_output = " ".join(str(c) for c in mock_questionary_print.call_args_list)
        assert "Notebook" not in all_output or "No items found" in " ".join(
            str(c) for c in mock_print_grey.call_args_list
        )

    def test_find_unknown_type_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        """Search with unknown type shows error."""
        cli_executor.exec_command("find 'data' -P type=FakeType123")

        error_output = str(mock_fab_ui_print_error.call_args_list)
        assert ErrorMessages.Find.unrecognized_type("FakeType123", "") in error_output

    def test_find_unsupported_type_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        """Search with unsupported type shows error."""
        cli_executor.exec_command("find 'data' -P type=Dashboard")

        error_output = str(mock_fab_ui_print_error.call_args_list)
        assert ErrorMessages.Common.type_not_supported("Dashboard") in error_output

    def test_find_invalid_param_format_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        """Search with malformed -P value shows error."""
        cli_executor.exec_command("find 'data' -P notakeyvalue")

        error_output = str(mock_fab_ui_print_error.call_args_list)
        assert (
            ErrorMessages.Common.invalid_parameter_format("notakeyvalue")
            in error_output
        )

    def test_find_unsupported_param_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        """Search with unknown param key shows error."""
        cli_executor.exec_command("find 'data' -P foo=bar")

        error_output = str(mock_fab_ui_print_error.call_args_list)
        assert ErrorMessages.Common.unsupported_parameter("foo") in error_output

    def test_find_unsupported_param_ne_failure(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        """Search with unknown param key using != shows error."""
        cli_executor.exec_command("find 'data' -P foo!=bar")

        error_output = str(mock_fab_ui_print_error.call_args_list)
        assert ErrorMessages.Common.unsupported_parameter("foo") in error_output

    def test_find_with_jmespath_query_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Notebook, search with JMESPath query."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(
            f"""find '{notebook.display_name}' -q "[?type=='Notebook']" """
        )

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_multi_type_eq_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Notebook, search for Notebook and Report types."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(
            f"find '{notebook.display_name}' -P type=[Notebook,Report]"
        )

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            ["Notebook"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_json_output_success(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_time_sleep,
    ):
        """Create a Notebook, search with JSON output."""
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()
        time.sleep(30)

        cli_executor.exec_command(
            f"find '{notebook.display_name}' --output_format json"
        )

        mock_questionary_print.assert_called()
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


class TestFindTruncation:
    """Tests for column truncation with long display names.

    Uses handcrafted VCR cassettes (not recordable) because the test harness
    normalizes display names to short monikers during recording, which would
    defeat the purpose of testing truncation on long names.
    """

    LONG_NAME = "A" * 256

    @pytest.fixture(autouse=True)
    def _skip_on_record(self, vcr_mode):
        if vcr_mode == "all":
            pytest.skip("Synthetic cassettes — not recordable")

    @pytest.fixture(autouse=True)
    def _mock_input(self, monkeypatch):
        """Raise EOFError on input() to stop pagination after the first page."""
        monkeypatch.setattr(
            "builtins.input", lambda *args: (_ for _ in ()).throw(EOFError)
        )

    def test_find_long_name_truncated_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Text output truncates a 256-char display name."""
        cli_executor.exec_command(f"find 'longname'")

        mock_questionary_print.assert_called()
        full_name_found = any(
            self.LONG_NAME in str(call)
            for call in mock_questionary_print.call_args_list
        )
        assert not full_name_found, "Full 256-char name should be truncated in text output"
        _assert_strings_in_mock_calls(
            ["…"],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_long_name_details_not_truncated_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """Detail mode (-l) shows the full 256-char name without truncation."""
        cli_executor.exec_command(f"find 'longname' -l")

        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [self.LONG_NAME],
            should_exist=True,
            mock_calls=mock_questionary_print.call_args_list,
        )

    def test_find_long_name_json_not_truncated_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
    ):
        """JSON output preserves the full 256-char name without truncation."""
        cli_executor.exec_command(f"find 'longname' --output_format json")

        mock_questionary_print.assert_called()
        json_output = None
        for call in mock_questionary_print.call_args_list:
            try:
                json_output = json.loads(call.args[0])
                break
            except (json.JSONDecodeError, IndexError):
                continue
        assert json_output is not None, "No valid JSON found in output"
        names = [item.get("name", "") for item in json_output["result"]["data"]]
        assert self.LONG_NAME in names, "Full 256-char name not found in JSON output"


class TestFindPagination:
    """E2E tests for pagination, JMESPath filtering, and edge cases.

    Uses handcrafted VCR cassettes (not recordable) to exercise
    the full CLI pipeline through cli_executor → find → _find_interactive.
    """

    @pytest.fixture(autouse=True)
    def _skip_on_record(self, vcr_mode):
        if vcr_mode == "all":
            pytest.skip("Synthetic cassettes — not recordable")

    def test_find_single_page_no_prompt_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        monkeypatch,
    ):
        """Single page of results — items displayed, no pagination prompt."""
        prompt_called = False

        def _fail_on_prompt(*args):
            nonlocal prompt_called
            prompt_called = True

        monkeypatch.setattr("builtins.input", _fail_on_prompt)

        cli_executor.exec_command("find 'singlepage'")

        assert not prompt_called, "Prompt should not appear for single page"
        output = " ".join(str(c) for c in mock_questionary_print.call_args_list)
        assert "NB-0" in output
        assert "3 items found" in output

    def test_find_multi_page_interactive_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        monkeypatch,
    ):
        """Two pages — user presses Enter to continue, sees all items."""
        monkeypatch.setattr("builtins.input", lambda *a: "")

        cli_executor.exec_command("find 'multipage'")

        output = " ".join(str(c) for c in mock_questionary_print.call_args_list)
        assert "NB-P1-0" in output
        assert "NB-P2-0" in output
        assert "5 items found" in output

    def test_find_no_items_display_after_jmespath_filters_all_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        mock_print_grey,
        monkeypatch,
    ):
        """JMESPath filter empties all results → 'No items found.'"""
        monkeypatch.setattr(
            "builtins.input", lambda *a: (_ for _ in ()).throw(EOFError)
        )

        cli_executor.exec_command(
            """find 'jmespathempty' -q "[?type=='Lakehouse']" """
        )

        grey_output = " ".join(str(c) for c in mock_print_grey.call_args_list)
        assert "No items found" in grey_output

    def test_find_jmespath_skips_empty_page_success(
        self,
        cli_executor: CLIExecutor,
        mock_questionary_print,
        monkeypatch,
    ):
        """Three pages — middle page emptied by JMESPath, prompt skipped for it."""
        prompt_count = 0

        def _count_prompt(*a):
            nonlocal prompt_count
            prompt_count += 1
            return ""

        monkeypatch.setattr("builtins.input", _count_prompt)

        cli_executor.exec_command(
            """find 'jmespathskip' -q "[?type=='Notebook']" """
        )

        # Prompt shown once (after page 1 with items), NOT after page 2 (empty)
        assert prompt_count == 1, f"Expected 1 prompt, got {prompt_count}"
        output = " ".join(str(c) for c in mock_questionary_print.call_args_list)
        assert "NB-" in output
        assert "LH-" not in output
