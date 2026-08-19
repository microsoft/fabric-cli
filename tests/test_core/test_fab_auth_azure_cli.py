# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages


def _az_account_json(tenant_id: str, user_name: str = "testuser@contoso.com") -> str:
    """Return mock JSON output for 'az account show'."""
    import json as _json

    return _json.dumps({"tenantId": tenant_id, "userName": user_name})


@pytest.fixture(autouse=True)
def temp_dir_fixture(monkeypatch, tmp_path):
    """Create a temporary directory and configure FabAuth to use it."""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_location", lambda: str(tmp_path)
    )
    # Ensure shutil.which("az") resolves in tests (Windows uses az.cmd)
    monkeypatch.setattr(
         "shutil.which",
         lambda cmd: f"/usr/bin/{cmd}" if cmd == "az" else None,
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
    # Clear singleton caches between tests
    auth = FabAuth()
    auth._azure_cli_credential = None
    auth._cached_az_account = None
    auth._cached_az_account_time = 0.0
    auth._auth_info = {}
    auth.app = None
    # Update file paths to use the test's tmp_path
    monkeypatch.setattr(auth, "auth_file", str(tmp_path / "auth.json"))
    monkeypatch.setattr(auth, "cache_file", str(tmp_path / "cache.bin"))
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
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="test-tenant")
        assert auth.get_identity_type() == "azure_cli"

    def test_set_azure_cli_with_tenant(self, temp_dir_fixture):
        """set_azure_cli with tenant_id should store the tenant."""
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="test-tenant-id")
        assert auth.get_tenant_id() == "test-tenant-id"

    @patch("subprocess.run")
    def test_set_azure_cli_auto_captures_tenant(
        self, mock_run, temp_dir_fixture
    ):
        """set_azure_cli without tenant_id should auto-capture from az account show."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("auto-captured-tenant-id")
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "auto-captured-tenant-id"
        mock_run.assert_called_once_with(
            ["/usr/bin/az", "account", "show", "--query", "{tenantId:tenantId,userName:user.name}", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

    @patch("subprocess.run")
    def test_set_azure_cli_explicit_tenant_overrides_auto(
        self, mock_run, temp_dir_fixture
    ):
        """Explicit tenant_id should be used even if az has a different one."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("other-tenant")
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="explicit-tenant")
        assert auth.get_tenant_id() == "explicit-tenant"
        # Still calls az account show once to capture principal for drift detection
        mock_run.assert_called_once()


class TestAzureCliTokenAcquisition:
    """Test token acquisition via AzureCliCredential."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_dispatches_to_azure_cli(
        self, mock_credential_class, temp_dir_fixture
    ):
        """acquire_token should use AzureCliCredential for azure_cli identity."""
        mock_token = MagicMock()
        mock_token.token = "fake-token-123"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Clear cache for clean test
        auth._azure_cli_credential = None

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)

        assert result["access_token"] == "fake-token-123"
        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_from_azure_cli_success(
        self, mock_credential_class, temp_dir_fixture
    ):
        """_acquire_token_from_azure_cli should return token dict on success."""
        mock_token = MagicMock()
        mock_token.token = "az-cli-token-abc"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert result["access_token"] == "az-cli-token-abc"
        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_from_azure_cli_with_tenant(
        self, mock_credential_class, temp_dir_fixture
    ):
        """_acquire_token_from_azure_cli should pass tenant_id to credential."""
        mock_token = MagicMock()
        mock_token.token = "tenant-specific-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="my-tenant-id")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        mock_credential_class.assert_called_once_with(tenant_id="my-tenant-id")

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
        mock_credential = MagicMock()
        error = type("ClientAuthenticationError", (Exception,), {})("Tenant not found")
        mock_credential.get_token.side_effect = error
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
        assert "manually to diagnose" in str(exc_info.value)


class TestAzureCliTenantDrift:
    """Test tenant drift detection during token acquisition."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    @patch("subprocess.run")
    def test_tenant_drift_blocks_token_acquisition(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Should block when stored tenant differs from current az session."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("different-tenant")
        )

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="original-tenant")
        auth._azure_cli_credential = None

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        expected_msg = ErrorMessages.Auth.azure_cli_tenant_mismatch(
            "original-tenant", "different-tenant"
        )
        assert expected_msg in str(exc_info.value)
        mock_credential_class.assert_not_called()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    @patch("subprocess.run")
    def test_tenant_match_allows_token_acquisition(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Should allow when stored tenant matches current az session."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("same-tenant")
        )
        mock_token = MagicMock()
        mock_token.token = "valid-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="same-tenant")
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "valid-token"


