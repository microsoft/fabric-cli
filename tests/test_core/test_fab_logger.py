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
    logger.log_debug_http_response(200, {}, "Response text", time.time(), "cmd")

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_response(200, {}, "Response text", time.time(), "cmd")


def test_log_debug_http_response_sample_header(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(
        200, {"Some-Header": "value"}, "Response text", time.time(), "cmd"
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_response(
        200, {"Some-Header": "value"}, "Response text", time.time(), "cmd"
    )


def test_log_debug_http_response_json(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(
        200,
        {"Content-Type": "application/json"},
        json.dumps({"key": "value"}),
        time.time(),
        "cmd",
    )

    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "0")
    logger.log_debug_http_response(
        200,
        {"Content-Type": "application/json"},
        json.dumps({"key": "value"}),
        time.time(),
        "cmd",
    )


def test_log_debug_http_response_bad_json(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "1")
    logger.log_debug_http_response(
        200, {"Content-Type": "application/json"}, "{ bad json", time.time(), "cmd"
    )


def test_log_debug_http_response_bulk_export(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "true")
    response_body = json.dumps(
        {
            "itemDefinitionsIndex": {"item1": "index1"},
            "definitionParts": [
                {
                    "path": "item_path",
                    "payload": "item_payload",
                    "payloadType": "base64",
                }
            ],
        }
    )
    with patch.object(logger.get_logger(), "debug") as mock_debug:
        logger.log_debug_http_response(
            200,
            {"Content-Type": "application/json"},
            response_body,
            time.time(),
            "bulk-export",
        )

    logged_messages = [call.args[0] for call in mock_debug.call_args_list]
    expected_json = '{"itemDefinitionsIndex":{"item1":"index1"},"definitionParts":"redacted_from_log"}'
    assert any(expected_json in msg for msg in logged_messages)


def test_log_debug_http_response_bulk_export_missing_keys(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "true")
    response_body = json.dumps({"itemDefinitionsIndex": {"item1": "index1"}})
    with patch.object(logger.get_logger(), "debug") as mock_debug:
        logger.log_debug_http_response(
            200,
            {"Content-Type": "application/json"},
            response_body,
            time.time(),
            "bulk-export",
        )

    logged_messages = [call.args[0] for call in mock_debug.call_args_list]
    expected_json = '{"itemDefinitionsIndex":{"item1":"index1"}}'
    assert any(expected_json in msg for msg in logged_messages)


def test_log_debug_http_response_export(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "true")
    response_body = json.dumps(
        {
            "definition": {
                "format": "ipynb",
                "parts": [
                    {
                        "path": "notebook.ipynb",
                        "payload": "base64encodedcontent",
                        "payloadType": "base64",
                    },
                    {
                        "path": "meta.json",
                        "payload": "anotherpayload",
                        "payloadType": "base64",
                    },
                ],
            }
        }
    )
    with patch.object(logger.get_logger(), "debug") as mock_debug:
        logger.log_debug_http_response(
            200,
            {"Content-Type": "application/json"},
            response_body,
            time.time(),
            "export",
        )

    logged_messages = [call.args[0] for call in mock_debug.call_args_list]
    expected_json = (
        '{"definition":{"format":"ipynb","parts":'
        '[{"path":"notebook.ipynb","payload":"redacted_from_log","payloadType":"base64"},'
        '{"path":"meta.json","payload":"redacted_from_log","payloadType":"base64"}]}}'
    )
    assert any(expected_json in msg for msg in logged_messages)


def test_log_debug_http_response_export_missing_parts(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "true")
    response_body = json.dumps({"definition": {"format": "ipynb"}})
    with patch.object(logger.get_logger(), "debug") as mock_debug:
        logger.log_debug_http_response(
            200,
            {"Content-Type": "application/json"},
            response_body,
            time.time(),
            "export",
        )

    logged_messages = [call.args[0] for call in mock_debug.call_args_list]
    expected_json = '{"definition":{"format":"ipynb"}}'
    assert any(expected_json in msg for msg in logged_messages)


def test_log_debug_http_response_other_command_no_processing(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda x: "true")
    response_body = json.dumps(
        {
            "itemDefinitionsIndex": {"item1": "index1"},
            "definitionParts": {"part1": "large_payload_data"},
            "definition": {"format": "ipynb", "parts": [{"payload": "content"}]},
        }
    )
    with patch.object(logger.get_logger(), "debug") as mock_debug:
        logger.log_debug_http_response(
            200,
            {"Content-Type": "application/json"},
            response_body,
            time.time(),
            "other cmd",
        )

    logged_messages = [call.args[0] for call in mock_debug.call_args_list]
    expected_json = json.dumps(json.loads(response_body), separators=(",", ":"))
    assert any(expected_json in msg for msg in logged_messages)


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


# ── Security: log directory and file permissions ─────────────────────────────

_skip_on_windows = pytest.mark.skipif(
    os.name == "nt", reason="POSIX permission tests not applicable on Windows"
)


@_skip_on_windows
def test_get_log_file_path_creates_directory_with_restricted_permissions_success(
    monkeypatch, tmp_path
):
    """Verify log directory is created with mode 0o700 (owner-only)."""
    log_dir = tmp_path / "fabric-cli" / "log"
    monkeypatch.setattr(logger, "user_log_dir", lambda app_name: str(log_dir))

    result = logger._get_log_file_path()
    assert result.endswith("fabcli_debug.log")
    assert log_dir.exists()

    mode = oct(log_dir.stat().st_mode & 0o777)
    assert mode == "0o700", f"Log directory has mode {mode}, expected 0o700"


@_skip_on_windows
def test_log_file_created_with_restricted_permissions_success(monkeypatch, tmp_path):
    """Verify log file is created with mode 0o600 and is readable by the owner."""
    log_dir = tmp_path / "fabric-cli" / "log"
    log_dir.mkdir(parents=True, mode=0o700)
    monkeypatch.setattr(logger, "user_log_dir", lambda app_name: str(log_dir))

    # Reset singleton so _setup_logger creates a fresh handler
    monkeypatch.setattr(logger, "_logger_instance", None)

    log_file = log_dir / "fabcli_debug.log"
    log_instance = logger._setup_logger(str(log_file))

    # Write something to ensure the file exists
    log_instance.debug("permission test entry")

    assert log_file.exists()
    mode = oct(log_file.stat().st_mode & 0o777)
    assert mode == "0o600", f"Log file has mode {mode}, expected 0o600"

    # Verify the owner can still read the file
    content = log_file.read_text()
    assert "permission test entry" in content

    # Cleanup: remove handlers to avoid accumulation on the global singleton
    for handler in log_instance.handlers[:]:
        log_instance.removeHandler(handler)
        handler.close()


@_skip_on_windows
def test_log_file_rotation_preserves_restricted_permissions_success(
    monkeypatch, tmp_path
):
    """Verify rotated log files maintain 0o600 permissions."""
    log_dir = tmp_path / "fabric-cli" / "log"
    log_dir.mkdir(parents=True, mode=0o700)
    log_file = log_dir / "fabcli_debug.log"

    # Create a handler with a small maxBytes to force rotation quickly
    handler = logger._RestrictedRotatingFileHandler(
        str(log_file),
        maxBytes=100,  # Very small to trigger rotation
        backupCount=2,
    )
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    test_logger = logging.getLogger("FabricCLI_rotation_test")
    test_logger.setLevel(logging.DEBUG)
    test_logger.addHandler(handler)

    # Write enough data to trigger at least one rotation
    for i in range(20):
        test_logger.debug(f"rotation test entry {i} with padding to exceed limit")

    # Check that at least one rotated file was created
    rotated_file_1 = log_dir / "fabcli_debug.log.1"
    assert rotated_file_1.exists(), "Expected at least one rotated log file"

    # Verify permissions on the base log file
    mode = oct(log_file.stat().st_mode & 0o777)
    assert mode == "0o600", f"Base log file has mode {mode}, expected 0o600"

    # Verify permissions on the rotated file
    mode = oct(rotated_file_1.stat().st_mode & 0o777)
    assert mode == "0o600", f"Rotated log file has mode {mode}, expected 0o600"

    # Cleanup
    test_logger.removeHandler(handler)
    handler.close()
