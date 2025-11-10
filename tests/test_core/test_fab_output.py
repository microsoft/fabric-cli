# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for FabricCLIOutput."""

import json
from enum import Enum

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_output import FabricCLIOutput, OutputResult, OutputStatus


class TestEnum(str, Enum):
    A = "a"
    B = "b"
    C = "c"

def test_output_result_json_success():
    """Test OutputResult successfully handles properties and json conversion."""
    # Test 1: With all fields
    result = OutputResult(
        data={"test": "data"},
        hidden_data=[TestEnum.A, TestEnum.B],
        message="test message",
    )

    assert result.data == [{"test": "data"}]
    assert result.hidden_data == ["a", "b"]
    assert result.message == "test message"

    result_dict = result.to_dict()
    assert result_dict["data"] == [{"test": "data"}]
    assert result_dict["hidden_data"] == ["a", "b"]
    assert result_dict["message"] == "test message"

    # Test 2: Without optional fields
    result = OutputResult(data={"test": "data"}, hidden_data=None, message=None)

    assert result.data == [{"test": "data"}]
    assert result.hidden_data is None
    assert result.message is None

    result_dict = result.to_dict()
    assert result_dict["data"] == [{"test": "data"}]
    assert "hidden_data" not in result_dict
    assert "message" not in result_dict

    # Test 3: With empty data
    result = OutputResult(data=[], hidden_data=None, message=None)
    assert result.get_data_keys() == []

    # Test 4: With data containing keys
    result = OutputResult(
        data=[{"key1": "val1", "key2": "val2"}], hidden_data=None, message=None
    )
    assert set(result.get_data_keys()) == {"key1", "key2"}

def test_fabric_cli_output_json_success():
    """Test output successfully converts to JSON with different fields."""
    # Test 1: With data and hidden_data, without message
    output = FabricCLIOutput(
        command="test",
        status=OutputStatus.Success,
        data={"test": "data"},
        hidden_data=[TestEnum.A, TestEnum.B],
    )
    json_output = json.loads(output.to_json())
    assert "message" not in json_output["result"]
    assert json_output["command"] == "test"
    assert json_output["result"]["data"] == [{"test": "data"}]
    assert json_output["result"]["hidden_data"] == ["a", "b"]

    # Test 2: With only message
    output = FabricCLIOutput(
        command="test", status=OutputStatus.Success, message="test message"
    )
    json_output = json.loads(output.to_json())
    assert json_output["result"]["message"] == "test message"
    assert "data" not in json_output["result"]
    assert "hidden_data" not in json_output["result"]

def test_fabric_cli_output_json_failure():
    """Test output to JSON fails with invalid data."""
    # Setup
    output = FabricCLIOutput(
        command="test", output_format_type=None, data=object()  # Un-serializable object
    )

    # Verify
    from fabric_cli.core.fab_exceptions import FabricCLIError

    with pytest.raises(FabricCLIError) as ex:
        output.to_json()
    ex.value.status_code == fab_constant.WARNING_INVALID_JSON_FORMAT
    ex.value.message == fab_constant.ERROR_INVALID_JSON


def test_output_result_success():
    # Test 1: with None values
    result = OutputResult(data=None, hidden_data=None, message=None)
    assert result.data is None
    assert result.hidden_data is None
    assert result.message is None

    # Test 2: hidden_data with empty list
    result = OutputResult(data={"test": "data"}, hidden_data=[], message=None)
    assert result.hidden_data == []

    # Test 3: hidden_data sorting
    result = OutputResult(
        data={"test": "data"},
        hidden_data=[TestEnum.C, TestEnum.A, TestEnum.B],
        message=None,
    )
    assert result.hidden_data == ["a", "b", "c"]

def test_fabric_cli_output_show_headers():
    """Test show_headers property is handled correctly."""
    # Test with show_headers True
    output = FabricCLIOutput(data={"test": "data"}, show_headers=True)
    assert output.show_headers is True

    # Test with show_headers False (default)
    output = FabricCLIOutput(data={"test": "data"})
    assert output.show_headers is False

def test_fabric_cli_output_format_type_success():
    """Test output_format_type property is handled successfully."""
    # Test with format type set
    output = FabricCLIOutput(output_format_type="json")
    assert output.output_format_type == "json"

    # Test with no format type
    output = FabricCLIOutput()
    assert output.output_format_type is None


def test_fabric_cli_output_error_handling_success():
    """Test error handling is successful with different status conditions."""
    # Test with failed status and error code
    output = FabricCLIOutput(
        status=OutputStatus.Failure,
        error_code="TEST_ERROR",
        message="Test error message",
    )

    json_output = json.loads(output.to_json())
    assert json_output["status"] == OutputStatus.Failure
    assert json_output["result"]["error_code"] == "TEST_ERROR"
    assert json_output["result"]["message"] == "Test error message"

    # Test error code not present in success status
    output = FabricCLIOutput(
        status=OutputStatus.Success,
        error_code="TEST_ERROR",  # Should be ignored in success status
    )
    json_output = json.loads(output.to_json())
    assert "error_code" not in json_output

    # Test default error_code when no error code is provided in failed status
    output = FabricCLIOutput(
        status=OutputStatus.Failure,
        message="Test error message",
    )

    json_output = json.loads(output.to_json())
    assert json_output["result"]["error_code"] == "UnexpectedError"


def test_fabric_cli_output_show_key_value_list_success():
    """Test show_key_value_list property is handled correctly."""
    # Test with show_key_value_list True
    output = FabricCLIOutput(data={"test": "data"}, show_key_value_list=True)
    assert output.show_key_value_list is True

    # Test with show_key_value_list False (default)
    output = FabricCLIOutput(data={"test": "data"})
    assert output.show_key_value_list is False

    # Test with explicit False
    output = FabricCLIOutput(data={"test": "data"}, show_key_value_list=False)
    assert output.show_key_value_list is False
