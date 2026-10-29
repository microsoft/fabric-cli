# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Unit tests for job start waiting and job run compatibility."""

import inspect
import json
from argparse import Namespace
from unittest.mock import Mock

import pytest

from fabric_cli.commands.jobs import fab_jobs
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_parser_setup import CustomArgumentParser
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.parsers import fab_jobs_parser


def _parse_job_args(command: str, flags: list[str]) -> Namespace:
    parser = CustomArgumentParser()
    fab_jobs_parser.register_parser(parser.add_subparsers(dest="command"))
    args = parser.parse_args(["job", command, "ws.Workspace/nb.Notebook", *flags])
    args.item = "nb.Notebook"
    args.output_format = "json"
    args.command_path = f"job {command}"
    return args


@pytest.fixture
def job_mocks(monkeypatch: pytest.MonkeyPatch) -> Namespace:
    """Isolate context resolution, HTTP requests, output, and polling delays."""
    item = Mock(spec=Item)
    monkeypatch.setattr(
        fab_jobs.handle_context, "get_command_context", Mock(return_value=item)
    )
    monkeypatch.setattr(fab_jobs.utils_job, "add_item_props_to_args", Mock())
    monkeypatch.setattr(fab_jobs.utils_job, "build_config_from_args", Mock())

    response = Mock(status_code=202, headers={})
    start = Mock(return_value=(response, "test-job-id"))
    poll = Mock(
        side_effect=[
            Mock(status_code=200, headers={}, text=json.dumps({"status": status}))
            for status in ("InProgress", "Completed")
        ]
    )
    sleep = Mock()
    output = Mock()
    monkeypatch.setattr(fab_jobs.jobs_run.jobs_api, "run_on_demand_item_job", start)
    monkeypatch.setattr(fab_jobs.utils_job.jobs_api, "get_item_job_instance", poll)
    monkeypatch.setattr(fab_jobs.utils_job.time, "sleep", sleep)
    monkeypatch.setattr(fab_jobs.fab_ui, "print_grey", Mock())
    monkeypatch.setattr(fab_jobs.fab_ui, "print_progress", Mock())
    monkeypatch.setattr(fab_jobs.fab_ui, "print_output_format", output)
    monkeypatch.setattr(fab_jobs.fab_ui, "print_entries_unix_style", Mock())
    return Namespace(start=start, poll=poll, sleep=sleep, output=output)


@pytest.mark.parametrize(
    ("command", "flags", "wait"),
    [
        ("start", [], False),
        ("start", ["--wait"], True),
        ("start", ["-w"], True),
        ("run", [], True),
    ],
)
def test_job_wait_behavior(
    command: str, flags: list[str], wait: bool, job_mocks: Namespace
) -> None:
    args = _parse_job_args(command, flags)

    inspect.unwrap(fab_jobs.run_command)(args)

    assert args.wait is wait
    job_mocks.start.assert_called_once_with(args, None)
    assert job_mocks.poll.call_count == (2 if wait else 0)
    assert job_mocks.sleep.call_count == (2 if wait else 0)
    job_mocks.output.assert_called_once()
    assert job_mocks.output.call_args.kwargs["data"] == {"id": "test-job-id"}
    assert job_mocks.output.call_args.kwargs["message"] == (
        f"Job instance 'test-job-id' {'completed' if wait else 'created'}"
    )


@pytest.mark.parametrize("command", ["start", "run"])
def test_job_wait_reports_failure(command: str, job_mocks: Namespace) -> None:
    args = _parse_job_args(command, ["--wait"] if command == "start" else [])
    job_mocks.poll.side_effect = None
    job_mocks.poll.return_value = Mock(
        status_code=200, headers={}, text=json.dumps({"status": "Failed"})
    )

    with pytest.raises(FabricCLIError) as exc_info:
        inspect.unwrap(fab_jobs.run_command)(args)

    assert exc_info.value.status_code == fab_constant.ERROR_JOB_FAILED
    job_mocks.output.assert_not_called()


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        (["--timeout", "60"], "--timeout can only be used with --wait"),
        (
            ["--polling_interval", "10"],
            "--polling_interval can only be used with --wait",
        ),
        (
            ["--timeout", "60", "--polling_interval", "10"],
            "--timeout, --polling_interval can only be used with --wait",
        ),
    ],
)
def test_job_start_wait_options_without_wait_failure(
    flags: list[str], expected: str, job_mocks: Namespace
) -> None:
    args = _parse_job_args("start", flags)

    with pytest.raises(FabricCLIError) as exc_info:
        inspect.unwrap(fab_jobs.run_command)(args)

    assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert exc_info.value.message == expected
    job_mocks.start.assert_not_called()


def test_job_start_wait_timeout_success(
    job_mocks: Namespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _parse_job_args(
        "start", ["--wait", "--timeout", "60", "--polling_interval", "10"]
    )
    wait = Mock()
    monkeypatch.setattr(fab_jobs.jobs_run.utils_job, "wait_for_job_completion", wait)

    inspect.unwrap(fab_jobs.run_command)(args)

    wait.assert_called_once()
    assert wait.call_args.kwargs["timeout"] == 60
    assert wait.call_args.kwargs["custom_polling_interval"] == 10


def test_job_start_wait_timeout_cancels_job(
    job_mocks: Namespace,
    monkeypatch: pytest.MonkeyPatch,
    mock_fab_set_state_config,
) -> None:
    args = _parse_job_args("start", ["--wait", "--timeout", "5"])
    mock_fab_set_state_config(fab_constant.FAB_JOB_CANCEL_ONTIMEOUT, "true")
    monkeypatch.setattr(
        fab_jobs.jobs_run.utils_job,
        "wait_for_job_completion",
        Mock(side_effect=TimeoutError("timed out")),
    )
    monkeypatch.setattr(fab_jobs.fab_ui, "print_warning", Mock())
    cancel = Mock(return_value=Mock(status_code=202))
    monkeypatch.setattr(fab_jobs.jobs_run.jobs_api, "cancel_item_job_instance", cancel)

    inspect.unwrap(fab_jobs.run_command)(args)

    cancel.assert_called_once_with(args)
    assert args.instance_id == "test-job-id"
