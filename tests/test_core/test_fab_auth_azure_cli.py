# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_mem_store


def _mock_credential(mock_class):
    """Set up a mock AzureCliCredential that returns an opaque token."""
    mock_token = MagicMock()
    mock_token.token = "test string"
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
        "FAB_SPN_CERT_PASSWORD",
        "FAB_SPN_FEDERATED_TOKEN",
        "FAB_MANAGED_IDENTITY",
    ):
        monkeypatch.delenv(var, raising=False)
    # Clear singleton state between tests
    auth = FabAuth()
    monkeypatch.setattr(auth, "auth_file", str(tmp_path / "auth.json"))
    monkeypatch.setattr(auth, "cache_file", str(tmp_path / "cache.bin"))
    auth._azure_cli_credential = None
    auth._auth_info = {}
    auth.app = None
    context = Context()
    context._context = None
    monkeypatch.setattr(context, "_context_file", str(tmp_path / "context.json"))

    monkeypatch.setattr(
        auth,
        "_decode_jwt_token",
        MagicMock(return_value={"tid": "test-tenant"}),
    )

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

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_first_token_acquisition_stores_tenant(
        self, mock_credential_class, temp_dir_fixture
    ):
        """First token acquisition should discover and store tenant from JWT."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        assert auth.get_tenant_id() is None
        with patch.object(
            auth, "_decode_jwt_token", return_value={"tid": "discovered-tenant"}
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "discovered-tenant"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_tenant_updated_on_subsequent_calls(
        self, mock_credential_class, temp_dir_fixture
    ):
        """A changed Azure CLI tenant should reset context and cached resources."""
        mock_credential, _ = _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None
        with patch.object(
            auth,
            "_decode_jwt_token",
            side_effect=[{"tid": "original-tenant"}, {"tid": "new-tenant"}],
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
            fab_mem_store._get_workspaces_from_cache.cache.update({"key": "value"})
            fab_mem_store._get_workspace_folders_from_cache.cache.update(
                {"key": "value"}
            )
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "new-tenant"
        assert auth.get_identity_type() == "azure_cli"
        assert Context().get_tenant_id() == "new-tenant"
        assert fab_mem_store._get_workspaces_from_cache.cache.currsize == 0
        assert fab_mem_store._get_workspace_folders_from_cache.cache.currsize == 0
        mock_credential_class.assert_called_once()
        assert mock_credential.get_token.call_count == 2


class TestAzureCliTokenAcquisition:
    """Test token acquisition via AzureCliCredential."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_dispatches_to_azure_cli(
        self, mock_credential_class, temp_dir_fixture
    ):
        """acquire_token should use AzureCliCredential for azure_cli identity."""
        mock_credential, _ = _mock_credential(mock_credential_class)

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
        mock_credential, _ = _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        result = auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert result["access_token"] == "test string"
        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_credential_inherits_azure_cli_context(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Credential should be created without tenant_id — inherits Azure CLI context."""
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
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
        mock_credential.get_token.side_effect = ClientAuthenticationError(
            "Tenant not found"
        )
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
        mock_credential.get_token.side_effect = RuntimeError("accessToken: eyJ0eXAi...")
        mock_credential_class.return_value = mock_credential

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert "eyJ0eXAi" not in str(exc_info.value)
        assert "Unable to get a token from Azure CLI" in str(exc_info.value)


class TestAzureCliSingletonCredential:
    """Test singleton AzureCliCredential lifecycle."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_singleton_credential_reused_across_calls(
        self, mock_credential_class, temp_dir_fixture
    ):
        """Repeated calls should reuse the same AzureCliCredential instance."""
        _mock_credential(mock_credential_class)

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
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        auth._acquire_token_from_azure_cli(con.SCOPE_ONELAKE_DEFAULT)

        # Same credential instance for both scopes
        mock_credential_class.assert_called_once()
        assert mock_credential_class.return_value.get_token.call_count == 2

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_logout_clears_credential(self, mock_credential_class, temp_dir_fixture):
        """logout() should clear the credential instance."""
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        # Acquire a token — creates singleton credential
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        auth.logout()
        assert auth._azure_cli_credential is None


class TestAzureCliScopeHandling:
    """Test that different scopes are correctly passed to Azure CLI."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_onelake_scope(self, mock_credential_class, temp_dir_fixture):
        """OneLake scope should be passed correctly."""
        mock_credential, _ = _mock_credential(mock_credential_class)

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
        mock_credential, _ = _mock_credential(mock_credential_class)

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
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        # Acquire token to set credential
        auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._azure_cli_credential is not None

        auth.logout()
        assert auth._azure_cli_credential is None

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_first_acquisition_discovers_tenant(
        self, mock_credential_class, temp_dir_fixture
    ):
        """First token acquisition should discover tenant from JWT claims."""
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None
        with patch.object(
            auth, "_decode_jwt_token", return_value={"tid": "discovered-tenant"}
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "discovered-tenant"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_re_login_resets_state(self, mock_credential_class, temp_dir_fixture):
        """Re-login (set_access_mode again) should reset state."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        with patch.object(auth, "_decode_jwt_token", return_value={"tid": "tenant-A"}):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "tenant-A"

        # Re-login — set_access_mode("azure_cli") when already azure_cli does NOT logout
        auth.set_access_mode("azure_cli")
        assert auth.get_tenant_id() == "tenant-A"


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
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        mock_app = MagicMock()
        auth.app = mock_app

        result = auth.acquire_token(con.SCOPE_FABRIC_DEFAULT)
        assert "access_token" in result
        mock_app.acquire_token_silent.assert_not_called()
        mock_app.acquire_token_interactive.assert_not_called()
        mock_app.acquire_token_for_client.assert_not_called()
