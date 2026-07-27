# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import importlib.metadata
import os
import platform
import re
from typing import Optional

from fabric_cli.core import fab_constant

_HOST_APP_VERSION_RE = re.compile(r"\d+(\.\d+){0,2}(-[a-zA-Z0-9\.-]+)?")


def build_user_agent(ctxt_cmd: str) -> str:
    """Build the User-Agent header for API requests.

    Example:
        ms-fabric-cli/1.0.0 (create; Windows/10; Python/3.10.2) ado/2.0.0
    """
    user_agent = (
        f"{fab_constant.API_USER_AGENT}/{fab_constant.FAB_VERSION} "
        f"({ctxt_cmd}; {platform.system()}/{platform.release()}; "
        f"Python/{platform.python_version()})"
    )
    host_app = _get_host_app()
    if host_app:
        user_agent += host_app

    return user_agent


def resolve_library_user_agent(
    package_name: str, user_agent_name: str
) -> Optional[str]:
    """Build a ``<name>/<installed version>`` User-Agent token for a host library.

    Resolves the installed distribution version so a caller can stamp telemetry with the
    version the CLI actually ships (e.g. ``ms-fabric-cicd/1.2.0``). Returns None if the
    package metadata cannot be resolved.

    Args:
        package_name: The distribution name to resolve the version from (e.g., ``fabric-cicd``).
        user_agent_name: The User-Agent identity to use (e.g., ``ms-fabric-cicd``).
    """
    try:
        version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None
    return f"{user_agent_name}/{version}"


def _get_host_app() -> str:
    """Get the HostApp suffix for the User-Agent header based on environment variables.

    Returns an empty string if the environment variable is not set or has an invalid value.
    """
    _host_app_in_env = os.environ.get(fab_constant.FAB_HOST_APP_ENV_VAR)
    if not _host_app_in_env:
        return ""

    host_app_name = next(
        (
            allowed_app
            for allowed_app in fab_constant.ALLOWED_FAB_HOST_APP_VALUES
            if _host_app_in_env.lower() == allowed_app.lower()
        ),
        None,
    )

    if not host_app_name:
        return ""

    host_app = f" {host_app_name.lower()}"

    # Check for optional version
    host_app_version = os.environ.get(fab_constant.FAB_HOST_APP_VERSION_ENV_VAR)

    # validate host_app_version format is a valid version (e.g., 1.0.0)
    if host_app_version and _HOST_APP_VERSION_RE.fullmatch(host_app_version):
        host_app += f"/{host_app_version}"
    return host_app
