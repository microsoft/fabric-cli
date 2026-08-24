# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the MSAL bridge with Azure CLI identity type."""

import base64
import json as _json
import time
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ClientAuthenticationError

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_msal_bridge import MsalTokenCredential
from fabric_cli.errors import ErrorMessages


def _make_jwt(tid: str = "test-tenant", oid: str = "test-oid") -> str:
    """Create a fake JWT with specified claims."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    claims = {"tid": tid, "oid": oid, "iss": f"https://sts.windows.net/{tid}/"}
    payload = base64.urlsafe_b64encode(
        _json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


@pytest.fixture(autouse=True)
def temp_dir_fixture(monkeypatch, tmp_path):
    """Isolate FabAuth singleton for bridge tests."""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_location", lambda: str(
            tmp_path)
    )
    monkeypatch.delenv("FAB_TOKEN", raising=False)
    monkeypatch.delenv("FAB_TOKEN_ONELAKE", raising=False)
    monkeypatch.delenv("FAB_TOKEN_AZURE", raising=False)
    auth = FabAuth()
    auth._azure_cli_credential = None
    auth._auth_info = {}

    # Bypass JWKS signature validation — fake JWTs have no valid signature
    def _test_decode_jwt_token(self, token, expected_audience=None):
        parts = token.split(".")
        if len(parts) < 2:
            raise FabricCLIError(
                ErrorMessages.Auth.jwt_decode_failed(),
                con.ERROR_AUTHENTICATION_FAILED,
            )
        payload = parts[1]
        payload += "=" * ((-len(payload)) % 4)
        try:
            decoded = base64.urlsafe_b64decode(payload)
            return _json.loads(decoded)
        except Exception:
            raise FabricCLIError(
                ErrorMessages.Auth.jwt_decode_failed(),
                con.ERROR_AUTHENTICATION_FAILED,
            )

    monkeypatch.setattr(auth, "_decode_jwt_token", lambda token,
                        expected_audience=None: _test_decode_jwt_token(auth, token, expected_audience))


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
        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        credential = MsalTokenCredential(auth)
        with pytest.raises(ClientAuthenticationError):
            credential.get_token("https://evil.example.com/.default")
