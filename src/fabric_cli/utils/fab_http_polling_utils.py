# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
from typing import Optional
from requests.structures import CaseInsensitiveDict
from fabric_cli.core import fab_logger

DEFAULT_POLLING_INTERVAL = 10
_LRO_POLL_TARGETS_SECONDS = (2, 7, 20)


def get_polling_interval(
    response_headers: CaseInsensitiveDict[str],
    custom_polling_interval: Optional[int] = None,
) -> int:
    """
    Extract a custom interval or Retry-After header with fallback and logging.

    Args:
        response_headers: HTTP response headers case insensitive dictionary
        custom_polling_interval: Optional custom polling interval in seconds

    Returns:
        int: Polling interval in seconds
    """
    if custom_polling_interval is not None:
        fab_logger.log_debug(
            f"Using custom polling interval: {custom_polling_interval} seconds"
        )
        return custom_polling_interval

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


def get_lro_polling_interval(
    response_headers: CaseInsensitiveDict[str],
    audience: str,
    poll_count: int,
    polling_started: float,
) -> int:
    """
    Select the heuristic or Retry-After interval for a long-running operation.

    Fabric operations use elapsed-time targets for the first three polls.
    Remaining waits are rounded to the nearest whole second.
    Other audiences and later polls use Retry-After.
    """
    elapsed = time.monotonic() - polling_started
    if audience == "fabric" and 0 <= poll_count < len(_LRO_POLL_TARGETS_SECONDS):
        # Deadlines account for time spent on previous poll requests.
        target = _LRO_POLL_TARGETS_SECONDS[poll_count]
        custom_interval = max(0, round(target - elapsed))
        interval = get_polling_interval(response_headers, custom_interval)
        source = f"heuristic (target={target}s)"
    else:
        interval = get_polling_interval(response_headers)
        source = "latest response Retry-After or fallback"

    fab_logger.log_debug(
        f"LRO poll #{poll_count + 1}: audience={audience}, "
        f"elapsed={elapsed:.3f}s, wait={interval:.3f}s, source={source}"
    )
    return interval
