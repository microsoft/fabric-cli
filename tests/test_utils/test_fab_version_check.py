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


class TestFetchLatestVersionFromPyPI:
    """Test _fetch_latest_version_from_pypi logic."""

    @patch("fabric_cli.utils.fab_version_check.requests.get")
    def test_fetch_success(self, mock_get):
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
    def test_fetch_failure(self, mock_get):
        """Should return None when PyPI request fails (network error)."""
        mock_get.side_effect = requests.ConnectionError("Network error")

        result = fab_version_check._fetch_latest_version_from_pypi()

        assert result is None

    @patch("fabric_cli.utils.fab_version_check.requests.get")
    def test_fetch_failure_http_error(self, mock_get):
        """Should return None when PyPI returns non-200 status code."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        result = fab_version_check._fetch_latest_version_from_pypi()

        assert result is None

    @patch("fabric_cli.utils.fab_version_check.requests.get")
    def test_fetch_failure_invalid_json(self, mock_get):
        """Should return None when PyPI returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = fab_version_check._fetch_latest_version_from_pypi()

        assert result is None

    @patch("fabric_cli.utils.fab_version_check.requests.get")
    def test_fetch_failure_missing_keys(self, mock_get):
        """Should return None when PyPI response is missing expected keys."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": {}}  # Missing "info" key
        mock_get.return_value = mock_response

        result = fab_version_check._fetch_latest_version_from_pypi()

        assert result is None


class TestIsPyPIVersionNewer:
    """Test _is_pypi_version_newer logic."""

    def test_newer_major_version(self):
        """Should return True when major version is newer."""
        result = fab_version_check._is_pypi_version_newer(_increment_version("major"))
        assert result is True

    def test_newer_minor_version(self):
        """Should return True when minor version is newer."""
        result = fab_version_check._is_pypi_version_newer(_increment_version("minor"))
        assert result is True

    def test_newer_patch_version(self):
        """Should return True when patch version is newer."""
        result = fab_version_check._is_pypi_version_newer(_increment_version("patch"))
        assert result is True

    def test_same_version(self):
        """Should return False when versions are the same."""
        result = fab_version_check._is_pypi_version_newer(__version__)
        assert result is False

    def test_older_version(self):
        """Should return False when latest is older."""
        result = fab_version_check._is_pypi_version_newer(_decrement_version())
        assert result is False

    def test_invalid_version_format(self):
        """Should return False when version format is invalid."""
        result = fab_version_check._is_pypi_version_newer("invalid.version")
        assert result is False

    def test_none_version(self):
        """Should return False when version is None."""
        result = fab_version_check._is_pypi_version_newer(None)
        assert result is False


class TestCheckAndNotifyUpdate:
    """Test check_and_notify_update main function."""

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_disabled_by_config(self, mock_get_config):
        """Should not check when user has disabled updates."""
        mock_get_config.return_value = "false"

        fab_version_check.check_and_notify_update()

        # Should call get_config for check_updates setting
        assert any(
            call[0][0] == fab_constant.FAB_CHECK_UPDATES
            for call in mock_get_config.call_args_list
        )

    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_new_version_available(self, mock_get_config, mock_fetch):
        """Should display notification when newer version is available."""
        newer_version = _increment_version("major")
        mock_get_config.return_value = "true"
        mock_fetch.return_value = newer_version

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should display notification
            mock_ui.print_grey.assert_called()
            call_msg = str(mock_ui.print_grey.call_args)
            assert newer_version in call_msg
            assert "pip install --upgrade" in call_msg

    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_same_version(self, mock_get_config, mock_fetch):
        """Should not display notification when on latest version."""
        mock_get_config.return_value = "true"
        mock_fetch.return_value = __version__

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should not display notification
            mock_ui.print_grey.assert_not_called()

    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_fetch_fails(self, mock_get_config, mock_fetch):
        """Should not display notification when PyPI fetch fails."""
        mock_get_config.return_value = "true"
        mock_fetch.return_value = None  # Simulate fetch failure

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should not display notification
            mock_ui.print_grey.assert_not_called()

    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_older_version(self, mock_get_config, mock_fetch):
        """Should not display notification when PyPI version is older."""
        mock_get_config.return_value = "true"
        mock_fetch.return_value = _decrement_version()

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should not display notification
            mock_ui.print_grey.assert_not_called()
