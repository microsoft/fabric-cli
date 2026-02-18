# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import uuid
from argparse import Namespace
from unittest.mock import patch

import pytest

from fabric_cli.client.fab_api_client import (
    _get_host_app,
    _transform_workspace_url_for_private_link_if_needed,
    do_request,
)
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricAPIError


@pytest.mark.parametrize("private_link_enabled_config_value", [True, "True", "true"])
def test_transform_workspace_url_success(
    mock_fab_set_state_config, private_link_enabled_config_value
):
    """Test successful transformation of workspace URL"""
    workspace_id = str(uuid.uuid4())
    workspace_id_clean = workspace_id.replace("-", "")
    uri = f"workspaces/{workspace_id}/items"
    url = f"api.fabric.mock-test.com"

    mock_fab_set_state_config(
        fab_constant.FAB_WS_PRIVATE_LINKS_ENABLED, private_link_enabled_config_value
    )

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)

    expected = (
        f"{workspace_id_clean}.z{workspace_id_clean[:2]}.w.api.fabric.mock-test.com"
    )
    assert result == expected


@pytest.mark.parametrize(
    "private_link_enabled_config_value", [False, None, "", "false"]
)
def test_transform_workspace_url_disabled_feature_success(
    mock_fab_set_state_config, private_link_enabled_config_value
):
    """Test that transformation is skipped when feature is disabled"""
    workspace_id = str(uuid.uuid4())
    uri = f"workspaces/{workspace_id}/items"
    url = f"api.fabric.mock-test.com"

    mock_fab_set_state_config(
        fab_constant.FAB_WS_PRIVATE_LINKS_ENABLED, private_link_enabled_config_value
    )
    result = _transform_workspace_url_for_private_link_if_needed(url, uri)

    assert result == url


def test_transform_workspace_url_admin_api_skipped_success(setup_default_private_links):
    """Test that admin APIs are skipped"""
    workspace_id = str(uuid.uuid4())
    uri = f"aDMin/workspaces/{workspace_id}/items"
    url = f"api.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)
    assert result == url  # Should return original URL unchanged


def test_transform_workspace_url_no_workspace_id_success(setup_default_private_links):
    """Test that URLs without workspace ID are not transformed"""
    uri = "v1/items/list"
    url = f"api.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)
    assert result == url  # Should return original URL unchanged


def test_should_not_transform_workspace_url_when_invalid_workspace_id_format_success(
    setup_default_private_links,
):
    """Test that URLs with invalid workspace ID format are not transformed"""
    uri = "v1/workspaces/invalid-id/items"
    url = f"api.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)
    assert result == url  # Should return original URL unchanged


def test_transform_workspace_url_case_insensitive_success(setup_default_private_links):
    """Test that workspace ID matching is case insensitive"""
    workspace_id = str(uuid.uuid4()).upper()
    workspace_id_clean = workspace_id.replace("-", "")
    uri = f"V1/WORKSPACES/{workspace_id}/ITEMS"
    url = f"api.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)
    expected = (
        f"{workspace_id_clean}.z{workspace_id_clean[:2]}.w.api.fabric.mock-test.com"
    )
    assert result == expected


def test_transform_workspace_url_different_region_codes_success(
    setup_default_private_links,
):
    """Test transformation with different region codes (first 2 chars of workspace ID)"""
    test_cases = [
        (f"AB{str(uuid.uuid4())[2:]}", "zAB"),
        (f"12{str(uuid.uuid4())[2:]}", "z12"),
        (f"cd{str(uuid.uuid4())[2:]}", "zcd"),
        (f"99{str(uuid.uuid4())[2:]}", "z99"),
    ]

    for workspace_id, expected_suffix in test_cases:
        workspace_id_clean = workspace_id.replace("-", "")
        uri = f"v1/workspaces/{workspace_id}/items"
        url = f"api.fabric.mock-test.com"

        result = _transform_workspace_url_for_private_link_if_needed(url, uri)

        expected = f"{workspace_id_clean}.{expected_suffix}.w.api.fabric.mock-test.com"
        assert result == expected, f"Failed for workspace_id: {workspace_id}"


