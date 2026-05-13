# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils.fab_cmd_job_utils import (
    validate_timeout_polling_interval,
    wait_for_job_completion,
)
from fabric_cli.utils.fab_http_polling_utils import DEFAULT_POLLING_INTERVAL


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


@patch("questionary.print")
@patch("fabric_cli.utils.fab_cmd_job_utils.get_polling_interval")
@patch("fabric_cli.utils.fab_cmd_job_utils.jobs_api.get_item_job_instance")
@patch("fabric_cli.utils.fab_cmd_job_utils.time.sleep")
def test_wait_for_job_completion_json_output_contains_instance_id(
    mock_sleep,
    mock_api,
    mock_get_polling_interval,
    mock_print,
    default_job_args,
    mock_job_response,
):
    """Verify that Completed status includes the job instance id in JSON output."""
    mock_get_polling_interval.return_value = DEFAULT_POLLING_INTERVAL
    mock_api.return_value = create_mock_response(status="Completed")

    job_instance_id = "abc12345-def6-7890-abcd-ef1234567890"
    wait_for_job_completion(
        default_job_args,
        job_instance_id,
        mock_job_response,
        custom_polling_interval=None,
    )

    # Find the JSON output call
    json_output = None
    for call in mock_print.call_args_list:
        try:
            parsed = json.loads(call.args[0])
            if parsed.get("status") == "Success" and "result" in parsed:
                json_output = parsed
                break
        except (json.JSONDecodeError, TypeError, IndexError):
            continue

    assert json_output is not None, "Expected JSON output from wait_for_job_completion"
    assert json_output["status"] == "Success"
    assert "data" in json_output["result"]
    assert len(json_output["result"]["data"]) == 1
    assert json_output["result"]["data"][0]["id"] == job_instance_id
    assert "completed" in json_output["result"]["message"]


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
    
    # Should raise FabricCLIError with ERROR_JOB_FAILED when job status is "Failed"
    with pytest.raises(FabricCLIError) as exc_info:
        wait_for_job_completion(default_job_args, "test-job-id", mock_job_response, custom_polling_interval=None)
    
    # Verify the exception details
    assert exc_info.value.status_code == fab_constant.ERROR_JOB_FAILED
    assert "Job instance 'test-job-id' Failed" in str(exc_info.value.message)
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


# region JSON output contract tests


@patch('questionary.print')
@patch('fabric_cli.commands.jobs.fab_jobs_run.jobs_api.run_on_demand_item_job')
def test_job_start_json_output_contains_instance_id(mock_run_job, mock_print):
    """Verify that job start (no wait) in JSON mode outputs result.data[0].id with the job instance id."""
    from fabric_cli.commands.jobs.fab_jobs_run import exec_command

    job_instance_id = "abc12345-def6-7890-abcd-ef1234567890"
    mock_response = Mock()
    mock_response.status_code = 202
    mock_response.headers = {"Location": f"https://api.fabric.microsoft.com/v1/workspaces/ws1/items/item1/jobs/instances/{job_instance_id}"}
    mock_run_job.return_value = (mock_response, job_instance_id)

    args = Namespace(
        command="job",
        command_path="job start",
        wait=False,
        configuration=None,
        output_format="json",
    )
    item = Mock()
    item.path = "/ws.Workspace/nb.Notebook"

    exec_command(args, item)

    # Find the JSON output call
    json_output = None
    for call in mock_print.call_args_list:
        try:
            parsed = json.loads(call.args[0])
            if parsed.get("status") == "Success" and "result" in parsed:
                json_output = parsed
                break
        except (json.JSONDecodeError, TypeError, IndexError):
            continue

    assert json_output is not None, "Expected JSON output from job start"
    assert json_output["status"] == "Success"
    assert "data" in json_output["result"]
    assert len(json_output["result"]["data"]) == 1
    assert json_output["result"]["data"][0]["id"] == job_instance_id
    assert "created" in json_output["result"]["message"]


@patch('questionary.print')
@patch('fabric_cli.commands.jobs.fab_jobs_run.jobs_api.cancel_item_job_instance')
@patch('fabric_cli.commands.jobs.fab_jobs_run.config.get_config')
@patch('fabric_cli.commands.jobs.fab_jobs_run.utils_job.wait_for_job_completion')
@patch('fabric_cli.commands.jobs.fab_jobs_run.jobs_api.run_on_demand_item_job')
def test_job_run_timeout_cancelled_json_output_contains_instance_id(
    mock_run_job, mock_wait, mock_get_config, mock_cancel, mock_print
):
    """Verify that timeout-cancelled path in JSON mode outputs result.data[0].id with the job instance id."""
    from fabric_cli.commands.jobs.fab_jobs_run import exec_command

    job_instance_id = "abc12345-def6-7890-abcd-ef1234567890"
    mock_response = Mock()
    mock_response.status_code = 202
    mock_response.headers = {}
    mock_run_job.return_value = (mock_response, job_instance_id)

    # Simulate timeout
    mock_wait.side_effect = TimeoutError(f"Job instance '{job_instance_id}' timed out after 1 seconds")

    # Configure cancel-on-timeout to true
    mock_get_config.return_value = "true"

    # Cancel returns 202
    mock_cancel_response = Mock()
    mock_cancel_response.status_code = 202
    mock_cancel.return_value = mock_cancel_response

    args = Namespace(
        command="job",
        command_path="job run",
        wait=True,
        timeout=1,
        configuration=None,
        output_format="json",
        polling_interval=None,
    )
    item = Mock()
    item.path = "/ws.Workspace/nb.Notebook"

    exec_command(args, item)

    # Find the JSON output call for cancellation
    json_output = None
    for call in mock_print.call_args_list:
        try:
            parsed = json.loads(call.args[0])
            if parsed.get("status") == "Success" and "result" in parsed:
                json_output = parsed
                break
        except (json.JSONDecodeError, TypeError, IndexError):
            continue

    assert json_output is not None, "Expected JSON output from timeout-cancelled job run"
    assert json_output["status"] == "Success"
    assert "data" in json_output["result"]
    assert len(json_output["result"]["data"]) == 1
    assert json_output["result"]["data"][0]["id"] == job_instance_id
    assert "cancelled" in json_output["result"]["message"]


# endregion


if __name__ == "__main__":
    pytest.main([__file__])