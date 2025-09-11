# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import os
import platform
import time
from unittest.mock import patch

import pytest
from requests import RequestException

from fabric_cli.core import fab_logger as logger
from fabric_cli.core import fab_state_config
from fabric_cli.core.fab_exceptions import FabricCLIError


def test_log_warning():
    logger.log_warning("This is a warning message")

    logger.log_warning("This is a warning message with a command", "command")


def test_log_debug():
    logger.log_debug("This is a debug message")


def test_log_info():
    logger.log_info("This is an info message")


def test_log_progress(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_progress("This is a progress message")

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_progress("This is a progress message")


def test_log_debug_http_request(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request("GET", "http://example.com", {}, 10)

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request("GET", "http://example.com", {}, 10)


def test_log_debug_http_request_json(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request(
        "GET", "http://example.com", {}, 10, json={"key": "value"}
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request(
        "GET", "http://example.com", {}, 10, json={"key": "value"}
    )


def test_log_debug_http_request_data(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request(
        "GET", "http://example.com", {}, 10, data={"key": "value"}
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request(
        "GET", "http://example.com", {}, 10, data={"key": "value"}
    )


def test_log_debug_http_request_files(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request(
        "GET", "http://example.com", {}, 10, files={"key": "value"}
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request(
        "GET", "http://example.com", {}, 10, files={"key": "value"}
    )


def test_log_debug_http_request_attempt(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request("GET", "http://example.com", {}, 10, attempt=2)

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request("GET", "http://example.com", {}, 10, attempt=2)


def test_log_debug_http_request_user_agent(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request(
        "GET", "http://example.com", {"User-Agent": "value"}, 10
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request(
        "GET", "http://example.com", {"User-Agent": "value"}, 10
    )


def test_log_debug_http_request_authorization(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request(
        "GET", "http://example.com", {"Authorization": "value"}, 10
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request(
        "GET", "http://example.com", {"Authorization": "value"}, 10
    )


def test_log_debug_http_request_sample_header(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request(
        "GET", "http://example.com", {"Some-Header": "value"}, 10
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request(
        "GET", "http://example.com", {"Some-Header": "value"}, 10
    )


def test_log_debug_http_response(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(200, {}, "Response text", time.time())

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_response(200, {}, "Response text", time.time())


def test_log_debug_http_response_sample_header(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(
        200, {"Some-Header": "value"}, "Response text", time.time()
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_response(
        200, {"Some-Header": "value"}, "Response text", time.time()
    )


def test_log_debug_http_response_json(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(
        200,
        {"Content-Type": "application/json"},
        json.dumps({"key": "value"}),
        time.time(),
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_response(
        200,
        {"Content-Type": "application/json"},
        json.dumps({"key": "value"}),
        time.time(),
    )


def test_log_debug_http_response_bad_json(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(
        200, {"Content-Type": "application/json"}, "{ bad json", time.time()
    )


def test_log_debug_http_request_exception(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_request_exception(RequestException("This is an exception"))

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_request_exception(RequestException("This is an exception"))


def test_get_logger():
    assert logger.get_logger() is not None
    assert logger.get_logger().name == "FabricCLI"
    assert logger.get_logger().level == logging.DEBUG
    assert (
        logger.get_logger().handlers[0].formatter._fmt
        == "%(asctime)s - %(levelname)s - %(message)s"
    )
    assert logger.log_file_path is not None


def test_get_log_file_path(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    assert_log_file_path("\\AppData\\Local")
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    # Simulate realpath returns a different path (sandbox)
    monkeypatch.setattr("os.path.realpath", lambda x: x + "_sandbox")
    assert_log_file_path("\\AppData\\Local", True)
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert_log_file_path("/Library/Logs")
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(os, "environ", {})
    assert_log_file_path("/.local/state")
    monkeypatch.setattr(os, "environ", {"XDG_STATE_HOME": "/tmp"})
    assert_log_file_path("/tmp")


def assert_log_file_path(base_dir: str, is_sandbox=False):
    log_file_path = logger._get_log_file_path()
    assert log_file_path is not None
    assert log_file_path.endswith("fabcli_debug.log")
    assert base_dir in log_file_path
    if is_sandbox:
        assert "_sandbox" in log_file_path


def test_print_log_file_path_debug_enabled_success(
    mock_get_log_file_path, mock_log_warning, monkeypatch
):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "true")

    mock_get_log_file_path.return_value = "/fake/path/fabcli_debug.log"

    logger.print_log_file_path()

    mock_get_log_file_path.assert_called_once()
    mock_log_warning.assert_called_once()


def test_print_log_file_path_debug_disabled_success(
    mock_get_log_file_path, mock_log_warning, monkeypatch
):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "false")

    logger.print_log_file_path()

    mock_get_log_file_path.assert_not_called()
    mock_log_warning.assert_not_called()


@pytest.fixture
def mock_log_warning():
    with patch("fabric_cli.core.fab_logger.log_warning") as mock:
        yield mock


@pytest.fixture
def mock_get_log_file_path():
    with patch("fabric_cli.core.fab_logger.get_log_file_path") as mock:
        yield mock
