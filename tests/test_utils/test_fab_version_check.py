# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for fab_version_check module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

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


class TestShouldCheckPyPI:
    """Test _should_check_pypi logic."""

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_should_check_no_previous_check(self, mock_get_config):
        """Should check PyPI when no previous check exists."""
        mock_get_config.return_value = None

        result = fab_version_check._should_check_pypi()

        assert result is True

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_should_check_invalid_timestamp(self, mock_get_config):
        """Should check PyPI when timestamp is invalid."""
        mock_get_config.return_value = "invalid-timestamp"

        result = fab_version_check._should_check_pypi()

        assert result is True

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_should_check_old_timestamp(self, mock_get_config):
        """Should check PyPI when last check was older than configured interval."""
        # Use interval + 1 hour to ensure we're past the threshold
        old_time = datetime.now() - timedelta(
            hours=fab_constant.VERSION_CHECK_INTERVAL_HOURS + 1
        )
        mock_get_config.return_value = old_time.isoformat()

        result = fab_version_check._should_check_pypi()

        assert result is True

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_should_not_check_recent_timestamp(self, mock_get_config):
        """Should not check PyPI when last check was within configured interval."""
        # Use half the interval to ensure we're well within the threshold
        recent_time = datetime.now() - timedelta(
            hours=fab_constant.VERSION_CHECK_INTERVAL_HOURS / 2
        )
        mock_get_config.return_value = recent_time.isoformat()

        result = fab_version_check._should_check_pypi()

        assert result is False


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
        """Should return None when PyPI request fails (any exception)."""
        mock_get.side_effect = Exception("Network error")

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


class TestUpdatePyPICache:
    """Test _update_pypi_cache logic."""

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.set_config")
    def test_update_timestamp_only(self, mock_set_config):
        """Should update timestamp when no version provided."""
        fab_version_check._update_pypi_cache()

        # Should be called once for timestamp
        assert mock_set_config.call_count == 1
        call_args = mock_set_config.call_args_list[0]
        assert call_args[0][0] == fab_constant.FAB_PYPI_CACHE_TIMESTAMP
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(call_args[0][1])

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.set_config")
    def test_update_with_version(self, mock_set_config):
        """Should update both timestamp and version when version provided."""
        fab_version_check._update_pypi_cache("2.0.0")

        # Should be called twice: once for timestamp, once for version
        assert mock_set_config.call_count == 2

        # Check that both keys were set
        call_keys = [call[0][0] for call in mock_set_config.call_args_list]
        assert fab_constant.FAB_PYPI_CACHE_TIMESTAMP in call_keys
        assert fab_constant.FAB_PYPI_LATEST_VERSION in call_keys


class TestCheckAndNotifyUpdate:
    """Test check_and_notify_update main function."""

    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_disabled_by_config(self, mock_get_config):
        """Should not check when user has disabled updates."""
        mock_get_config.return_value = "false"

        fab_version_check.check_and_notify_update()

        # Should call get_config for check_updates setting (and potentially debug_enabled)
        # Just verify it was called with FAB_CHECK_UPDATES at least once
        assert any(
            call[0][0] == fab_constant.FAB_CHECK_UPDATES
            for call in mock_get_config.call_args_list
        )

    @patch("fabric_cli.utils.fab_version_check._update_pypi_cache")
    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check._should_check_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_check_pypi_new_version_available(
        self,
        mock_get_config,
        mock_should_check,
        mock_fetch,
        mock_update_state,
    ):
        """Should display notification when newer version is available."""
        newer_version = _increment_version("major")
        
        def get_config_side_effect(key):
            if key == fab_constant.FAB_CHECK_UPDATES:
                return "true"
            elif key == fab_constant.FAB_PYPI_LATEST_VERSION:
                return newer_version
            return None
        
        mock_get_config.side_effect = get_config_side_effect
        mock_should_check.return_value = True
        mock_fetch.return_value = newer_version

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should display notification
            assert mock_ui.print_grey.call_count == 2
            assert newer_version in str(mock_ui.print_grey.call_args_list[0])
            assert "pip install --upgrade" in str(mock_ui.print_grey.call_args_list[1])

        # Should update state
        mock_update_state.assert_called_once_with(newer_version)

    @patch("fabric_cli.utils.fab_version_check._update_pypi_cache")
    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check._should_check_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_check_pypi_same_version(
        self,
        mock_get_config,
        mock_should_check,
        mock_fetch,
        mock_update_state,
    ):
        """Should not display notification when on latest version."""
        mock_get_config.side_effect = lambda key: (
            "true" if key == fab_constant.FAB_CHECK_UPDATES else None
        )
        mock_should_check.return_value = True
        mock_fetch.return_value = __version__

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should not display notification
            mock_ui.print_grey.assert_not_called()

        # Should still update state
        mock_update_state.assert_called_once()

    @patch("fabric_cli.utils.fab_version_check._update_pypi_cache")
    @patch("fabric_cli.utils.fab_version_check._fetch_latest_version_from_pypi")
    @patch("fabric_cli.utils.fab_version_check._should_check_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_check_pypi_fetch_fails(
        self,
        mock_get_config,
        mock_should_check,
        mock_fetch,
        mock_update_state,
    ):
        """Should not display notification when PyPI fetch fails."""
        mock_get_config.side_effect = lambda key: (
            "true" if key == fab_constant.FAB_CHECK_UPDATES else None
        )
        mock_should_check.return_value = True
        mock_fetch.return_value = None  # Simulate fetch failure

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should not display notification
            mock_ui.print_grey.assert_not_called()

        # Should still update state to avoid repeated failures
        mock_update_state.assert_called_once_with(None)

    @patch("fabric_cli.utils.fab_version_check._should_check_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_use_cached_version(self, mock_get_config, mock_should_check):
        """Should use cached version when check is not needed."""
        newer_version = _increment_version("major")

        def get_config_side_effect(key):
            if key == fab_constant.FAB_CHECK_UPDATES:
                return "true"
            elif key == fab_constant.FAB_PYPI_LATEST_VERSION:
                return newer_version
            return None

        mock_get_config.side_effect = get_config_side_effect
        mock_should_check.return_value = False  # Use cache

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should display notification using cached version
            assert mock_ui.print_grey.call_count == 2
            assert newer_version in str(mock_ui.print_grey.call_args_list[0])

    @patch("fabric_cli.utils.fab_version_check._should_check_pypi")
    @patch("fabric_cli.utils.fab_version_check.fab_state_config.get_config")
    def test_no_cached_version(self, mock_get_config, mock_should_check):
        """Should not display notification when no cached version exists."""

        def get_config_side_effect(key):
            if key == fab_constant.FAB_CHECK_UPDATES:
                return "true"
            return None

        mock_get_config.side_effect = get_config_side_effect
        mock_should_check.return_value = False  # Use cache

        with patch("fabric_cli.utils.fab_version_check.fab_ui") as mock_ui:
            fab_version_check.check_and_notify_update()

            # Should not display notification (no cached version)
            mock_ui.print_grey.assert_not_called()
