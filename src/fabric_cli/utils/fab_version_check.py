# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Version update checking for Fabric CLI.

This module checks PyPI for newer versions of ms-fabric-cli and displays
a notification to the user if an update is available.
"""

from typing import Optional

import requests

from fabric_cli import __version__
from fabric_cli.core import fab_constant, fab_logger, fab_state_config
from fabric_cli.utils import fab_ui


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
        response.raise_for_status()
        return response.json()["info"]["version"]
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        # Silently fail - don't interrupt user experience for version checks
        fab_logger.log_debug(f"Failed to fetch version from PyPI: {e}")
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
        # Conservative: don't show notification version could not be parsed
        return False


def check_and_notify_update() -> None:
    """
    Check for CLI updates and display notification if a newer version is available.

    This function:
    - Respects user's check_updates config setting
    - Checks PyPI on every login for the latest version
    - Displays notification if an update is available
    - Fails silently if PyPI is unreachable
    """
    check_enabled = fab_state_config.get_config(fab_constant.FAB_CHECK_UPDATES)
    if check_enabled == "false":
        fab_logger.log_debug("Version check disabled by user configuration")
        return

    fab_logger.log_debug("Checking PyPI for latest version")
    latest_version = _fetch_latest_version_from_pypi()

    if latest_version and _is_pypi_version_newer(latest_version):
        msg = (
            f"\n[notice] A new release of fab is available: {__version__} → {latest_version}\n"
            "[notice] To update, run: pip install --upgrade ms-fabric-cli\n"
        )
        fab_ui.print_grey(msg)
    elif latest_version:
        fab_logger.log_debug(f"Already on latest version: {__version__}")
    else:
        fab_logger.log_debug("Could not fetch latest version from PyPI")
