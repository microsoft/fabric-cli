# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch

import pytest
from requests.structures import CaseInsensitiveDict

from fabric_cli.utils.fab_http_polling_utils import (
    get_lro_polling_interval,
    get_polling_interval,
    DEFAULT_POLLING_INTERVAL,
)


@patch("fabric_cli.core.fab_logger.log_debug")
def test_valid_retry_after_header(mock_log_debug):
    headers = CaseInsensitiveDict({"Retry-After": "120"})
    interval = get_polling_interval(headers)
    assert interval == 120
    mock_log_debug.assert_called_with(
        "Successfully extracted polling interval: 120 seconds"
    )


def test_invalid_retry_after_header():
    headers = CaseInsensitiveDict({"Retry-After": "invalid"})
    interval = get_polling_interval(headers)
    assert interval == DEFAULT_POLLING_INTERVAL

    headers = CaseInsensitiveDict({"Retry-After": ""})
    interval = get_polling_interval(headers)
    assert interval == DEFAULT_POLLING_INTERVAL


def test_missing_retry_after_header():
    headers = CaseInsensitiveDict({})
    interval = get_polling_interval(headers)
    assert interval == DEFAULT_POLLING_INTERVAL

    headers = CaseInsensitiveDict({"Other-Header": "value"})
    interval = get_polling_interval(headers)
    assert interval == DEFAULT_POLLING_INTERVAL


def test_hardcoded_fallback_value():
    headers = CaseInsensitiveDict({})
    interval = get_polling_interval(headers)
    assert interval == DEFAULT_POLLING_INTERVAL


def test_custom_polling_interval_takes_precedence():
    headers = CaseInsensitiveDict({"Retry-After": "120"})
    interval = get_polling_interval(headers, custom_polling_interval=15)
    assert interval == 15


@patch("fabric_cli.core.fab_logger.log_debug")
def test_logging_custom_interval(mock_log_debug):
    headers = CaseInsensitiveDict({})
    get_polling_interval(headers, custom_polling_interval=25)

    mock_log_debug.assert_called_with("Using custom polling interval: 25 seconds")


@pytest.mark.parametrize(
    ("poll_count", "elapsed", "expected"),
    [
        (0, 0.0, 2.0),
        (1, 2.0, 5.0),
        (2, 7.0, 13.0),
        (1, 3.25, 3.75),
        (2, 10.5, 9.5),
        (1, 12.0, 0.0),
        (2, 22.0, 0.0),
    ],
)
def test_lro_heuristic_uses_elapsed_targets_success(
    monkeypatch: pytest.MonkeyPatch, poll_count: int, elapsed: float, expected: float
) -> None:
    headers = CaseInsensitiveDict({"Retry-After": "30"})
    monkeypatch.setattr(
        "fabric_cli.utils.fab_http_polling_utils.time.monotonic",
        lambda: 100.0 + elapsed,
    )
    assert get_lro_polling_interval(headers, "fabric", poll_count, 100.0) == expected


@pytest.mark.parametrize(
    ("audience", "poll_count"),
    [("azure", 0), ("fabric", 3)],
)
def test_lro_uses_retry_after_when_heuristics_do_not_apply_success(
    monkeypatch: pytest.MonkeyPatch, audience: str, poll_count: int
) -> None:
    headers = CaseInsensitiveDict({"Retry-After": "30"})
    monkeypatch.setattr(
        "fabric_cli.utils.fab_http_polling_utils.time.monotonic", lambda: 100.0
    )
    assert get_lro_polling_interval(headers, audience, poll_count, 100.0) == 30


@pytest.mark.parametrize("retry_after", [None, "", "invalid"])
def test_lro_heuristic_exhaustion_uses_header_fallback_success(
    retry_after: str | None,
) -> None:
    headers: CaseInsensitiveDict[str] = CaseInsensitiveDict()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    assert (
        get_lro_polling_interval(headers, "fabric", 3, 20.0) == DEFAULT_POLLING_INTERVAL
    )
