# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the MSAL bridge with Azure CLI identity type."""

import time
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ClientAuthenticationError

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_msal_bridge import MsalTokenCredential


class TestMsalBridgeAzureCli:
    """Verify MsalTokenCredential works when identity_type is azure_cli."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_bridge_returns_access_token_for_azure_cli_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """MsalTokenCredential.get_token should return an AccessToken via Azure CLI."""
        mock_token = MagicMock()
        mock_token.token = "test string"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        credential = MsalTokenCredential(auth)
        result = credential.get_token(con.SCOPE_FABRIC_DEFAULT[0])

        assert result.token == "test string"
        assert result.expires_on == mock_token.expires_on
        mock_credential_class.assert_called_once_with()
        mock_credential.get_token.assert_called_once_with(con.SCOPE_FABRIC_DEFAULT[0])

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_bridge_rejects_invalid_scope(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """MsalTokenCredential should reject scopes not in the allowlist."""
        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        credential = MsalTokenCredential(auth)
        with pytest.raises(ClientAuthenticationError):
            credential.get_token("https://evil.example.com/.default")

    def test_bridge_returns_access_token_in_proxy_auth_mode_success(
        self, monkeypatch, azure_cli_auth_fixture
    ):
        """Proxy auth placeholders should satisfy the TokenCredential contract."""
        monkeypatch.setenv("FAB_PROXY_AUTH_ENABLED", "true")
        auth = FabAuth()

        credential = MsalTokenCredential(auth)
        result = credential.get_token(con.SCOPE_FABRIC_DEFAULT[0])

        assert result.token == "mockToken"
        assert result.expires_on == 9999999999
