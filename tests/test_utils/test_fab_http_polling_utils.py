# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch
from requests.structures import CaseInsensitiveDict

from fabric_cli.utils.fab_http_polling_utils import get_polling_interval, DEFAULT_POLLING_INTERVAL


@patch('fabric_cli.core.fab_logger.log_debug')
def test_valid_retry_after_header(mock_log_debug):
    headers = CaseInsensitiveDict({"Retry-After": "120"})
    interval = get_polling_interval(headers)
    assert interval == 120
    mock_log_debug.assert_called_with("Successfully extracted polling interval: 120 seconds")


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


@patch('fabric_cli.core.fab_logger.log_debug')
def test_logging_custom_interval(mock_log_debug):
    headers = CaseInsensitiveDict({})
    get_polling_interval(headers, custom_polling_interval=25)
    
    mock_log_debug.assert_called_with("Using custom polling interval: 25 seconds")