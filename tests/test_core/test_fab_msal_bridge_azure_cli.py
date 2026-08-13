# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the MSAL bridge with Azure CLI identity type."""

import time
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_msal_bridge import MsalTokenCredential


@pytest.fixture(autouse=True)
def temp_dir_fixture(monkeypatch, tmp_path):
    """Isolate FabAuth singleton for bridge tests."""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_location", lambda: str(tmp_path)
    )
    monkeypatch.delenv("FAB_TOKEN", raising=False)
    monkeypatch.delenv("FAB_TOKEN_ONELAKE", raising=False)
    monkeypatch.delenv("FAB_TOKEN_AZURE", raising=False)
    auth = FabAuth()
    auth._azure_cli_token_cache.clear()
    auth._cached_az_tenant = None
    auth._cached_az_tenant_time = 0.0
    auth._auth_info = {}


class TestMsalBridgeAzureCli:
    """Verify MsalTokenCredential works when identity_type is azure_cli."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_bridge_returns_access_token_for_azure_cli(
        self, mock_credential_class
    ):
        """MsalTokenCredential.get_token should return an AccessToken via Azure CLI."""
        mock_token = MagicMock()
        mock_token.token = "bridge-azure-cli-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        credential = MsalTokenCredential(auth)
        result = credential.get_token(con.SCOPE_FABRIC_DEFAULT[0])

        assert result.token == "bridge-azure-cli-token"
        assert result.expires_on == mock_token.expires_on

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_bridge_rejects_invalid_scope(self, mock_credential_class):
        """MsalTokenCredential should reject scopes not in the allowlist."""
        from azure.core.exceptions import ClientAuthenticationError

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        credential = MsalTokenCredential(auth)
        with pytest.raises(ClientAuthenticationError):
            credential.get_token("https://evil.example.com/.default")


class TestMsalBridgeNonAzureCli:
    """Verify non-azure-cli identity types never invoke AzureCliCredential."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_user_identity_does_not_invoke_azure_cli(self, mock_credential_class):
        """When identity_type is 'user', AzureCliCredential must not be instantiated."""
        auth = FabAuth()
        auth.set_access_mode("user")

        # Simulate MSAL returning a cached token so no interactive prompt
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "test@contoso.com"}]
        mock_app.acquire_token_silent.return_value = {
            "access_token": "msal-user-token",
            "expires_on": str(int(time.time()) + 3600),
        }
        auth.app = mock_app

        credential = MsalTokenCredential(auth)
        result = credential.get_token(con.SCOPE_FABRIC_DEFAULT[0])

        assert result.token == "msal-user-token"
        mock_credential_class.assert_not_called()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_service_principal_does_not_invoke_azure_cli(
        self, mock_credential_class
    ):
        """When identity_type is 'service_principal', AzureCliCredential must not be instantiated."""
        auth = FabAuth()
        auth.set_access_mode("service_principal")

        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "spn-token",
            "expires_on": str(int(time.time()) + 3600),
        }
        auth.app = mock_app

        credential = MsalTokenCredential(auth)
        result = credential.get_token(con.SCOPE_FABRIC_DEFAULT[0])

        assert result.token == "spn-token"
        mock_credential_class.assert_not_called()