class TestAzureCliPrincipalDrift:
    """Test principal (identity) drift detection during token acquisition."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    @patch("subprocess.run")
    def test_principal_drift_blocks_token_acquisition(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Should block when stored principal differs from current az identity."""
        # Login as alice
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("same-tenant", "alice@contoso.com")
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="same-tenant")
        auth._azure_cli_credential = None

        # Now az is logged in as bob (same tenant)
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("same-tenant", "bob@contoso.com")
        )
        auth._cached_az_account = None  # Force re-query

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # Error message must NOT contain PII (no email addresses)
        assert "alice" not in str(exc_info.value)
        assert "bob" not in str(exc_info.value)
        assert "identity has changed" in str(exc_info.value)
        mock_credential_class.assert_not_called()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    @patch("subprocess.run")
    def test_principal_match_allows_token_acquisition(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Should allow when principal matches stored identity."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("same-tenant", "alice@contoso.com")
        )
        mock_token = MagicMock()
        mock_token.token = "valid-token"
        mock_token.expires_on = int(time.time()) + 3600
        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="same-tenant")
        auth._azure_cli_credential = None
        auth._cached_az_account = None  # Force re-query

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "valid-token"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    @patch("subprocess.run")
    def test_no_stored_principal_skips_drift_check(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """If no principal was stored at login, drift check is skipped."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("same-tenant", "anyone@contoso.com")
        )
        mock_token = MagicMock()
        mock_token.token = "valid-token"
        mock_token.expires_on = int(time.time()) + 3600
        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Manually set identity without principal (simulate old auth file)
        auth._set_auth_properties({con.IDENTITY_TYPE: "azure_cli"})
        auth.set_tenant("same-tenant")
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "valid-token"


class TestAzureCliSingletonCredential:
    """Test singleton AzureCliCredential lifecycle."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_singleton_credential_reused_across_calls(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Repeated calls should reuse the same AzureCliCredential instance."""
        mock_token = MagicMock()
        mock_token.token = "reused-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # AzureCliCredential constructor called only once (singleton)
        mock_credential_class.assert_called_once()
        # get_token called twice (no in-memory cache)
        assert mock_credential.get_token.call_count == 2

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_different_scopes_use_same_credential(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Different scopes should use the same singleton credential instance."""
        call_count = 0

        def make_token(*args):
            nonlocal call_count
            call_count += 1
            token = MagicMock()
            token.token = f"token-{call_count}"
            token.expires_on = int(time.time()) + 3600
            return token

        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = make_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        r1 = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        r2 = auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)

        assert r1["access_token"] == "token-1"
        assert r2["access_token"] == "token-2"
        # Same credential instance for both scopes
        mock_credential_class.assert_called_once()
        assert mock_credential.get_token.call_count == 2

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_clears_credential(
        self, mock_credential_class, temp_dir_fixture
    ):
        """set_azure_cli should clear and recreate the credential instance."""
        mock_token = MagicMock()
        mock_token.token = "token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Acquire a token — creates singleton credential
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        # Login with explicit tenant — credential must be cleared
        auth.set_azure_cli(tenant_id="new-tenant")
        assert auth._azure_cli_credential is None


class TestAzureCliScopeHandling:
    """Test that different scopes are correctly passed to Azure CLI."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_onelake_scope(self, mock_credential_class, temp_dir_fixture):
        """OneLake scope should be passed correctly."""
        mock_token = MagicMock()
        mock_token.token = "storage-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

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
        mock_token = MagicMock()
        mock_token.token = "mgmt-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_AZURE_DEFAULT)

        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )


class TestAzureCliCacheInvalidation:
    """Test cache invalidation on logout and forced refresh at login."""

    @patch("subprocess.run")
    def test_logout_clears_tenant_cache(self, mock_run, temp_dir_fixture):
        """logout() should clear the cached account info."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("cached-tenant")
        )

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth._cached_az_account is not None
        assert auth._cached_az_account["tenant_id"] == "cached-tenant"

        auth.logout()
        assert auth._cached_az_account is None
        assert auth._cached_az_account_time == 0.0
        assert auth._azure_cli_credential is None

    @patch("subprocess.run")
    def test_login_forces_fresh_tenant_query(self, mock_run, temp_dir_fixture):
        """set_azure_cli should bypass cache and query az fresh."""
        # First call returns tenant-A
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("tenant-A")
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "tenant-A"

        # Simulate user switching az tenant, then re-logging in
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("tenant-B")
        )
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()  # Should force refresh, get tenant-B
        assert auth.get_tenant_id() == "tenant-B"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    @patch("subprocess.run")
    def test_single_subprocess_across_three_login_scopes(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Login should call az account show only once across 3 scope validations."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("login-tenant")
        )

        mock_token = MagicMock()
        mock_token.token = "login-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()  # 1 subprocess call (force_refresh)

        # 3 scope validations — each calls drift check, but cache should hit
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)
        auth._acquire_token_from_azure_cli(con.SCOPE_AZURE_DEFAULT)

        # az account show called once at login, cached for drift checks
        assert mock_run.call_count == 1

    @patch("subprocess.run")
    def test_identity_type_preserved_after_tenant_change(
        self, mock_run, temp_dir_fixture
    ):
        """identity_type should remain azure_cli after tenant changes."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("tenant-A")
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_identity_type() == "azure_cli"

        # Re-login with different tenant
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_az_account_json("tenant-B")
        )
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_identity_type() == "azure_cli"
        assert auth.get_tenant_id() == "tenant-B"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_login_clears_credential_on_tenant_change(
        self, mock_credential_class, temp_dir_fixture
    ):
        """set_azure_cli should clear credential when transitioning tenants."""
        mock_token = MagicMock()
        mock_token.token = "token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Acquire a token with no tenant stored
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        # Login with explicit tenant — credential must be cleared for recreation
        auth.set_azure_cli(tenant_id="new-tenant")
        assert auth._azure_cli_credential is None


