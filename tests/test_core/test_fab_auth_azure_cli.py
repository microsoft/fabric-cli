# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError


@pytest.fixture(autouse=True)
def temp_dir_fixture(monkeypatch, tmp_path):
    """Create a temporary directory and configure FabAuth to use it."""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_location", lambda: str(tmp_path)
    )
    # Clear env vars that would interfere
    monkeypatch.delenv("FAB_TOKEN", raising=False)
    monkeypatch.delenv("FAB_TOKEN_ONELAKE", raising=False)
    monkeypatch.delenv("FAB_TOKEN_AZURE", raising=False)
    # Clear singleton caches between tests
    auth = FabAuth()
    auth._azure_cli_token_cache.clear()
    auth._cached_az_tenant = None
    auth._cached_az_tenant_time = 0.0
    return str(tmp_path)


@pytest.fixture
def auth_instance(temp_dir_fixture):
    """Get a fresh FabAuth instance."""
    # Clear singleton for test isolation
    FabAuth.__wrapped__ = None  # type: ignore
    from fabric_cli.core import fab_auth as fab_auth_module

    if FabAuth in fab_auth_module.singleton.__wrapped__:  # type: ignore
        del fab_auth_module.singleton.__wrapped__[FabAuth]  # type: ignore
    return FabAuth()


