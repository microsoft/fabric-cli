# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch

import pytest
from requests.structures import CaseInsensitiveDict

from fabric_cli.utils.fab_http_polling_utils import (
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
        (3, 20.0, 30.0),
        (4, 50.0, 30.0),
    ],
)
def test_heuristic_interval_uses_elapsed_targets_then_header(
    poll_count: int, elapsed: float, expected: float
) -> None:
    headers = CaseInsensitiveDict({"Retry-After": "30"})
    assert (
        get_polling_interval(
            headers, heuristic_poll_count=poll_count, elapsed_seconds=elapsed
        )
        == expected
    )


def test_custom_interval_takes_precedence_over_heuristics() -> None:
    headers = CaseInsensitiveDict({"Retry-After": "30"})
    assert (
        get_polling_interval(headers, 15, heuristic_poll_count=0, elapsed_seconds=0)
        == 15
    )


def test_elapsed_time_alone_does_not_enable_heuristics() -> None:
    headers = CaseInsensitiveDict({"Retry-After": "30"})
    assert get_polling_interval(headers, elapsed_seconds=2.0) == 30


@pytest.mark.parametrize("retry_after", [None, "", "invalid"])
def test_heuristic_exhaustion_uses_header_fallback(retry_after: str | None) -> None:
    headers: CaseInsensitiveDict[str] = CaseInsensitiveDict()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    assert (
        get_polling_interval(headers, heuristic_poll_count=3, elapsed_seconds=20)
        == DEFAULT_POLLING_INTERVAL
    )