class TestAzureCliTenantDiscoveryFailures:
    """Test _get_azure_cli_tenant failure paths."""

    @patch("subprocess.run")
    def test_nonzero_return_code_returns_none(self, mock_run, temp_dir_fixture):
        """Should return None when az account show fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        auth = FabAuth()
        auth._cached_az_tenant = None
        auth._cached_az_tenant_time = 0.0
        assert auth._get_azure_cli_tenant(force_refresh=True) is None

    @patch("subprocess.run")
    def test_empty_stdout_returns_none(self, mock_run, temp_dir_fixture):
        """Should return None when az returns empty stdout."""
        mock_run.return_value = MagicMock(returncode=0, stdout="   \n")
        auth = FabAuth()
        auth._cached_az_tenant = None
        auth._cached_az_tenant_time = 0.0
        assert auth._get_azure_cli_tenant(force_refresh=True) is None

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("az", 10))
    def test_timeout_returns_none(self, mock_run, temp_dir_fixture):
        """Should return None on subprocess timeout."""
        auth = FabAuth()
        auth._cached_az_tenant = None
        auth._cached_az_tenant_time = 0.0
        assert auth._get_azure_cli_tenant(force_refresh=True) is None

    def test_az_not_installed_returns_none(self, monkeypatch, temp_dir_fixture):
        """Should return None when az CLI is not installed."""
        monkeypatch.setattr("shutil.which", lambda cmd: None)
        auth = FabAuth()
        auth._cached_az_tenant = None
        auth._cached_az_tenant_time = 0.0
        assert auth._get_azure_cli_tenant(force_refresh=True) is None

    @patch("subprocess.run")
    def test_cache_hit_before_ttl_expiry(self, mock_run, temp_dir_fixture):
        """Should return cached tenant without calling subprocess."""
        auth = FabAuth()
        auth._cached_az_account = {"tenant_id": "cached-tenant", "principal_name": "user@test.com"}
        auth._cached_az_account_time = time.monotonic()  # Just cached now
        result = auth._get_azure_cli_tenant()
        assert result == "cached-tenant"
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_cache_miss_after_ttl_expiry(self, mock_run, temp_dir_fixture):
        """Should call subprocess after TTL expires."""
        mock_run.return_value = MagicMock(returncode=0, stdout=_az_account_json("new-tenant"))
        auth = FabAuth()
        auth._cached_az_account = {"tenant_id": "old-tenant", "principal_name": "user@test.com"}
        auth._cached_az_account_time = time.monotonic() - 30
        result = auth._get_azure_cli_tenant()
        assert result == "new-tenant"
        mock_run.assert_called_once()


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
        mock_token = MagicMock()
        mock_token.token = "az-cli-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        mock_app = MagicMock()
        auth.app = mock_app

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "az-cli-token"
        mock_app.acquire_token_silent.assert_not_called()
        mock_app.acquire_token_interactive.assert_not_called()
        mock_app.acquire_token_for_client.assert_not_called()
