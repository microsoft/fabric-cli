# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import platform
from argparse import Namespace
from enum import Enum
from typing import Callable, Optional

import pytest

import fabric_cli.core.fab_state_config as state_config
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_output import FabricCLIOutput, OutputStatus
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as ui


class OutputType(Enum):
    STDOUT = "stdout"
    STDERR = "stderr"


def verify_output_stream(capsys: pytest.CaptureFixture, output_type: OutputType) -> None:
    """Helper to verify output appears in the correct stream.

    Args:
        capsys: Pytest fixture for capturing stdout/stderr
        output_type: Which stream to check (stdout or stderr)
    """
    captured = capsys.readouterr()
    if output_type == OutputType.STDOUT:
        assert captured.out != ""
        assert captured.err == ""
    else:  # STDERR
        assert captured.out == ""
        assert captured.err != ""


def test_get_common_style():
    from questionary import Style

    # Test that the function returns a Style object
    style = ui.get_common_style()
    assert style is not None


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Failed to run on windows with vscode - no real console",
)
def test_print_success(capsys):
    """Test standard print function (stdout only)."""
    with pytest.raises(AttributeError):
        ui.print(None)

    test_msg = "Hello from standard print"
    ui.print(test_msg)
    verify_output_stream(capsys, OutputType.STDOUT)


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Failed to run on windows with vscode - no real console",
)
def test_print_fabric_success(capsys):
    """Test fabric print function (stdout only)."""
    with pytest.raises(AttributeError):
        ui.print_fabric(None)

    test_msg = "In color fabric text"
    ui.print_fabric(test_msg)
    verify_output_stream(capsys, OutputType.STDOUT)


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Failed to run on windows with vscode - no real console",
)
def test_print_grey_success(capsys):
    """Test grey print function (configurable output stream)."""

    test_msg = "Standard grey output"
    ui.print_grey(test_msg, to_stderr=False)
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test stderr
    stderr_msg = "Grey output to stderr"
    ui.print_grey(stderr_msg)
    verify_output_stream(capsys, OutputType.STDERR)


def test_print_done_success(capsys):
    """Test done function (stdout with HTML escaping)."""
    with pytest.raises(AttributeError):
        ui.print_done(None)

    # Test HTML escaping
    ui.print_done("alert('test')")
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test regular message
    ui.print_done("Operation completed")
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_warning_success(capsys):
    """Test warning function (stderr with HTML escaping)."""
    with pytest.raises(AttributeError):
        ui.print_warning(None)

    # Test HTML escaping
    ui.print_warning("alert('test')")
    verify_output_stream(capsys, OutputType.STDERR)

    # Test with command
    ui.print_warning("warning message", command="test-cmd")
    verify_output_stream(capsys, OutputType.STDERR)

def test_print_error_success(capsys):
    """Test error function (stdout with HTML escaping)."""
    # Test HTML escaping
    ui._print_error_format_text("alert('test')")
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test with command
    ui._print_error_format_text("error message", command="test-cmd")
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test with FabricCLIError
    custom_error = FabricCLIError("error", fab_constant.ERROR_ALREADY_EXISTS)
    ui._print_error_format_text(custom_error)
    verify_output_stream(capsys, OutputType.STDOUT)

    ui._print_error_format_text(custom_error, command="test-cmd")
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_info_success(capsys):
    """Test info function (stderr with HTML escaping)."""
    with pytest.raises(AttributeError):
        ui.print_info(None)

    # Test HTML escaping
    ui.print_info("alert")
    verify_output_stream(capsys, OutputType.STDERR)

    # Test with command
    ui.print_info("info message", command="test-cmd")
    verify_output_stream(capsys, OutputType.STDERR)


def test_print_progress_success(capsys):
    """Test progress function (always writes to stderr)."""
    # Test with just text
    ui.print_progress("Processing files")
    verify_output_stream(capsys, OutputType.STDERR)

    # Test with progress percentage
    ui.print_progress("Uploading", progress=75)
    verify_output_stream(capsys, OutputType.STDERR)

    # Test with None
    ui.print_progress(None)
    verify_output_stream(capsys, OutputType.STDERR)


