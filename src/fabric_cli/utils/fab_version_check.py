# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Version update checking for Fabric CLI.

This module checks PyPI for newer versions of ms-fabric-cli and displays
a notification to the user if an update is available. Checks are cached
according to VERSION_CHECK_INTERVAL_HOURS to minimize PyPI API calls.
"""

from datetime import datetime, timedelta
from typing import Optional

import requests

from fabric_cli import __version__
from fabric_cli.core import fab_constant, fab_logger, fab_state_config
from fabric_cli.utils import fab_ui


def _should_check_pypi() -> bool:
    """
    Determine if we should check PyPI based on last check time.

    Returns:
        True if more than VERSION_CHECK_INTERVAL_HOURS hours have passed since last check, False otherwise.
    """
    last_check_str = fab_state_config.get_config(fab_constant.FAB_PYPI_CACHE_TIMESTAMP)

    if not last_check_str:
        return True

    try:
        last_check_time = datetime.fromisoformat(last_check_str)
        time_since_check = datetime.now() - last_check_time
        return time_since_check > timedelta(hours=fab_constant.VERSION_CHECK_INTERVAL_HOURS)
    except (ValueError, TypeError):
        # Invalid timestamp format, check again
        return True


def _fetch_latest_version_from_pypi() -> Optional[str]:
    """
    Fetch the latest version from PyPI JSON API.

    Returns:
        Latest version string if successful, None otherwise.
    """
    try:
        response = requests.get(
            fab_constant.VERSION_CHECK_PYPI_URL,
            timeout=fab_constant.VERSION_CHECK_TIMEOUT_SECONDS
        )

        if response.status_code == 200:
            data = response.json()
            return data["info"]["version"]
    except Exception:
        # Silently fail - don't interrupt user experience for version checks
        pass

    return None


def _is_pypi_version_newer(pypi_version: str) -> bool:
    """
    Compare PyPI version with current version to determine if an update is available.

    Args:
        pypi_version: Version string from PyPI

    Returns:
        True if PyPI version is newer than current installed version
    """
    try:
        # Parse versions as tuples (e.g., "1.3.0" -> (1, 3, 0))
        current_parts = tuple(int(x) for x in __version__.split("."))
        pypi_parts = tuple(int(x) for x in pypi_version.split("."))
        return pypi_parts > current_parts
    except (ValueError, AttributeError):
        # Conservative: don't show notification if we can't reliably parse versions
        return False


def _update_pypi_cache(latest_version: Optional[str] = None) -> None:
    """
    Update the PyPI cache timestamp and optionally store the latest version.

    Args:
        latest_version: Latest version from PyPI to cache
    """
    fab_state_config.set_config(
        fab_constant.FAB_PYPI_CACHE_TIMESTAMP, datetime.now().isoformat()
    )

    if latest_version:
        fab_state_config.set_config(fab_constant.FAB_PYPI_LATEST_VERSION, latest_version)


def check_and_notify_update() -> None:
    """
    Check for CLI updates and display notification if a newer version is available.

    This function:
    - Respects user's check_updates config setting
    - Hits PyPI a maximum of once per week to refresh cached version
    - Checks cached version on every login (fast)
    - Displays notification whenever an update is available
    - Fails silently if PyPI is unreachable
    """
    # Check if user has disabled update checks
    check_enabled = fab_state_config.get_config(fab_constant.FAB_CHECK_UPDATES)
    if check_enabled == "false":
        fab_logger.log_debug("Version check disabled by user configuration")
        return

    # Try to refresh from PyPI if interval has passed
    if _should_check_pypi():
        fab_logger.log_debug("Checking PyPI for latest version")
        latest_version = _fetch_latest_version_from_pypi()
        # Update cache regardless of result to avoid repeated failures
        _update_pypi_cache(latest_version)
    else:
        fab_logger.log_debug("Using cached version (PyPI check interval not reached)")

    # Always check cached version and notify if update available
    cached_version = fab_state_config.get_config(fab_constant.FAB_PYPI_LATEST_VERSION)
    if cached_version and _is_pypi_version_newer(cached_version):
        fab_logger.log_debug(f"New version available: {cached_version}")
        fab_ui.print_grey(
            f"\n[notice] A new release of fab is available: {__version__} → {cached_version}"
        )
        fab_ui.print_grey(
            "[notice] To update, run: pip install --upgrade ms-fabric-cli\n"
        )
    else:
        fab_logger.log_debug(f"Already on latest version: {__version__}")
