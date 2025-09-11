# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

from fabric_cli.utils.fab_cmd_job_utils import (
    wait_for_job_completion,
    validate_timeout_polling_interval,
)
from fabric_cli.utils.fab_http_polling_utils import DEFAULT_POLLING_INTERVAL
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core import fab_constant


@pytest.fixture
def default_job_args():
    return Namespace(
        ws_id="test-ws",
        item_id="test-item",
        command="test-command",
        output_format="json"
    )


@pytest.fixture
def mock_job_response():
    mock_response = Mock()
    mock_response.headers = {}
    return mock_response


def create_mock_response(status_code=200, status="Completed", headers=None, error=None):
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.headers = headers or {}
    
    response_data = {"status": status}
    if error:
        response_data["error"] = error
    
    mock_response.text = json.dumps(response_data)
    return mock_response


@patch('fabric_cli.utils.fab_cmd_job_utils.get_polling_interval')
@patch('fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance')
@patch('fabric_cli.utils.fab_cmd_job_utils.time.sleep')
def test_wait_for_job_completion_immediate_success(mock_sleep, mock_api, mock_get_polling_interval, default_job_args, mock_job_response):
    mock_get_polling_interval.return_value = DEFAULT_POLLING_INTERVAL
    mock_api.return_value = create_mock_response()
    
    wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, custom_polling_interval=None)
    
    assert mock_sleep.call_count == 1
    mock_get_polling_interval.assert_called_once_with({}, None)


@patch('fabric_cli.utils.fab_cmd_job_utils.get_polling_interval')
@patch('fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance')
@patch('fabric_cli.utils.fab_cmd_job_utils.time.sleep')
def test_wait_for_job_completion_with_custom_interval(mock_sleep, mock_api, mock_get_polling_interval, default_job_args, mock_job_response):
    mock_get_polling_interval.return_value = 15
    mock_api.return_value = create_mock_response()
    
    wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, custom_polling_interval=15)
    
    assert mock_sleep.call_count == 1
    sleep_calls = mock_sleep.call_args_list
    assert sleep_calls[0].args[0] == 15
    mock_get_polling_interval.assert_called_once_with({}, 15)


@patch('fabric_cli.utils.fab_cmd_job_utils.get_polling_interval')
@patch('fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance')
@patch('fabric_cli.utils.fab_cmd_job_utils.time.sleep')
def test_wait_for_job_completion_progress_then_complete(mock_sleep, mock_api, mock_get_polling_interval, default_job_args, mock_job_response):
    mock_get_polling_interval.side_effect = [DEFAULT_POLLING_INTERVAL, 45]
    
    mock_response_progress = create_mock_response(status="InProgress", headers={"Retry-After": "45"})
    mock_response_complete = create_mock_response()
    
    mock_api.side_effect = [mock_response_progress, mock_response_complete]
    
    wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, custom_polling_interval=None)
    
    assert mock_sleep.call_count == 2
    sleep_calls = mock_sleep.call_args_list
    assert sleep_calls[0].args[0] == DEFAULT_POLLING_INTERVAL
    assert sleep_calls[1].args[0] == 45
    assert mock_get_polling_interval.call_count == 2


@patch('fabric_cli.utils.fab_cmd_job_utils.get_polling_interval')
@patch('fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance')
@patch('fabric_cli.utils.fab_cmd_job_utils.time.sleep')
def test_wait_for_job_completion_failed_status(mock_sleep, mock_api, mock_get_polling_interval, default_job_args, mock_job_response):
    mock_get_polling_interval.return_value = DEFAULT_POLLING_INTERVAL
    mock_api.return_value = create_mock_response(status="Failed", error="Test error")
    
    wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, custom_polling_interval=None)
    
    assert mock_sleep.call_count == 1


@patch('fabric_cli.utils.fab_cmd_job_utils.get_polling_interval')
@patch('fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance')
@patch('fabric_cli.utils.fab_cmd_job_utils.time.sleep')
def test_wait_for_job_completion_timeout(mock_sleep, mock_api, mock_get_polling_interval, default_job_args, mock_job_response):
    mock_get_polling_interval.return_value = DEFAULT_POLLING_INTERVAL
    mock_api.return_value = create_mock_response(status="InProgress")
    
    with pytest.raises(TimeoutError):
        wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, timeout=5, custom_polling_interval=None)


@patch('fabric_cli.utils.fab_cmd_job_utils.get_polling_interval')
@patch('fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance')
@patch('fabric_cli.utils.fab_cmd_job_utils.time.sleep')
def test_wait_for_job_completion_cancelled_status(mock_sleep, mock_api, mock_get_polling_interval, default_job_args, mock_job_response):
    mock_get_polling_interval.return_value = DEFAULT_POLLING_INTERVAL
    mock_api.return_value = create_mock_response(status="Cancelled")
    
    wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, custom_polling_interval=None)
    
    assert mock_sleep.call_count == 1


def test_validate_timeout_polling_interval_equal_values_failure():
    args = Namespace(timeout=30, polling_interval=30)
    
    with pytest.raises(FabricCLIError) as exc_info:
        validate_timeout_polling_interval(args)
    
    assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert "Custom polling interval (30s) cannot be greater than or equal to timeout (30s)" in str(exc_info.value)


def test_validate_timeout_polling_interval_greater_failure():
    args = Namespace(timeout=20, polling_interval=30)
    
    with pytest.raises(FabricCLIError) as exc_info:
        validate_timeout_polling_interval(args)
    
    assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert "Custom polling interval (30s) cannot be greater than or equal to timeout (20s)" in str(exc_info.value)


def test_validate_timeout_polling_interval_valid_combination_success():
    args = Namespace(timeout=60, polling_interval=30)
    
    # Should not raise any exception
    validate_timeout_polling_interval(args)


def test_validate_timeout_polling_interval_no_values_success():
    args = Namespace()
    
    validate_timeout_polling_interval(args)


def test_validate_timeout_polling_interval_only_timeout_success():
    args = Namespace(timeout=30)
    
    validate_timeout_polling_interval(args)


def test_validate_timeout_polling_interval_only_polling_interval_success():
    args = Namespace(polling_interval=30)
    
    validate_timeout_polling_interval(args)


def test_validate_timeout_polling_interval_none_values_success():
    args = Namespace(timeout=None, polling_interval=None)
    
    validate_timeout_polling_interval(args)

if __name__ == "__main__":
    pytest.main([__file__])