def test_display_help_success(capsys):
    """Test help display function (stdout)."""
    commands = {
        "Commands": {
            "load": "Load data into a table in the lakehouse.",
            "optimize": "Optimize a Delta table.",
            "schema": "Display the schema of a Delta table.",
            "vacuum": "Vacuum a Delta table by removing old files.",
        },
    }

    # Test with regular commands
    ui.display_help(commands)
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test with custom header
    ui.display_help(commands, custom_header=fab_constant.COMMAND_TABLES_DESCRIPTION)
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test edge cases
    ui.display_help([])
    verify_output_stream(capsys, OutputType.STDOUT)

    ui.display_help(None)
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_entries_unix_style_success(capsys):
    """Test printing entries in unix-style format (uses stderr)."""
    # Test with basic entries and fields
    entries = [{"row": 1, "name": "test"}, {"row": 2, "name": "test_2"}]
    fields = ["row", "name"]

    # Test with header
    ui.print_entries_unix_style(entries, fields, header=True)
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test without header
    ui.print_entries_unix_style(entries, fields, header=False)
    verify_output_stream(capsys, OutputType.STDOUT)

    # Test empty entries
    entries = []
    ui.print_entries_unix_style(entries, fields, header=True)
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_error_format_text_to_stdout_success(mock_fab_set_state_config, capsys):
    # Setup
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "text")

    err = FabricCLIError("print error format text", fab_constant.ERROR_NOT_SUPPORTED)

    ui.print_output_error(err, command="command")

    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_error_format_json_to_stdout_success(
    mock_questionary_print, mock_fab_set_state_config
):
    """Test error format in JSON mode (verifies both JSON structure and output stream)."""
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")
    err = FabricCLIError("print error format json", fab_constant.ERROR_NOT_SUPPORTED)
    ui.print_output_error(err, command="command")

    output = json.loads(mock_questionary_print.mock_calls[0].args[0])

    # Check base level fields
    assert output["status"] == OutputStatus.Failure
    assert output["command"] == "command"
    assert output["result"]["message"] == "print error format json"
    assert output["result"]["error_code"] == fab_constant.ERROR_NOT_SUPPORTED


def test_print_error_format_text_success(mock_fab_set_state_config, capsys):
    """Test error format in text mode (verifies both text structure and output stream)."""
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "text")
    err = FabricCLIError("print error format text", fab_constant.ERROR_NOT_SUPPORTED)
    ui.print_output_error(err, command="test-command")

    output = capsys.readouterr().out
    assert "x test-command: [NotSupported] print error format text" in output


def test_print_error_format_json_output_in_stdout(mock_fab_set_state_config, capsys):
    """Test error format in JSON mode (verifies both JSON structure and output stream)."""
    # Set output format to json
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")
    err = FabricCLIError("print error format json", fab_constant.ERROR_NOT_SUPPORTED)
    ui.print_output_error(err, command="command")

    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_error_format_failure(mock_fab_set_state_config):
    # Setup
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "test")
    err = FabricCLIError("error", fab_constant.ERROR_ALREADY_EXISTS)
    with pytest.raises(FabricCLIError) as ex:
        ui.print_output_error(err, command="command")
    ex.value.message == "Output format test not supported"
    ex.value.status_code == fab_constant.ERROR_NOT_SUPPORTED