def test_transform_workspace_url_complex_path_success(setup_default_private_links):
    """Test transformation with complex URI path"""
    workspace_id = str(uuid.uuid4())
    workspace_id_clean = workspace_id.replace("-", "")
    uri = f"v1/workspaces/{workspace_id}/items/456/definitions/789"
    url = f"api.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)

    expected = (
        f"{workspace_id_clean}.z{workspace_id_clean[:2]}.w.api.fabric.mock-test.com"
    )
    assert result == expected


# OneLake-specific tests for private link transformation
def test_transform_onelake_url_with_workspace_id_as_first_segment_success(
    setup_default_private_links,
):
    """Test OneLake URL transformation when workspace ID is the first segment"""
    workspace_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    workspace_id_clean = workspace_id.replace("-", "")
    uri = f"{workspace_id}/{item_id}/Files/test.txt"
    url = "onelake.dfs.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, is_onelake_api=True
    )

    expected = f"{workspace_id_clean}.z{workspace_id_clean[:2]}.{url}"
    assert result == expected


def test_transform_onelake_url_with_fabric_workspaces_pattern_no_transformation_success(
    setup_default_private_links,
):
    """Test OneLake URL is NOT transformed when using Fabric workspaces pattern (OneLake only handles first segment GUID)"""
    workspace_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    uri = f"workspaces/{workspace_id}/items/{item_id}/dataAccessRoles"
    url = "onelake.dfs.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, is_onelake_api=True
    )

    # Should return original URL unchanged since OneLake doesn't handle workspaces pattern
    assert result == url


def test_transform_onelake_url_no_transformation_when_no_guid_first_segment_success(
    setup_default_private_links,
):
    uri = "Files/test.txt"
    url = "onelake.dfs.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, is_onelake_api=True
    )

    assert result == url  # Should return original URL unchanged


def test_transform_onelake_url_no_transformation_when_invalid_guid_first_segment_success(
    setup_default_private_links,
):
    uri = "invalid-guid/Files/test.txt"
    url = "onelake.dfs.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, is_onelake_api=True
    )

    assert result == url  # Should return original URL unchanged


def test_transform_onelake_url_case_insensitive_workspace_id_success(
    setup_default_private_links,
):
    workspace_id = str(uuid.uuid4()).upper()
    item_id = str(uuid.uuid4())
    workspace_id_clean = workspace_id.replace("-", "")
    uri = f"{workspace_id}/{item_id}/Files/test.txt"
    url = "onelake.dfs.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, is_onelake_api=True
    )

    expected = f"{workspace_id_clean}.z{workspace_id_clean[:2]}.{url}"
    assert result == expected


def test_transform_onelake_url_different_region_codes_success(
    setup_default_private_links,
):
    test_cases = [
        (f"12{str(uuid.uuid4())[2:]}", "z12"),
        (f"ab{str(uuid.uuid4())[2:]}", "zab"),
        (f"CD{str(uuid.uuid4())[2:]}", "zCD"),
        (f"99{str(uuid.uuid4())[2:]}", "z99"),
    ]

    for workspace_id, expected_suffix in test_cases:
        workspace_id_clean = workspace_id.replace("-", "")
        item_id = str(uuid.uuid4())
        uri = f"{workspace_id}/{item_id}/Files/test.txt"
        url = "onelake.dfs.fabric.mock-test.com"

        result = _transform_workspace_url_for_private_link_if_needed(
            url, uri, is_onelake_api=True
        )

        expected = f"{workspace_id_clean}.{expected_suffix}.{url}"
        assert result == expected, f"Failed for workspace_id: {workspace_id}"


