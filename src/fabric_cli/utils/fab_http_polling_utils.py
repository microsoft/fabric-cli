# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional
from requests.structures import CaseInsensitiveDict
from fabric_cli.core import fab_logger

DEFAULT_POLLING_INTERVAL = 10


def get_polling_interval(
    response_headers: CaseInsensitiveDict[str],
    custom_polling_interval: Optional[int] = None
) -> int:
    """
    Extract polling interval from custom value or Retry-After header with fallback and logging.
    
    Args:
        response_headers: HTTP response headers case insensitive dictionary
        custom_polling_interval: Optional custom polling interval in seconds
        
    Returns:
        int: Polling interval in seconds
    """
    if custom_polling_interval is not None:
        fab_logger.log_debug(f"Using custom polling interval: {custom_polling_interval} seconds")
        return custom_polling_interval
    
    retry_after_value = response_headers.get("retry-after", DEFAULT_POLLING_INTERVAL)
    fab_logger.log_debug(f"Retrieved Retry-After header value: {retry_after_value}")
    
    try:
        interval = int(retry_after_value)
        fab_logger.log_debug(f"Successfully extracted polling interval: {interval} seconds")
        return interval
    except (ValueError, TypeError):
        fab_logger.log_debug(f"Invalid Retry-After header value '{retry_after_value}', cannot convert to integer, using {DEFAULT_POLLING_INTERVAL}-second fallback")
        return DEFAULT_POLLING_INTERVAL