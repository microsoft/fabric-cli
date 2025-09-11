# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import http
import json
import logging
import os
import platform
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import fabric_cli.core.fab_constant as fab_constant
import fabric_cli.core.fab_state_config as fab_state_config
import fabric_cli.utils.fab_ui as utils_ui

_logger_instance = None  # Singleton instance
log_file_path = None  # Path to the current log file


def log_warning(message, command=None):
    """Print a warning message."""
    utils_ui.print_warning(message, command)


def log_debug(message):
    """Print a debug message."""
    if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) == "true":
        formatted_message = f"[debug] {message}"
        utils_ui.print_grey(formatted_message)


def log_info(message):
    """Print an info message."""
    formatted_message = f"[info] {message}"
    utils_ui.print_info(formatted_message)


def log_progress(message, progress=None):
    if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) == "true":
        formatted_message = f"[debug] {message}"
        utils_ui.print_progress(formatted_message, progress)


def log_debug_http_request(
    method, url, headers, timeout_sec, attempt=1, json=None, data=None, files=None
):
    """Logs a http request debug message if FAB_DEBUG is enabled."""
    if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) != "true":
        return

    logger = get_logger()

    # Format the request time
    request_time = (
        datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S.%f %Z%z")[:-3]
    )

    # Log the request details
    logger.debug(f"> * Request at {request_time}")
    logger.debug(f"> Attempt: {attempt}")
    logger.debug(f"> Request URL: {url}")
    logger.debug(f"> Request method: {method.upper()}")

    # Headers
    logger.debug("> Request headers:")
    for key, value in headers.items():
        if key.lower() == "authorization":
            value = "*****"  # Mask authorization token
        elif key.lower() == "user-agent":
            continue  # Skip logging the User-Agent header
        logger.debug(f"    '{key}': '{value}'")

    # Body
    logger.debug("> Request body:")
    if json:
        logger.debug("    " + str(json))
    elif data:
        logger.debug("    " + str(data))
    elif files:
        logger.debug("    Files:")
        for file_key, file_value in files.items():
            logger.debug(f"        '{file_key}': '{file_value}'")
    else:
        logger.debug("    None")

    # Timeout
    logger.debug(f"> Timeout: {timeout_sec} seconds")
    logger.debug("")


def log_debug_http_response(status_code, headers, response_text, start_time):
    """Logs a http response debug message if FAB_DEBUG is enabled."""
    if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) != "true":
        return

    logger = get_logger()
    end_time = time.time()

    # Get the status code text
    status_text = (
        http.HTTPStatus(status_code).phrase
        if status_code in http.HTTPStatus._value2member_map_
        else "Unknown Status"
    )

    # Get the current time with local timezone automatically
    response_time = (
        datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S.%f %Z%z")[:-3]
    )

    # Log the response details
    logger.debug(f"< * Response received at {response_time}")
    logger.debug(f"< Status: {status_code} {status_text}")

    # Headers
    logger.debug("< Response headers:")
    for key, value in headers.items():
        logger.debug(f"    '{key}': '{value}'")

    # Body
    logger.debug("< Response body:")
    if response_text is None or response_text == "":
        logger.debug("    None")
    else:
        content_type = headers.get("Content-Type", "")
        if "application/json" in content_type:
            logger.debug("    " + _parse_json_into_single_line(response_text))
        else:
            # If not JSON, log as plain text
            logger.debug("    " + response_text)

    # Response time
    response_time_sec = end_time - start_time
    logger.debug(f"< Request duration: {response_time_sec:.3f} seconds")
    logger.debug("")


def log_debug_http_request_exception(e):
    """
    Logs a debug message for an HTTP request exception if FAB_DEBUG is enabled.
    This function is intended to be used when an HTTP request fails and raises a
    RequestException. It logs the exception details to help with debugging.
    """
    if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) != "true":
        return

    logger = get_logger()

    # Log the exception details
    logger.debug(f"< * Exception occurred")
    logger.debug(f"< Exception: {e}")
    logger.debug("")


def _get_log_file_path():
    """Create a log file path in the user's log directory."""
    log_dir = user_log_dir("fabric-cli")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "fabcli_debug.log")


def get_logger():
    """Singleton logger instance with a single file handler."""
    global _logger_instance, log_file_path
    # Set up the file handler
    log_file_path = _get_log_file_path()  # Set the global log file path
    if _logger_instance is None:
        _logger_instance = _setup_logger(log_file_path)

    return _logger_instance


def _setup_logger(file_name: str):
    # Initialize the singleton logger
    _logger_instance = logging.getLogger("FabricCLI")
    _logger_instance.setLevel(logging.DEBUG)

    # Configure the log file rotation.
    file_handler = RotatingFileHandler(
        file_name,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=7,  # Retain 7 rotated files (35 MB total)
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Attach the file handler to the logger
    _logger_instance.addHandler(file_handler)

    return _logger_instance


def get_log_file_path():
    """Return the current log file path."""
    global log_file_path
    if log_file_path is None:
        get_logger()  # Initialize the logger to set the log file path
    return log_file_path


def print_log_file_path():
    """Print log file path if debug is enabled."""
    if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) == "true":
        log_file_path = get_log_file_path()
        log_warning(f"'debug_enabled' is on ({log_file_path})\n")


def user_log_dir(app_name):
    if platform.system() == "Windows":
        # On Windows, use the AppData/Local/<AppName>/Logs folder
        base_dir = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        log_dir = os.path.join(base_dir, app_name, "Logs")
        # Check for Windows sandbox environment (e.g., running in Windows Sandbox)
        if os.path.realpath(log_dir) != log_dir:
            # In sandbox, use the expanded path directly (avoid realpath redirection issues)
            log_dir = os.path.realpath(log_dir)
    elif platform.system() == "Darwin":
        # On macOS, use the Library/Logs/<AppName> folder
        base_dir = os.path.expanduser("~/Library/Logs")
        log_dir = os.path.join(base_dir, app_name)
    else:
        # On Linux, use the ~/.local/state/<AppName>/log folder
        base_dir = os.getenv("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
        log_dir = os.path.join(base_dir, app_name, "log")

    return log_dir


def _parse_json_into_single_line(json_text):
    try:
        parsed_json = json.loads(json_text)
        compact_json = json.dumps(parsed_json, separators=(",", ":"))
        return compact_json
    except json.JSONDecodeError:
        return "Failed to parse JSON response"
