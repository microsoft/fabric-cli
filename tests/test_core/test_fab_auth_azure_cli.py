# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json as _json
import time
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages


def _make_jwt(tid: str = "test-tenant", oid: str = "test-oid",
              iss: str = "https://sts.windows.net/test-tenant/", **extra_claims) -> str:
    """Create a fake JWT with specified claims (no signature validation needed)."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    claims = {"tid": tid, "oid": oid, "iss": iss, **extra_claims}
    payload = base64.urlsafe_b64encode(_json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


def _mock_credential_with_jwt(mock_class, tid="test-tenant", oid="test-oid",
                               iss="https://sts.windows.net/test-tenant/", **extra):
    """Set up a mock AzureCliCredential that returns a JWT with given claims."""
    token_str = _make_jwt(tid=tid, oid=oid, iss=iss, **extra)
    mock_token = MagicMock()
    mock_token.token = token_str
    mock_token.expires_on = int(time.time()) + 3600
    mock_credential = MagicMock()
    mock_credential.get_token.return_value = mock_token
    mock_class.return_value = mock_credential
    return mock_credential, mock_token


@pytest.fixture(autouse=True)
def temp_dir_fixture(monkeypatch, tmp_path):
    """Create a temporary directory and configure FabAuth to use it."""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_location", lambda: str(tmp_path)
    )
    # Clear env vars that would interfere with auth
    for var in (
        "FAB_TOKEN",
        "FAB_TOKEN_ONELAKE",
        "FAB_TOKEN_AZURE",
        "FAB_TENANT_ID",
        "FAB_SPN_CLIENT_ID",
        "FAB_SPN_CLIENT_SECRET",
        "FAB_SPN_CERT_PATH",
        "FAB_MANAGED_IDENTITY",
    ):
        monkeypatch.delenv(var, raising=False)
    # Clear singleton state between tests
    auth = FabAuth()
    auth._azure_cli_credential = None
    auth._auth_info = {}
    auth.app = None
    # Update file paths to use the test's tmp_path
    monkeypatch.setattr(auth, "auth_file", str(tmp_path / "auth.json"))
    monkeypatch.setattr(auth, "cache_file", str(tmp_path / "cache.bin"))

    # Bypass JWKS signature validation in tests — fake JWTs cannot pass
    # real signature checks. Decode claims via base64 like the removed
    # _decode_jwt_claims helper.
    def _test_decode_jwt_token(self, token, expected_audience=None):
        """Test-only: decode JWT payload without signature validation."""
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

    monkeypatch.setattr(auth, "_decode_jwt_token", lambda token, expected_audience=None: _test_decode_jwt_token(auth, token, expected_audience))

    return str(tmp_path)


class TestAzureCliIdentityType:
    """Test that azure_cli is a valid identity type."""

    def test_azure_cli_in_auth_keys(self):
        """azure_cli should be in the allowed identity types."""
        assert "azure_cli" in con.AUTH_KEYS[con.IDENTITY_TYPE]

    def test_set_access_mode_accepts_azure_cli(self, temp_dir_fixture):
        """set_access_mode should accept azure_cli without raising."""
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        assert auth.get_identity_type() == "azure_cli"

    def test_set_azure_cli_sets_identity_type(self, temp_dir_fixture):
        """set_azure_cli should configure identity_type to azure_cli."""
        with patch("fabric_cli.core.fab_auth.AzureCliCredential") as mock_class:
            _mock_credential_with_jwt(mock_class, tid="test-tenant")
            auth = FabAuth()
            auth.set_access_mode("azure_cli")
            auth.set_azure_cli()
            assert auth.get_identity_type() == "azure_cli"

    def test_set_azure_cli_stores_jwt_tenant(self, temp_dir_fixture):
        """set_azure_cli should store the tenant from the JWT tid claim."""
        with patch("fabric_cli.core.fab_auth.AzureCliCredential") as mock_class:
            _mock_credential_with_jwt(mock_class, tid="test-tenant-id")
            auth = FabAuth()
            auth.set_access_mode("azure_cli")
            auth.set_azure_cli()
            assert auth.get_tenant_id() == "test-tenant-id"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_set_azure_cli_auto_captures_tenant(
        self, mock_credential_class, temp_dir_fixture
    ):
        """set_azure_cli without tenant_id should auto-capture from JWT claims."""
        _mock_credential_with_jwt(mock_credential_class, tid="auto-captured-tenant-id")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "auto-captured-tenant-id"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_set_azure_cli_tenant_always_from_jwt(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Tenant is always inherited from the Azure CLI JWT, never overridden."""
        _mock_credential_with_jwt(mock_credential_class, tid="jwt-tenant")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "jwt-tenant"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_set_azure_cli_matching_tenant_param_accepted(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Explicit tenant that matches Azure CLI context should succeed."""
        _mock_credential_with_jwt(mock_credential_class, tid="my-tenant")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="my-tenant")
        assert auth.get_tenant_id() == "my-tenant"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_set_azure_cli_mismatched_tenant_param_rejected(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Explicit tenant that differs from Azure CLI context should error."""
        _mock_credential_with_jwt(mock_credential_class, tid="cli-tenant")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        with pytest.raises(FabricCLIError, match="does not match"):
            auth.set_azure_cli(tenant_id="other-tenant")


class TestAzureCliTokenAcquisition:
    """Test token acquisition via AzureCliCredential."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_dispatches_to_azure_cli(
        self, mock_credential_class, temp_dir_fixture
    ):
        """acquire_token should use AzureCliCredential for azure_cli identity."""
        mock_credential, _ = _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)

        assert "access_token" in result
        mock_credential.get_token.assert_called_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_from_azure_cli_success(
        self, mock_credential_class, temp_dir_fixture
    ):
        """_acquire_token_from_azure_cli should return token dict on success."""
        mock_credential, mock_token = _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert result["access_token"] == mock_token.token
        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_credential_inherits_azure_cli_context(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Credential should be created without tenant_id — inherits Azure CLI context."""
        _mock_credential_with_jwt(mock_credential_class, tid="my-tenant-id")

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # All credential creations should be without tenant_id
        for call in mock_credential_class.call_args_list:
            assert call == ((), {}), f"Expected no tenant_id, got {call}"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_from_azure_cli_credential_unavailable(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should raise FabricCLIError when Azure CLI is not logged in."""
        from fabric_cli.core.fab_auth import CredentialUnavailableError

        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = CredentialUnavailableError(
            "Azure CLI not logged in"
        )
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert ErrorMessages.Auth.azure_cli_not_available() in str(exc_info.value)
        assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_sdk_exception_surfaces_message(
        self, mock_credential_class, temp_dir_fixture
    ):
        """SDK exceptions (pre-sanitized by azure-identity) surface their message."""
        from azure.core.exceptions import ClientAuthenticationError

        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = ClientAuthenticationError("Tenant not found")
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "Tenant not found" in str(exc_info.value)

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_unknown_exception_returns_safe_message(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Non-SDK exceptions should always return a safe generic message."""
        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = RuntimeError(
            "accessToken: eyJ0eXAi..."
        )
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "eyJ0eXAi" not in str(exc_info.value)
        assert "Unable to get a token from Azure CLI" in str(exc_info.value)


class TestAzureCliTenantDrift:
    """Test tenant drift detection via JWT claims."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_tenant_drift_blocks_token_acquisition(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should block when token tid differs from stored tenant."""
        # Login with original-tenant
        _mock_credential_with_jwt(mock_credential_class, tid="original-tenant", oid="user1")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        # Now credential returns token for different-tenant
        _mock_credential_with_jwt(mock_credential_class, tid="different-tenant", oid="user1")

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        expected_msg = ErrorMessages.Auth.azure_cli_tenant_mismatch(
            "original-tenant", "different-tenant"
        )
        assert expected_msg in str(exc_info.value)

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_tenant_match_allows_token_acquisition(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should allow when token tid matches stored tenant."""
        _mock_credential_with_jwt(mock_credential_class, tid="same-tenant", oid="user1")

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert "access_token" in result


class TestAzureCliEnvironmentDrift:
    """Test cloud environment drift detection via JWT iss claim."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_environment_drift_blocks_token_acquisition(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should block when token issuer differs from stored environment."""
        # Login in Azure Public
        _mock_credential_with_jwt(
            mock_credential_class, tid="t1", oid="u1",
            iss="https://sts.windows.net/t1/"
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        # Now credential returns token from Azure Government
        _mock_credential_with_jwt(
            mock_credential_class, tid="t1", oid="u1",
            iss="https://sts.microsoftonline.us/t1/"
        )

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "environment has changed" in str(exc_info.value)

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_same_environment_allows_token_acquisition(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should allow when token issuer matches stored environment."""
        _mock_credential_with_jwt(
            mock_credential_class, tid="t1", oid="u1",
            iss="https://sts.windows.net/t1/"
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert "access_token" in result


class TestAzureCliPrincipalDrift:
    """Test principal (identity) drift detection via JWT OID claims."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_principal_drift_blocks_token_acquisition(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should block when token oid differs from stored principal."""
        # Login as alice (oid=alice-oid)
        _mock_credential_with_jwt(mock_credential_class, tid="same-tenant", oid="alice-oid")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        # Now credential returns token for bob (oid=bob-oid, same tenant)
        _mock_credential_with_jwt(mock_credential_class, tid="same-tenant", oid="bob-oid")

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # Error message must NOT contain PII (no OIDs exposed)
        assert "alice" not in str(exc_info.value)
        assert "bob" not in str(exc_info.value)
        assert "identity has changed" in str(exc_info.value)

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_principal_match_allows_token_acquisition(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should allow when token oid matches stored principal."""
        _mock_credential_with_jwt(mock_credential_class, tid="same-tenant", oid="alice-oid")

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert "access_token" in result

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_no_stored_principal_skips_drift_check(
        self, mock_credential_class, temp_dir_fixture
    ):
        """If no principal was stored at login, drift check is skipped."""
        _mock_credential_with_jwt(mock_credential_class, tid="same-tenant", oid="anyone-oid")

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Manually set identity without principal (simulate old auth file)
        auth._set_auth_properties({con.IDENTITY_TYPE: "azure_cli"})
        auth.set_tenant("same-tenant")
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert "access_token" in result


class TestAzureCliSingletonCredential:
    """Test singleton AzureCliCredential lifecycle."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_singleton_credential_reused_across_calls(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Repeated calls should reuse the same AzureCliCredential instance."""
        _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # AzureCliCredential constructor called only once (singleton)
        mock_credential_class.assert_called_once()
        # get_token called twice (no in-memory cache)
        assert mock_credential_class.return_value.get_token.call_count == 2

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_different_scopes_use_same_credential(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Different scopes should use the same singleton credential instance."""
        _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)

        # Same credential instance for both scopes
        mock_credential_class.assert_called_once()
        assert mock_credential_class.return_value.get_token.call_count == 2

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_clears_credential(
        self, mock_credential_class, temp_dir_fixture
    ):
        """set_azure_cli should clear and recreate the credential instance."""
        _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Acquire a token — creates singleton credential
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        # Login with explicit tenant — credential must be cleared
        auth.set_azure_cli()
        assert auth._azure_cli_credential is None


class TestAzureCliScopeHandling:
    """Test that different scopes are correctly passed to Azure CLI."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_onelake_scope(self, mock_credential_class, temp_dir_fixture):
        """OneLake scope should be passed correctly."""
        mock_credential, _ = _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)

        mock_credential.get_token.assert_called_once_with(
            "https://storage.azure.com/.default"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_azure_management_scope(self, mock_credential_class, temp_dir_fixture):
        """Azure management scope should be passed correctly."""
        mock_credential, _ = _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_AZURE_DEFAULT)

        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )


class TestAzureCliLoginLogoutLifecycle:
    """Test login/logout lifecycle and credential management."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_logout_clears_credential(self, mock_credential_class, temp_dir_fixture):
        """logout() should clear the credential instance."""
        _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth._azure_cli_credential is None  # cleared after login probe

        # Acquire token to set credential
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        auth.logout()
        assert auth._azure_cli_credential is None

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_discovers_tenant_from_jwt(self, mock_credential_class, temp_dir_fixture):
        """set_azure_cli should discover tenant from probe token JWT claims."""
        _mock_credential_with_jwt(mock_credential_class, tid="discovered-tenant")

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "discovered-tenant"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_stores_oid_and_issuer_for_drift_detection(self, mock_credential_class, temp_dir_fixture):
        """set_azure_cli should store OID and issuer from JWT for drift detection."""
        _mock_credential_with_jwt(mock_credential_class, tid="t1", oid="user-oid-123",
                                   iss="https://sts.windows.net/t1/")

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth._auth_info.get(con.FAB_AZURE_CLI_PRINCIPAL_ID) == "user-oid-123"
        assert auth._auth_info.get(con.FAB_AZURE_CLI_ISSUER) == "sts.windows.net"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_re_login_updates_tenant_and_oid(self, mock_credential_class, temp_dir_fixture):
        """Re-login should update tenant and OID from new probe token."""
        _mock_credential_with_jwt(mock_credential_class, tid="tenant-A", oid="oid-A")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "tenant-A"

        # Re-login with different identity
        _mock_credential_with_jwt(mock_credential_class, tid="tenant-B", oid="oid-B")
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "tenant-B"
        assert auth._auth_info.get(con.FAB_AZURE_CLI_PRINCIPAL_ID) == "oid-B"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_identity_type_preserved_after_tenant_change(
        self, mock_credential_class, temp_dir_fixture
    ):
        """identity_type should remain azure_cli after tenant changes."""
        _mock_credential_with_jwt(mock_credential_class, tid="tenant-A")
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_identity_type() == "azure_cli"

        _mock_credential_with_jwt(mock_credential_class, tid="tenant-B")
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_identity_type() == "azure_cli"
        assert auth.get_tenant_id() == "tenant-B"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_clears_credential_on_tenant_change(
        self, mock_credential_class, temp_dir_fixture
    ):
        """set_azure_cli should clear credential when transitioning tenants."""
        _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Acquire a token to set credential
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        # Login with explicit tenant — credential must be cleared for recreation
        auth.set_azure_cli()
        assert auth._azure_cli_credential is None


class TestJwtClaimsDecoding:
    """Test JWT claim extraction via _decode_jwt_token (with test fixture bypassing signature validation)."""

    def test_valid_jwt_extracts_claims(self, temp_dir_fixture):
        """Should decode tid and oid from a valid JWT."""
        token = _make_jwt(tid="my-tenant", oid="my-oid")
        auth = FabAuth()
        claims = auth._decode_jwt_token(token)
        assert claims["tid"] == "my-tenant"
        assert claims["oid"] == "my-oid"

    def test_invalid_jwt_raises(self, temp_dir_fixture):
        """Should raise FabricCLIError for malformed tokens."""
        auth = FabAuth()
        with pytest.raises((FabricCLIError, Exception)):
            auth._decode_jwt_token("not-a-jwt")
        with pytest.raises((FabricCLIError, Exception)):
            auth._decode_jwt_token("")

    def test_jwt_with_extra_claims(self, temp_dir_fixture):
        """Should extract additional claims."""
        token = _make_jwt(tid="t1", oid="o1", upn="user@contoso.com")
        auth = FabAuth()
        claims = auth._decode_jwt_token(token)
        assert claims["upn"] == "user@contoso.com"


class TestFailClosedOnMissingClaims:
    """Verify tokens with missing identity claims are rejected, not silently used."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_rejects_token_missing_oid(self, mock_class, temp_dir_fixture):
        """set_azure_cli should fail if probe token lacks oid."""
        header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(
            _json.dumps({"tid": "t1", "iss": "https://sts.windows.net/t1/"}).encode()
        ).rstrip(b"=").decode()
        token_str = f"{header}.{payload}.fakesig"
        mock_token = MagicMock()
        mock_token.token = token_str
        mock_token.expires_on = int(time.time()) + 3600
        mock_class.return_value.get_token.return_value = mock_token
        auth = FabAuth()
        with pytest.raises(FabricCLIError, match="Unable to validate"):
            auth.set_azure_cli()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_rejects_token_missing_tid(self, mock_class, temp_dir_fixture):
        """set_azure_cli should fail if probe token lacks tid."""
        header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(
            _json.dumps({"oid": "o1", "iss": "https://sts.windows.net/t1/"}).encode()
        ).rstrip(b"=").decode()
        token_str = f"{header}.{payload}.fakesig"
        mock_token = MagicMock()
        mock_token.token = token_str
        mock_token.expires_on = int(time.time()) + 3600
        mock_class.return_value.get_token.return_value = mock_token
        auth = FabAuth()
        with pytest.raises(FabricCLIError, match="Unable to validate"):
            auth.set_azure_cli()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_rejects_malformed_token(self, mock_class, temp_dir_fixture):
        """set_azure_cli should fail if probe token is not a valid JWT."""
        mock_token = MagicMock()
        mock_token.token = "not-a-jwt"
        mock_token.expires_on = int(time.time()) + 3600
        mock_class.return_value.get_token.return_value = mock_token
        auth = FabAuth()
        with pytest.raises(FabricCLIError, match="Azure CLI authentication failed"):
            auth.set_azure_cli()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquisition_rejects_token_missing_claims(self, mock_class, temp_dir_fixture):
        """Token acquisition should fail if returned token lacks identity claims."""
        # Login with good token
        _mock_credential_with_jwt(mock_class)
        auth = FabAuth()
        auth.set_azure_cli()

        # Now return a bad token on next call
        bad_token = MagicMock()
        bad_token.token = "not-a-jwt"
        bad_token.expires_on = int(time.time()) + 3600
        mock_class.return_value.get_token.return_value = bad_token
        with pytest.raises(FabricCLIError, match="Failed to decode JWT"):
            auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)


class TestNonAzureCliIsolation:
    """Verify each auth method uses only its own credential path — no overlap."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_user_identity_does_not_invoke_azure_cli(
        self, mock_credential_class, temp_dir_fixture
    ):
        """When identity_type is 'user', AzureCliCredential must not be instantiated."""
        auth = FabAuth()
        auth.set_access_mode("user")

        mock_app = MagicMock()
        mock_app.get_accounts.return_value = [{"username": "test@contoso.com"}]
        mock_app.acquire_token_silent.return_value = {
            "access_token": "msal-user-token",
            "expires_on": str(int(time.time()) + 3600),
        }
        auth.app = mock_app

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "msal-user-token"
        mock_credential_class.assert_not_called()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_service_principal_does_not_invoke_azure_cli(
        self, mock_credential_class, temp_dir_fixture
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

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "spn-token"
        mock_credential_class.assert_not_called()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_azure_cli_does_not_invoke_msal_app(
        self, mock_credential_class, temp_dir_fixture
    ):
        """When identity_type is 'azure_cli', MSAL app methods must not be called."""
        _mock_credential_with_jwt(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        mock_app = MagicMock()
        auth.app = mock_app

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)
        assert "access_token" in result
        mock_app.acquire_token_silent.assert_not_called()
        mock_app.acquire_token_interactive.assert_not_called()
        mock_app.acquire_token_for_client.assert_not_called()