@pytest.mark.parametrize(
    "private_link_enabled_config_value", [False, None, "", "false"]
)
def test_transform_onelake_url_disabled_feature_success(
    mock_fab_set_state_config, private_link_enabled_config_value
):
    workspace_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    uri = f"{workspace_id}/{item_id}/Files/test.txt"
    url = "onelake.dfs.fabric.mock-test.com"

    mock_fab_set_state_config(
        fab_constant.FAB_WS_PRIVATE_LINKS_ENABLED, private_link_enabled_config_value
    )
    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, is_onelake_api=True
    )

    assert result == url


def test_transform_fabric_url_no_transformation_when_guid_first_segment_success(
    setup_default_private_links,
):
    workspace_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    uri = f"{workspace_id}/{item_id}/Files/test.txt"
    url = "api.fabric.mock-test.com"

    result = _transform_workspace_url_for_private_link_if_needed(url, uri)

    # Should return original URL unchanged since Fabric APIs only handle workspaces pattern
    assert result == url


def test_transform_workspace_url_with_hostname_argument(setup_default_private_links):
    workspace_id = str(uuid.uuid4())
    uri = f"workspaces/{workspace_id}/items"
    url = "api.fabric.microsoft.com"
    custom_hostname = "custom.host.com"

    result = _transform_workspace_url_for_private_link_if_needed(
        url, uri, hostname=custom_hostname
    )
    assert result == custom_hostname


@patch.object(FabAuth(), "get_access_token", return_value="dummy-token")
def test_do_request_fabric_api_error_raised_on_failed_response(mock_get_token):

    class DummyResponse:
        def __init__(self):
            self.status_code = 500
            self.text = '{"message": "Some Error Message", "errorCode": "ErrorCode"}'
            self.headers = {}

    dummy_args = Namespace()
    dummy_args.uri = f"workspaces/{str(uuid.uuid4())}/items"
    dummy_args.method = "get"
    dummy_args.audience = None

    with patch("requests.Session.request", return_value=DummyResponse()):
        with pytest.raises(FabricAPIError) as excinfo:
            do_request(dummy_args, hostname="custom.hostname.com")
        assert "Some Error Message" == excinfo.value.message
        assert "ErrorCode" == excinfo.value.status_code


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


@pytest.fixture()
def setup_default_private_links(mock_fab_set_state_config):
    mock_fab_set_state_config(fab_constant.FAB_WS_PRIVATE_LINKS_ENABLED, "true")


@patch("platform.python_version", return_value="3.11.5")
@patch("platform.release", return_value="5.4.0")
@patch("platform.system", return_value="Linux")
@patch("requests.Session.request")
@patch("fabric_cli.core.fab_auth.FabAuth")
@patch("fabric_cli.core.fab_context.Context")
@pytest.mark.parametrize(
    "host_app_env, host_app_version_env, expected_suffix",
    [
        (None, None, ""),
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
        ("Invalid-App", "1.0.0", ""),
    ],
)
def test_do_request_user_agent_header(
    mock_context,
    mock_auth,
    mock_request,
    mock_system,
    mock_release,
    mock_python_version,
    host_app_env,
    host_app_version_env,
    expected_suffix,
    monkeypatch,
):
    """Test User-Agent header construction with and without host app identifier."""
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

    # Configure mocks
    mock_auth.return_value.get_access_token.return_value = "dummy-token"
    mock_context.return_value.command = "test-command"

    class DummyResponse:
        status_code = 200
        text = "{}"
        content = b"{}"
        headers = {}

    mock_request.return_value = DummyResponse()

    dummy_args = Namespace(
        uri="items",
        method="get",
        audience=None,
        headers=None,
        wait=False,
        raw_response=True,
        request_params={},
        json_file=None,
    )

    do_request(dummy_args)

    # Verify the User-Agent header from the actual request call
    call_kwargs = mock_request.call_args.kwargs
    headers = call_kwargs["headers"]
    user_agent = headers["User-Agent"]

    base_user_agent = (
        f"{fab_constant.API_USER_AGENT}/{fab_constant.FAB_VERSION} "
        f"(test-command; Linux/5.4.0; Python/3.11.5)"
    )
    expected_user_agent = base_user_agent + expected_suffix

    assert user_agent == expected_user_agent