def test_print_output_format_json_success(
    mock_questionary_print, mock_fab_set_state_config
):
    def assert_json_output(expected, actual, show_all=False):
        if expected.result.data:
            assert len(actual["result"]["data"]) > 0
            for i, item in enumerate(expected.result.data):
                assert actual["result"]["data"][i] == item
        else:
            assert "data" not in actual["result"]

        for key, value in actual.items():
            if key != "result" and key != "timestamp":
                assert value == getattr(expected, f"_{key}")

        assert "error_code" not in actual
        if show_all:
            assert "hidden_data" in actual["result"]
            assert actual["result"]["hidden_data"] == expected.result.hidden_data
        else:
            assert "hidden_data" not in actual["result"]

        if expected.result.message:
            assert actual["result"]["message"] == expected.result.message
        else:
            assert "message" not in actual["result"]

    # Test 1: With data and hidden_data, without message
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")
    output_mock = FabricCLIOutput(
        command="test",
        output_format_type="json",
        data=[{"name": "test1"}, {"name": "test2"}],
        hidden_data=["hidden1", "hidden2"],
    )

    args = Namespace(output_format="json", command="test")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        hidden_data=["hidden1", "hidden2"],
    )

    mock_questionary_print.assert_called_once()
    json_output = json.loads(mock_questionary_print.mock_calls[0].args[0])
    assert_json_output(output_mock, json_output, show_all=True)
    assert "message" not in json_output["result"]
    mock_questionary_print.reset_mock()

    # Test 2: With only message
    output_mock = FabricCLIOutput(
        command="test",
        output_format_type="json",
        message="Test message",
        status=OutputStatus.Success,
    )
    ui.print_output_format(args, message="Test message")
    mock_questionary_print.assert_called_once()
    json_output = json.loads(mock_questionary_print.mock_calls[0].args[0])
    assert_json_output(output_mock, json_output)
    mock_questionary_print.reset_mock()


def test_print_output_format_json_print_to_stdout_success(
    mock_fab_set_state_config, capsys
):
    # Mock get_config
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")

    # Test with --output_format json flag
    args = Namespace(output_format="json", command="test")
    ui.print_output_format(
        args, data=[{"name": "test1"}, {"name": "test2"}], message="Test message"
    )

    # Verify output streams
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_output_with_json_payload_to_stdout_success(capsys):
    """Test API response printing (always to stderr)."""
    # Test with JSON payload
    _payload = {
        "status_code": 200,
        "text": '{"key": "value"}',
        "headers": {"header": "value"},
    }
    args = Namespace(output_format="json")
    ui.print_output_format(args, data=_payload)
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_output_with_str_payload_to_stdout_success(capsys):
    """Test API response printing (always to stderr)."""
    args = Namespace(output_format="text")
    # Test with string payload
    _payload_str = "guid"
    ui.print_output_format(args, data=_payload_str)
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_output_format_text_success(
    mock_questionary_print, mock_fab_set_state_config
):
    # Setup
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "text")
    # Test 1: Basic text output without headers
    args = Namespace(command="test")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )
    assert mock_questionary_print.call_count == 1
    assert (
        mock_questionary_print.mock_calls[0].args[0]
        == '[\n  {\n    "name": "test1"\n  },\n  {\n    "name": "test2"\n  }\n]'
    )

    mock_questionary_print.reset_mock()

    # Test 2: Text output with hidden data
    args = Namespace(command="ls")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
        hidden_data=["hidden1", "hidden2"],
    )

    assert mock_questionary_print.call_count == 5
    assert mock_questionary_print.mock_calls[3].args[0] == "hidden1"
    assert mock_questionary_print.mock_calls[4].args[0] == "hidden2"

    mock_questionary_print.reset_mock()

    # Test 3: Text output without output_format_type
    args = Namespace(command="test", output_format_type=None)
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )
    assert mock_questionary_print.call_count == 1
    mock_questionary_print.reset_mock()

    # Test 4: Text output with show_headers=True
    ui.print_output_format(
        args,
        data=[{"name": "test1", "id": "test_id1"}, {"name": "test2", "id": "test_id2"}],
        message="Test message",
        hidden_data=["hidden1", "hidden2"],
        show_headers=True,
    )
    # assert there  is headers
    assert "name" in mock_questionary_print.mock_calls[0].args[0]
    assert "id" in mock_questionary_print.mock_calls[0].args[0]
    # assert hidden folders are displayed
    assert mock_questionary_print.mock_calls[5].args[0] == "hidden1"
    assert mock_questionary_print.mock_calls[6].args[0] == "hidden2"

    mock_questionary_print.reset_mock()

    # Test 5: Text output with subcommand ls
    args.test_subcommand = "ls"
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )
    # assert there is no headers
    assert "name" not in mock_questionary_print.mock_calls[0].args[0]
    assert "test1" in mock_questionary_print.mock_calls[0].args[0]
    assert "test2" in mock_questionary_print.mock_calls[1].args[0]


