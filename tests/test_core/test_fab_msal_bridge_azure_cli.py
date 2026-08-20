# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the MSAL bridge with Azure CLI identity type."""

import base64
import json as _json
import time
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_msal_bridge import MsalTokenCredential


def _make_jwt(tid: str = "test-tenant", oid: str = "test-oid") -> str:
    """Create a fake JWT with specified claims."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    claims = {"tid": tid, "oid": oid, "iss": f"https://sts.windows.net/{tid}/"}
    payload = base64.urlsafe_b64encode(_json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


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
    auth._azure_cli_credential = None
    auth._auth_info = {}


class TestMsalBridgeAzureCli:
    """Verify MsalTokenCredential works when identity_type is azure_cli."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_bridge_returns_access_token_for_azure_cli(
        self, mock_credential_class
    ):
        """MsalTokenCredential.get_token should return an AccessToken via Azure CLI."""
        token_str = _make_jwt()
        mock_token = MagicMock()
        mock_token.token = token_str
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        credential = MsalTokenCredential(auth)
        result = credential.get_token(con.SCOPE_FABRIC_DEFAULT[0])

        assert result.token == token_str
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
