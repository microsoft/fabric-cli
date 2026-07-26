# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import importlib.metadata
from unittest.mock import patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.utils.fab_user_agent import (
    _get_host_app,
    build_user_agent,
    resolve_library_user_agent,
)


@patch("fabric_cli.utils.fab_user_agent.platform.python_version", return_value="3.11.5")
@patch("fabric_cli.utils.fab_user_agent.platform.release", return_value="5.4.0")
@patch("fabric_cli.utils.fab_user_agent.platform.system", return_value="Linux")
def test_build_user_agent_without_host_app(
    mock_system, mock_release, mock_python_version, monkeypatch
):
    """build_user_agent returns the base token when no host app env is set."""
    monkeypatch.delenv(fab_constant.FAB_HOST_APP_ENV_VAR, raising=False)
    monkeypatch.delenv(fab_constant.FAB_HOST_APP_VERSION_ENV_VAR, raising=False)

    result = build_user_agent("deploy")

    assert result == (
        f"{fab_constant.API_USER_AGENT}/{fab_constant.FAB_VERSION} "
        f"(deploy; Linux/5.4.0; Python/3.11.5)"
    )


@patch("fabric_cli.utils.fab_user_agent.platform.python_version", return_value="3.11.5")
@patch("fabric_cli.utils.fab_user_agent.platform.release", return_value="5.4.0")
@patch("fabric_cli.utils.fab_user_agent.platform.system", return_value="Linux")
def test_build_user_agent_appends_host_app_suffix(
    mock_system, mock_release, mock_python_version, monkeypatch
):
    """build_user_agent appends the validated host-app suffix when env is set."""
    monkeypatch.setenv(
        fab_constant.FAB_HOST_APP_ENV_VAR, "Fabric-AzureDevops-Extension"
    )
    monkeypatch.setenv(fab_constant.FAB_HOST_APP_VERSION_ENV_VAR, "1.2.0")

    result = build_user_agent("create")

    assert result == (
        f"{fab_constant.API_USER_AGENT}/{fab_constant.FAB_VERSION} "
        f"(create; Linux/5.4.0; Python/3.11.5)"
        f" host-app/fabric-azuredevops-extension/1.2.0"
    )


def test_resolve_library_user_agent_uses_installed_version():
    """resolve_library_user_agent returns '<name>/<installed version>'."""
    with patch(
        "fabric_cli.utils.fab_user_agent.importlib.metadata.version",
        return_value="9.8.7",
    ):
        result = resolve_library_user_agent("some-package", "ms-some-package")

    assert result == "ms-some-package/9.8.7"


def test_resolve_library_user_agent_none_when_package_missing():
    """resolve_library_user_agent returns None when metadata is missing."""
    with patch(
        "fabric_cli.utils.fab_user_agent.importlib.metadata.version",
        side_effect=importlib.metadata.PackageNotFoundError,
    ):
        result = resolve_library_user_agent("missing-package", "ms-missing")

    assert result is None


@pytest.mark.parametrize(
    "host_app_env, host_app_version_env, expected_suffix",
    [
        (
            "Fabric-AzureDevops-Extension",
            None,
            " host-app/fabric-azuredevops-extension",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.2.0",
            " host-app/fabric-azuredevops-extension/1.2.0",
        ),
        (
            "fabric-azuredevops-extension",
            "1.2.0",
            " host-app/fabric-azuredevops-extension/1.2.0",
        ),
        ("Invalid-App", "1.0.0", ""),
        ("", None, ""),
        (None, None, ""),
        # Invalid version format - host app is still included but version is silently dropped
        (
            "Fabric-AzureDevops-Extension",
            "1.2.0.4",  # Invalid format
            " host-app/fabric-azuredevops-extension",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.2.a",  # Invalid format
            " host-app/fabric-azuredevops-extension",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "a.b.c",  # Invalid format
            " host-app/fabric-azuredevops-extension",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1",  # valid format
            " host-app/fabric-azuredevops-extension/1",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.2",  # valid format
            " host-app/fabric-azuredevops-extension/1.2",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.0.0",  # valid format
            " host-app/fabric-azuredevops-extension/1.0.0",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.0.0-rc.1",  # valid format
            " host-app/fabric-azuredevops-extension/1.0.0-rc.1",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.0.0-alpha",  # valid format
            " host-app/fabric-azuredevops-extension/1.0.0-alpha",
        ),
        (
            "Fabric-AzureDevops-Extension",
            "1.0.0-beta",  # valid format
            " host-app/fabric-azuredevops-extension/1.0.0-beta",
        ),
    ],
)
def test_get_host_app(host_app_env, host_app_version_env, expected_suffix, monkeypatch):
    """Test the _get_host_app helper function."""
    if host_app_env is not None:
        monkeypatch.setenv(fab_constant.FAB_HOST_APP_ENV_VAR, host_app_env)
    else:
        monkeypatch.delenv(fab_constant.FAB_HOST_APP_ENV_VAR, raising=False)

    if host_app_version_env is not None:
        monkeypatch.setenv(
            fab_constant.FAB_HOST_APP_VERSION_ENV_VAR, host_app_version_env
        )
    else:
        monkeypatch.delenv(fab_constant.FAB_HOST_APP_VERSION_ENV_VAR, raising=False)

    result = _get_host_app()

    assert result == expected_suffix
