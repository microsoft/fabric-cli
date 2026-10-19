# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional
from requests.structures import CaseInsensitiveDict
from fabric_cli.core import fab_logger

DEFAULT_POLLING_INTERVAL = 10
_LRO_POLL_TARGETS_SECONDS = (2, 7, 20)


def get_polling_interval(
    response_headers: CaseInsensitiveDict[str],
    custom_polling_interval: Optional[int] = None,
    *,
    heuristic_poll_count: Optional[int] = None,
    elapsed_seconds: float = 0.0,
) -> float:
    """
    Select a custom, opt-in heuristic, or Retry-After polling interval.

    Args:
        response_headers: HTTP response headers case insensitive dictionary
        custom_polling_interval: Optional custom polling interval in seconds
        heuristic_poll_count: Number of completed polls; None disables heuristics
        elapsed_seconds: Time since polling began, including request duration

    Returns:
        float: Polling interval in seconds. After the first three heuristic polls,
        use Retry-After with the existing fallback. Custom intervals take precedence.
    """
    if custom_polling_interval is not None:
        fab_logger.log_debug(
            f"Using custom polling interval: {custom_polling_interval} seconds"
        )
        return custom_polling_interval

    if heuristic_poll_count is not None and 0 <= heuristic_poll_count < len(
        _LRO_POLL_TARGETS_SECONDS
    ):
        # Deadlines avoid adding request latency to the early polling schedule.
        interval_seconds = max(
            0.0, _LRO_POLL_TARGETS_SECONDS[heuristic_poll_count] - elapsed_seconds
        )
        fab_logger.log_debug(
            f"Using heuristic polling interval: {interval_seconds} seconds"
        )
        return interval_seconds

    retry_after_value = response_headers.get("retry-after", DEFAULT_POLLING_INTERVAL)
    fab_logger.log_debug(f"Retrieved Retry-After header value: {retry_after_value}")

    try:
        interval = int(retry_after_value)
        fab_logger.log_debug(
            f"Successfully extracted polling interval: {interval} seconds"
        )
        return interval
    except (ValueError, TypeError):
        fab_logger.log_debug(
            f"Invalid Retry-After header value '{retry_after_value}', cannot convert to integer, using {DEFAULT_POLLING_INTERVAL}-second fallback"
        )
        return DEFAULT_POLLING_INTERVAL
