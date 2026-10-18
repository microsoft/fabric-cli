# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from pathlib import Path
from typing import TypedDict
from unittest.mock import Mock, patch

import pytest
from requests.structures import CaseInsensitiveDict

from fabric_cli.client import fab_api_client
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_cmd_job_utils


class PollingClock(TypedDict):
    now: float
    polls: list[float]
    sleeps: list[float]


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
    clock: PollingClock = {"now": 100.0, "polls": [], "sleeps": []}

    def sleep(seconds: float) -> None:
        assert seconds >= 0
        clock["sleeps"].append(seconds)
        clock["now"] += seconds

    monkeypatch.setattr(fab_api_client.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(fab_api_client.time, "sleep", sleep)
    monkeypatch.setattr(fab_api_client.fab_logger, "log_progress", Mock())
    return clock


def _poll(original_response: ApiResponse, audience: str = "fabric") -> ApiResponse:
    return fab_api_client._poll_operation(
        audience,
        "operations/test-operation",
        original_response,
        (
            fab_constant.SCOPE_FABRIC_DEFAULT
            if audience == "fabric"
            else fab_constant.SCOPE_AZURE_DEFAULT
        ),
        check_status=True,
    )


@pytest.mark.parametrize("disabled", [None, False, "false"])
def test_early_polls_follow_elapsed_targets_then_latest_header(
    polling_clock: PollingClock, disabled: object
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
        polling_clock["polls"].append(polling_clock["now"] - 100)
        return next(responses)

    original = _response(status_code=202)
    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value=disabled
        ),
        patch.object(fab_api_client, "do_request", side_effect=request),
    ):
        assert _poll(original) is original

    assert polling_clock["polls"] == [2, 7, 20, 29, 33]
    assert polling_clock["sleeps"] == [2, 5, 13, 9, 4]
    assert original.status_code == 200


@pytest.mark.parametrize(
    ("request_duration", "expected_polls", "expected_sleeps"),
    [(1, [2, 7, 20], [2, 4, 12]), (10, [2, 12, 22], [2, 0, 0])],
)
def test_poll_targets_account_for_request_duration(
    polling_clock: PollingClock,
    request_duration: int,
    expected_polls: list[int],
    expected_sleeps: list[int],
) -> None:
    responses = iter([_response(), _response(), _response("Succeeded")])

    def request(*args: object, **kwargs: object) -> ApiResponse:
        polling_clock["polls"].append(polling_clock["now"] - 100)
        polling_clock["now"] += request_duration
        return next(responses)

    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value="false"
        ),
        patch.object(fab_api_client, "do_request", side_effect=request),
    ):
        _poll(_response(status_code=202))

    assert polling_clock["polls"] == expected_polls
    assert polling_clock["sleeps"] == expected_sleeps


@pytest.mark.parametrize("disabled", [True, "true", "True", "TRUE"])
def test_disabled_heuristics_always_use_latest_header(
    polling_clock: PollingClock, disabled: object
) -> None:
    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value=disabled
        ),
        patch.object(
            fab_api_client,
            "do_request",
            side_effect=[_response(retry_after="6"), _response("Completed")],
        ),
    ):
        _poll(_response(status_code=202))

    assert polling_clock["sleeps"] == [20, 6]


@pytest.mark.parametrize("retry_after", [None, "invalid", ""])
@pytest.mark.parametrize("disabled", ["false", "true"])
def test_header_fallback_is_preserved(
    polling_clock: PollingClock, retry_after: str | None, disabled: str
) -> None:
    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value=disabled
        ),
        patch.object(
            fab_api_client,
            "do_request",
            side_effect=[
                _response(retry_after=retry_after),
                _response(retry_after=retry_after),
                _response(retry_after=retry_after),
                _response("Succeeded"),
            ],
        ),
    ):
        _poll(_response(retry_after=retry_after, status_code=202))

    assert polling_clock["sleeps"] == (
        [2, 5, 13, 10] if disabled == "false" else [10, 10, 10, 10]
    )


@pytest.mark.parametrize("status", ["Succeeded", "Completed", "Failed", "Cancelled"])
def test_terminal_status_stops_polling(
    polling_clock: PollingClock, status: str
) -> None:
    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value="false"
        ),
        patch.object(
            fab_api_client, "do_request", return_value=_response(status)
        ) as request,
    ):
        if status in ("Failed", "Cancelled"):
            with pytest.raises(FabricCLIError) as error:
                _poll(_response(status_code=202))
            assert error.value.status_code == (
                fab_constant.ERROR_OPERATION_FAILED
                if status == "Failed"
                else fab_constant.ERROR_OPERATION_CANCELLED
            )
        else:
            _poll(_response(status_code=202))

    request.assert_called_once()
    assert polling_clock["sleeps"] == [2]


def test_operation_result_is_fetched_without_additional_polling(
    polling_clock: PollingClock,
) -> None:
    completed = _response("Succeeded")
    completed.headers["Location"] = (
        "https://api.fabric.microsoft.com/v1/operations/test-operation/result"
    )
    result = _response("result")
    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value="false"
        ),
        patch.object(
            fab_api_client, "do_request", side_effect=[completed, result]
        ) as request,
    ):
        assert _poll(_response(status_code=202)) is result

    assert request.call_count == 2
    assert request.call_args.args[0].uri == "operations/test-operation/result"
    assert polling_clock["sleeps"] == [2]


@pytest.mark.parametrize("check_status", [True, False])
def test_azure_polling_keeps_header_intervals(
    polling_clock: PollingClock, check_status: bool
) -> None:
    original = _response(status_code=202)
    responses = (
        [_response(retry_after="8"), _response("Succeeded")]
        if check_status
        else [_response(status_code=201, retry_after="8"), _response()]
    )
    with (
        patch.object(
            fab_api_client.fab_state_config, "get_config", return_value="false"
        ),
        patch.object(fab_api_client, "do_request", side_effect=responses),
    ):
        result = fab_api_client._poll_operation(
            "azure",
            "/operation",
            original,
            fab_constant.SCOPE_AZURE_DEFAULT,
            check_status,
        )

    assert result is original
    assert polling_clock["sleeps"] == [20, 8]


@pytest.mark.parametrize("custom_interval", [None, 3])
def test_jobs_polling_keeps_header_and_custom_intervals(
    polling_clock: PollingClock, custom_interval: int | None
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

    assert polling_clock["sleeps"] == ([20, 8] if custom_interval is None else [3, 3])


@pytest.mark.parametrize("value", ["true", "false"])
def test_polling_config_can_be_set_and_completed(tmp_path: Path, value: str) -> None:
    from fabric_cli.commands.config import fab_config_set
    from fabric_cli.core import fab_state_config
    from fabric_cli.core.completers import fab_config_completers

    key = fab_constant.FAB_DISABLE_HEURISTIC_LRO_POLLING
    args = Namespace(key=key, value=value)
    with (
        patch.object(fab_state_config, "config_file", str(tmp_path / "config.json")),
        patch.object(fab_config_set.utils_ui, "print_grey"),
        patch.object(fab_config_set.utils_ui, "print_output_format"),
    ):
        fab_state_config.init_defaults()
        assert fab_state_config.get_config(key) == "false"
        fab_config_set.exec_command(args)
        assert fab_state_config.get_config(key) == value
        fab_state_config.init_defaults()
        assert fab_state_config.get_config(key) == value

    assert key in fab_config_completers.complete_config_keys("disable_")
    assert fab_config_completers.complete_config_values("", args) == ["false", "true"]
    assert not fab_config_set._can_key_contain_value(key, "invalid")