@pytest.fixture
def fresh_auth(temp_dir_fixture, monkeypatch):
    """Get a fresh FabAuth instance with singleton cleared."""
    # Reset singleton instances dict
    import fabric_cli.core.fab_auth as auth_module

    # Access the closure variable of the singleton decorator
    singleton_instances = auth_module.singleton.__code__.co_consts  # noqa
    # Simpler approach: just patch the module-level reference
    monkeypatch.setattr(
        "fabric_cli.core.fab_auth.FabAuth.__init__.__globals__",
        {},
        raising=False,
    )
    # Re-instantiate
    auth = FabAuth.__new__(FabAuth)
    auth.__init__()
    return auth


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
        auth.set_azure_cli()
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
            returncode=0, stdout="auto-captured-tenant-id\n"
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "auto-captured-tenant-id"

    @patch("subprocess.run")
    def test_set_azure_cli_explicit_tenant_overrides_auto(
        self, mock_run, temp_dir_fixture
    ):
        """Explicit tenant_id should be used even if az has a different one."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="az-tenant\n"
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="explicit-tenant")
        assert auth.get_tenant_id() == "explicit-tenant"


class TestAzureCliTokenAcquisition:
    """Test token acquisition via AzureCliCredential."""

    @patch("azure.identity.AzureCliCredential")
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
        auth._azure_cli_token_cache.clear()

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)

        assert result["access_token"] == "fake-token-123"
        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("azure.identity.AzureCliCredential")
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
        auth._azure_cli_token_cache.clear()

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert result["access_token"] == "az-cli-token-abc"
        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("azure.identity.AzureCliCredential")
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
        auth._azure_cli_token_cache.clear()

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        mock_credential_class.assert_called_once_with(tenant_id="my-tenant-id")

    @patch("azure.identity.AzureCliCredential")
    def test_acquire_token_from_azure_cli_credential_unavailable(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Should raise FabricCLIError when Azure CLI is not logged in."""
        from azure.identity import CredentialUnavailableError

        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = CredentialUnavailableError(
            "Azure CLI not logged in"
        )
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_token_cache.clear()

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "not installed or not logged in" in str(exc_info.value)

    @patch(
        "azure.identity.AzureCliCredential",
        side_effect=ImportError("No module named 'azure.identity'"),
    )
    def test_acquire_token_from_azure_cli_missing_package(
        self, mock_import, temp_dir_fixture
    ):
        """Should raise FabricCLIError when azure-identity is not installed."""
        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        # Need to actually test the import failure path
        with patch.dict("sys.modules", {"azure.identity": None}):
            with patch(
                "builtins.__import__", side_effect=ImportError("no azure.identity")
            ):
                with pytest.raises(FabricCLIError) as exc_info:
                    auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

                assert "azure-identity" in str(exc_info.value)

    @patch("azure.identity.AzureCliCredential")
    def test_acquire_token_sanitizes_error_messages(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Error messages should never contain token content."""
        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = Exception(
            "Failed with accessToken: eyJ0eXAi..."
        )
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_token_cache.clear()

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # Should not contain the raw token
        assert "eyJ0eXAi" not in str(exc_info.value)
        assert "manually to diagnose" in str(exc_info.value)

    @pytest.mark.parametrize(
        "error_msg",
        [
            "Error with Bearer token xyz",
            "refresh_token expired",
            "Authorization header invalid",
            "eyJhbGciOiJSUzI1NiIsInR5cCI6",
        ],
    )
    @patch("azure.identity.AzureCliCredential")
    def test_acquire_token_sanitizes_expanded_patterns(
        self, mock_credential_class, error_msg, temp_dir_fixture
    ):
        """All sensitive patterns should be sanitized from error messages."""
        mock_credential = MagicMock()
        mock_credential.get_token.side_effect = Exception(error_msg)
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_token_cache.clear()

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "manually to diagnose" in str(exc_info.value)


class TestAzureCliTenantDrift:
    """Test tenant drift detection during token acquisition."""

    @patch("azure.identity.AzureCliCredential")
    @patch("subprocess.run")
    def test_tenant_drift_blocks_token_acquisition(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Should block when stored tenant differs from current az session."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="different-tenant\n"
        )

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli(tenant_id="original-tenant")
        auth._azure_cli_token_cache.clear()

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "Tenant mismatch" in str(exc_info.value)
        assert "original-tenant" in str(exc_info.value)

    @patch("azure.identity.AzureCliCredential")
    @patch("subprocess.run")
    def test_tenant_match_allows_token_acquisition(
        self, mock_run, mock_credential_class, temp_dir_fixture
    ):
        """Should allow when stored tenant matches current az session."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="same-tenant\n"
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
        auth._azure_cli_token_cache.clear()

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "valid-token"


class TestAzureCliTokenCache:
    """Test in-memory token caching for Azure CLI tokens."""

    @patch("azure.identity.AzureCliCredential")
    def test_cached_token_avoids_subprocess(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Second call with same scope should use cache, not subprocess."""
        mock_token = MagicMock()
        mock_token.token = "cached-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_token_cache.clear()

        result1 = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        result2 = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert result1["access_token"] == "cached-token"
        assert result2["access_token"] == "cached-token"
        # get_token should only be called once (second call uses cache)
        mock_credential.get_token.assert_called_once()

    @patch("azure.identity.AzureCliCredential")
    def test_expired_cache_triggers_refresh(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Expired cached token should trigger a new subprocess call."""
        mock_token = MagicMock()
        mock_token.token = "fresh-token"
        mock_token.expires_on = int(time.time()) + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Pre-populate cache with expired token
        auth._azure_cli_token_cache.clear()
        auth._azure_cli_token_cache[con.SCOPE_FABRIC_DEFAULT[0]] = {
            "access_token": "old-token",
            "expires_on": int(time.time()) - 10,  # already expired
        }

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert result["access_token"] == "fresh-token"
        mock_credential.get_token.assert_called_once()

    @patch("azure.identity.AzureCliCredential")
    def test_different_scopes_cached_separately(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Different scopes should have separate cache entries."""
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
        auth._azure_cli_token_cache.clear()

        r1 = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        r2 = auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)

        assert r1["access_token"] == "token-1"
        assert r2["access_token"] == "token-2"
        assert mock_credential.get_token.call_count == 2


class TestAzureCliScopeHandling:
    """Test that different scopes are correctly passed to Azure CLI."""

    @patch("azure.identity.AzureCliCredential")
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
        auth._azure_cli_token_cache.clear()

        auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)

        mock_credential.get_token.assert_called_once_with(
            "https://storage.azure.com/.default"
        )

    @patch("azure.identity.AzureCliCredential")
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
        auth._azure_cli_token_cache.clear()

        auth._acquire_token_from_azure_cli(con.SCOPE_AZURE_DEFAULT)

        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )


class TestAzureCliCacheInvalidation:
    """Test cache invalidation on logout and forced refresh at login."""

    @patch("subprocess.run")
    def test_logout_clears_tenant_cache(self, mock_run, temp_dir_fixture):
        """logout() should clear the cached tenant."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="cached-tenant\n"
        )

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth._cached_az_tenant == "cached-tenant"

        auth.logout()
        assert auth._cached_az_tenant is None
        assert auth._cached_az_tenant_time == 0.0
        assert auth._azure_cli_token_cache == {}

    @patch("subprocess.run")
    def test_login_forces_fresh_tenant_query(self, mock_run, temp_dir_fixture):
        """set_azure_cli should bypass cache and query az fresh."""
        # First call returns tenant-A
        mock_run.return_value = MagicMock(
            returncode=0, stdout="tenant-A\n"
        )
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()
        assert auth.get_tenant_id() == "tenant-A"

        # Simulate user switching az tenant, then re-logging in
        mock_run.return_value = MagicMock(
            returncode=0, stdout="tenant-B\n"
        )
        auth.set_access_mode("azure_cli")
        auth.set_azure_cli()  # Should force refresh, get tenant-B
        assert auth.get_tenant_id() == "tenant-B"