def test_print_output_format_text_print_to_stdout_success(
    mock_fab_set_state_config, capsys
):
    # set output format config to text
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "text")

    # Test output with show_headers=True
    args = Namespace()
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
        show_headers=True,
    )
    # Verify text result is printed to stdout
    verify_output_stream(capsys, OutputType.STDOUT)


def test_print_output_format_with_F_flag(
    mock_questionary_print, mock_fab_set_state_config
):
    # set output format config to text
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "text")

    # Test --output_format json flag overrides config
    args = Namespace(command="test-json", output_format="json")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )

    # Verify json output format
    output = json.loads(mock_questionary_print.mock_calls[0].args[0])
    assert isinstance(output, dict)
    assert "result" in output
    assert "data" in output["result"]
    assert isinstance(output["result"]["data"], list)
    assert len(output["result"]["data"]) == 2
    assert all(isinstance(item, dict) for item in output["result"]["data"])
    mock_questionary_print.reset_mock()

    # set output format config to json
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")

    # Test --output_format text flag overrides config when config is json
    args = Namespace(command="test-text", output_format="text")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )

    # Verify text output format
    assert mock_questionary_print.call_count == 1
    assert all(
        isinstance(call.args[0], str) for call in mock_questionary_print.mock_calls
    )
    assert not any(
        "result" in call.args[0] for call in mock_questionary_print.mock_calls
    )
    assert (
        mock_questionary_print.mock_calls[0].args[0]
        == '[\n  {\n    "name": "test1"\n  },\n  {\n    "name": "test2"\n  }\n]'
    )


def test_print_output_format_with_force_output_success(
    mock_questionary_print, mock_fab_set_state_config
):
    # Test 1: output_format_type=json overrides config text format
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "text")

    args = Namespace(command="test-json", output_format="json")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )

    # Verify json output format
    output = json.loads(mock_questionary_print.mock_calls[0].args[0])
    assert isinstance(output, dict)
    assert "result" in output
    assert "data" in output["result"]
    assert isinstance(output["result"]["data"], list)
    assert len(output["result"]["data"]) == 2
    assert all(isinstance(item, dict) for item in output["result"]["data"])

    mock_questionary_print.reset_mock()

    # Test 2: output_format_type=text overrides config json format
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")
    args = Namespace(command="test-text", output_format="text")
    ui.print_output_format(
        args,
        data=[{"name": "test1"}, {"name": "test2"}],
        message="Test message",
    )

    # Verify text output format
    assert mock_questionary_print.call_count == 1
    assert all(
        isinstance(call.args[0], str) for call in mock_questionary_print.mock_calls
    )
    assert not any(
        "result" in call.args[0] for call in mock_questionary_print.mock_calls
    )
    assert (
        mock_questionary_print.mock_calls[0].args[0]
        == '[\n  {\n    "name": "test1"\n  },\n  {\n    "name": "test2"\n  }\n]'
    )


def test_print_output_format_failure(mock_fab_set_state_config):
    # Mock get_config to return an unsupported format
    mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "test")
    args = Namespace(command="test")

    # Test with unsupported format
    with pytest.raises(FabricCLIError) as ex:
        ui.print_output_format(args, data=[{"name": "test1"}], message="Test message")

    # Verify exception properties
    assert ex.value.message == "Output format test not supported"
    assert ex.value.status_code == fab_constant.ERROR_NOT_SUPPORTED


def test_print_output_format_text_no_result_failure():
    args = Namespace(command="test", output_format="text")

    # Execute command
    with pytest.raises(FabricCLIError) as excinfo:
        ui.print_output_format(args)

    # Assert
    assert excinfo.value.message == ErrorMessages.Common.invalid_result_format()
    assert excinfo.value.status_code == constant.ERROR_INVALID_INPUT


def test_print_version_seccess():
    ui.print_version()
    ui.print_version(None)
    # Just verify it doesn't crash - output verification would require mocking
