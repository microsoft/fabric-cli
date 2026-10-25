# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from dataclasses import dataclass, field
from unittest.mock import Mock, patch

import pytest
from requests.structures import CaseInsensitiveDict

from fabric_cli.client import fab_api_client
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_cmd_job_utils


@dataclass
class PollingClock:
    elapsed: float = 0
    poll_times: list[float] = field(default_factory=list)
    waits: list[float] = field(default_factory=list)

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0
        self.waits.append(seconds)
        self.elapsed += seconds


def _response(
    status: str = "Running",
    retry_after: str | None = "20",
    status_code: int = 200,
) -> ApiResponse:
    headers: CaseInsensitiveDict[str] = CaseInsensitiveDict()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return ApiResponse(
        status_code=status_code,
        text=json.dumps({"status": status}),
        content=b"",
        headers=headers,
    )


@pytest.fixture
def polling_clock(monkeypatch: pytest.MonkeyPatch) -> PollingClock:
    clock = PollingClock()
    monkeypatch.setattr(fab_api_client.time, "monotonic", lambda: clock.elapsed)
    monkeypatch.setattr(fab_api_client.time, "sleep", clock.sleep)
    monkeypatch.setattr(fab_api_client.fab_logger, "log_progress", Mock())
    return clock


def _poll_fabric_operation(original_response: ApiResponse) -> ApiResponse:
    return fab_api_client._poll_operation(
        "fabric",
        "operations/test-operation",
        original_response,
        fab_constant.SCOPE_FABRIC_DEFAULT,
        check_status=True,
    )


def test_first_three_polls_use_heuristic_then_latest_retry_after_success(
    polling_clock: PollingClock,
) -> None:
    responses = iter(
        [
            _response(retry_after="30"),
            _response(retry_after="40"),
            _response(retry_after="9"),
            _response(retry_after="4"),
            _response("Succeeded"),
        ]
    )

    def request(*args: object, **kwargs: object) -> ApiResponse:
        polling_clock.poll_times.append(polling_clock.elapsed)
        return next(responses)

    original = _response(status_code=202)
    with patch.object(fab_api_client, "do_request", side_effect=request):
        assert _poll_fabric_operation(original) is original

    assert polling_clock.poll_times == [2, 7, 20, 29, 33]
    assert polling_clock.waits == [2, 5, 13, 9, 4]
    assert original.status_code == 200


@pytest.mark.parametrize(
    ("request_duration", "expected_poll_times", "expected_waits"),
    [
        pytest.param(1, [2, 7, 20], [2, 4, 12], id="subtract-request-time-from-wait"),
        pytest.param(10, [2, 12, 22], [2, 0, 0], id="no-wait-after-missed-target"),
    ],
)
def test_time_spent_on_requests_is_subtracted_from_poll_waits_success(
    polling_clock: PollingClock,
    request_duration: int,
    expected_poll_times: list[int],
    expected_waits: list[int],
) -> None:
    responses = iter([_response(), _response(), _response("Succeeded")])

    def request(*args: object, **kwargs: object) -> ApiResponse:
        polling_clock.poll_times.append(polling_clock.elapsed)
        polling_clock.elapsed += request_duration
        return next(responses)

    with patch.object(fab_api_client, "do_request", side_effect=request):
        _poll_fabric_operation(_response(status_code=202))

    assert polling_clock.poll_times == expected_poll_times
    assert polling_clock.waits == expected_waits


@pytest.mark.parametrize("retry_after", [None, "invalid", ""])
def test_missing_or_invalid_retry_after_waits_10_seconds_success(
    polling_clock: PollingClock, retry_after: str | None
) -> None:
    with patch.object(
        fab_api_client,
        "do_request",
        side_effect=[
            _response(retry_after=retry_after),
            _response(retry_after=retry_after),
            _response(retry_after=retry_after),
            _response("Succeeded"),
        ],
    ):
        _poll_fabric_operation(_response(retry_after=retry_after, status_code=202))

    assert polling_clock.waits == [2, 5, 13, 10]


@pytest.mark.parametrize("status", ["Succeeded", "Completed"])
def test_completed_operation_stops_polling_success(
    polling_clock: PollingClock, status: str
) -> None:
    with patch.object(
        fab_api_client, "do_request", return_value=_response(status)
    ) as request:
        _poll_fabric_operation(_response(status_code=202))

    request.assert_called_once()
    assert polling_clock.waits == [2]


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        ("Failed", fab_constant.ERROR_OPERATION_FAILED),
        ("Cancelled", fab_constant.ERROR_OPERATION_CANCELLED),
    ],
)
def test_failed_or_cancelled_operation_raises_error_failure(
    polling_clock: PollingClock, status: str, expected_error: int
) -> None:
    with patch.object(
        fab_api_client, "do_request", return_value=_response(status)
    ) as request:
        with pytest.raises(FabricCLIError) as error:
            _poll_fabric_operation(_response(status_code=202))
        assert error.value.status_code == expected_error

    request.assert_called_once()
    assert polling_clock.waits == [2]


def test_completed_operation_fetches_result_without_another_wait_success(
    polling_clock: PollingClock,
) -> None:
    completed = _response("Succeeded")
    completed.headers["Location"] = (
        "https://api.fabric.microsoft.com/v1/operations/test-operation/result"
    )
    result = _response("result")
    with patch.object(
        fab_api_client, "do_request", side_effect=[completed, result]
    ) as request:
        assert _poll_fabric_operation(_response(status_code=202)) is result

    assert request.call_count == 2
    assert request.call_args.args[0].uri == "operations/test-operation/result"
    assert polling_clock.waits == [2]


@pytest.mark.parametrize("check_status", [True, False])
def test_azure_polls_always_wait_for_retry_after_success(
    polling_clock: PollingClock, check_status: bool
) -> None:
    original = _response(status_code=202)
    responses = (
        [_response(retry_after="8"), _response("Succeeded")]
        if check_status
        else [_response(status_code=201, retry_after="8"), _response()]
    )
    with patch.object(fab_api_client, "do_request", side_effect=responses):
        result = fab_api_client._poll_operation(
            "azure",
            "/operation",
            original,
            fab_constant.SCOPE_AZURE_DEFAULT,
            check_status,
        )

    assert result is original
    assert polling_clock.waits == [20, 8]


@pytest.mark.parametrize(
    ("custom_interval", "expected_waits"),
    [(None, [20, 8]), (3, [3, 3])],
)
def test_jobs_wait_for_retry_after_unless_custom_interval_is_set_success(
    polling_clock: PollingClock,
    custom_interval: int | None,
    expected_waits: list[int],
) -> None:
    with (
        patch.object(
            fab_cmd_job_utils.jobs_api,
            "get_item_job_instance",
            side_effect=[_response("InProgress", "8"), _response("Completed")],
        ),
        patch.object(fab_cmd_job_utils.fab_ui, "print_progress"),
        patch.object(fab_cmd_job_utils.fab_ui, "print_grey"),
        patch.object(fab_cmd_job_utils.fab_ui, "print_output_format"),
    ):
        fab_cmd_job_utils.wait_for_job_completion(
            Namespace(),
            "test-job",
            _response(status_code=202),
            custom_polling_interval=custom_interval,
        )

    assert polling_clock.waits == expected_waits
