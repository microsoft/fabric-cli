# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for fab_version_check module."""

from unittest.mock import MagicMock, patch

import requests

from fabric_cli import __version__
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_version_check


def _increment_version(component: str = "major") -> str:
    """Helper to create a newer version by incrementing a component.
    
    Args:
        component: Which version component to increment ("major", "minor", or "patch")
    
    Returns:
        A version string that is newer than __version__
    """
    parts = [int(x) for x in __version__.split(".")]
    if component == "major":
        return f"{parts[0] + 1}.0.0"
    elif component == "minor":
        return f"{parts[0]}.{parts[1] + 1}.0"
    elif component == "patch":
        return f"{parts[0]}.{parts[1]}.{parts[2] + 1}"
    raise ValueError(f"Unknown component: {component}")


def _decrement_version() -> str:
    """Helper to create an older version.
    
    Returns:
        A version string that is older than __version__
    """
    parts = [int(x) for x in __version__.split(".")]
    # If patch > 0, decrement it
    if parts[2] > 0:
        return f"{parts[0]}.{parts[1]}.{parts[2] - 1}"
    # If minor > 0, decrement minor and set patch to 0
    elif parts[1] > 0:
        return f"{parts[0]}.{parts[1] - 1}.0"
    # If major > 0, decrement major and set others to 0
    elif parts[0] > 0:
        return f"{parts[0] - 1}.0.0"
    # Edge case: version is 0.0.0 - can't go lower, just return it
    return "0.0.0"


@patch("fabric_cli.utils.fab_version_check.requests.get")
def test_cli_version_fetch_pypi_success(mock_get):
    """Should return version when PyPI request succeeds."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"info": {"version": "2.0.0"}}
    mock_get.return_value = mock_response

    result = fab_version_check._fetch_latest_version_from_pypi()

    assert result == "2.0.0"
    mock_get.assert_called_once_with(
        fab_constant.VERSION_CHECK_PYPI_URL,
        timeout=fab_constant.VERSION_CHECK_TIMEOUT_SECONDS,
    )


@patch("fabric_cli.utils.fab_version_check.requests.get")
def test_cli_version_fetch_pypi_network_error_failure(mock_get):
    """Should return None when PyPI request fails (network error)."""
    mock_get.side_effect = requests.ConnectionError("Network error")

    result = fab_version_check._fetch_latest_version_from_pypi()

    assert result is None


@patch("fabric_cli.utils.fab_version_check.requests.get")
def test_cli_version_fetch_pypi_http_error_failure(mock_get):
    """Should return None when PyPI returns non-200 status code."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    mock_get.return_value = mock_response

    result = fab_version_check._fetch_latest_version_from_pypi()

    assert result is None


@patch("fabric_cli.utils.fab_version_check.requests.get")
def test_cli_version_fetch_pypi_invalid_json_failure(mock_get):
    """Should return None when PyPI returns invalid JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    result = fab_version_check._fetch_latest_version_from_pypi()

    assert result is None


@patch("fabric_cli.utils.fab_version_check.requests.get")
def test_cli_version_fetch_pypi_missing_keys_failure(mock_get):
    """Should return None when PyPI response is missing expected keys."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"data": {}}  # Missing "info" key
    mock_get.return_value = mock_response

    result = fab_version_check._fetch_latest_version_from_pypi()

    assert result is None


def test_cli_version_compare_newer_major_success():
    """Should return True when major version is newer."""
    result = fab_version_check._is_pypi_version_newer(_increment_version("major"))
    assert result is True


def test_cli_version_compare_newer_minor_success():
    """Should return True when minor version is newer."""
    result = fab_version_check._is_pypi_version_newer(_increment_version("minor"))
    assert result is True


def test_cli_version_compare_newer_patch_success():
    """Should return True when patch version is newer."""
    result = fab_version_check._is_pypi_version_newer(_increment_version("patch"))
    assert result is True


def test_cli_version_compare_same_version_failure():
    """Should return False when versions are the same."""
    result = fab_version_check._is_pypi_version_newer(__version__)
    assert result is False


def test_cli_version_compare_older_version_failure():
    """Should return False when latest is older."""
    result = fab_version_check._is_pypi_version_newer(_decrement_version())
    assert result is False


def test_cli_version_compare_invalid_format_failure():
    """Should return False when version format is invalid."""
    result = fab_version_check._is_pypi_version_newer("invalid.version")
    assert result is False


def test_cli_version_compare_none_version_failure():
    """Should return False when version is None."""
    result = fab_version_check._is_pypi_version_newer(None)
    assert result is False


@patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
def test_cli_version_check_disabled_by_config_success(
    mock_fetch, mock_fab_set_state_config, mock_questionary_print
):
    """Should not display notification when update checks are disabled by config."""
    newer_version = _increment_version("major")
    mock_fab_set_state_config(fab_constant.FAB_CHECK_UPDATES, "false")
    mock_fetch.return_value = newer_version

    fab_version_check.check_and_notify_update()

    mock_questionary_print.assert_not_called()


@patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
def test_cli_version_check_new_version_available_success(
    mock_fetch, mock_fab_set_state_config, mock_questionary_print
):
    """Should display notification when newer version is available."""
    newer_version = _increment_version("major")
    mock_fab_set_state_config(fab_constant.FAB_CHECK_UPDATES, "true")
    mock_fetch.return_value = newer_version

    fab_version_check.check_and_notify_update()

    mock_questionary_print.assert_called()
    call_msg = str(mock_questionary_print.call_args)
    assert newer_version in call_msg
    assert "pip install --upgrade" in call_msg


@patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
def test_cli_version_check_same_version_success(
    mock_fetch, mock_fab_set_state_config, mock_questionary_print
):
    """Should not display notification when on latest version."""
    mock_fab_set_state_config(fab_constant.FAB_CHECK_UPDATES, "true")
    mock_fetch.return_value = __version__

    fab_version_check.check_and_notify_update()

    mock_questionary_print.assert_not_called()


@patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
def test_cli_version_check_fetch_failure(
    mock_fetch, mock_fab_set_state_config, mock_questionary_print
):
    """Should not display notification when PyPI fetch fails."""
    mock_fab_set_state_config(fab_constant.FAB_CHECK_UPDATES, "true")
    mock_fetch.return_value = None  # Simulate fetch failure

    fab_version_check.check_and_notify_update()

    mock_questionary_print.assert_not_called()


@patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
def test_cli_version_check_older_version_success(
    mock_fetch, mock_fab_set_state_config, mock_questionary_print
):
    """Should not display notification when PyPI version is older."""
    mock_fab_set_state_config(fab_constant.FAB_CHECK_UPDATES, "true")
    mock_fetch.return_value = _decrement_version()

    fab_version_check.check_and_notify_update()

    mock_questionary_print.assert_not_called()
