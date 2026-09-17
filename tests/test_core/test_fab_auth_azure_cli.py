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


class TestAzureCliIdentityType:
    """Test that azure_cli is a valid identity type."""

    def test_azure_cli_in_auth_keys_success(self):
        """azure_cli should be in the allowed identity types."""
        assert "azure_cli" in con.AUTH_KEYS[con.IDENTITY_TYPE]

    def test_set_access_mode_accepts_azure_cli_success(self, azure_cli_auth_fixture):
        """set_access_mode should accept azure_cli without raising."""
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        assert auth.get_identity_type() == "azure_cli"

    def test_validate_azure_cli_identity_checks_active_mode_success(
        self, azure_cli_auth_fixture
    ):
        auth = FabAuth()
        auth._auth_info = {con.IDENTITY_TYPE: "azure_cli"}

        with patch.object(auth, "get_access_token") as get_access_token:
            auth.validate_azure_cli_identity()

        get_access_token.assert_called_once_with(
            con.SCOPE_FABRIC_DEFAULT, interactive_renew=False
        )

    @pytest.mark.parametrize(
        "identity_type", [None, "user", "service_principal", "managed_identity"]
    )
    def test_validate_azure_cli_identity_skips_other_auth_modes_success(
        self, identity_type, azure_cli_auth_fixture
    ):
        auth = FabAuth()
        auth._auth_info = (
            {con.IDENTITY_TYPE: identity_type} if identity_type is not None else {}
        )

        with patch.object(auth, "get_access_token") as get_access_token:
            auth.validate_azure_cli_identity()

        get_access_token.assert_not_called()

    @pytest.mark.parametrize(
        "claims",
        [
            {},
            {"tid": "tenant-A"},
            {"oid": "principal-A"},
        ],
    )
    def test_check_azure_cli_identity_missing_claims_failure(
        self, claims, azure_cli_auth_fixture
    ):
        """Missing tenant or principal claims should fail authentication."""
        auth = FabAuth()
        auth._set_auth_properties(
            {
                con.IDENTITY_TYPE: "azure_cli",
                con.FAB_TENANT_ID: "tenant-A",
                con.FAB_PRINCIPAL_ID: "principal-A",
            }
        )

        with pytest.raises(FabricCLIError) as exc_info:
            auth._check_azure_cli_identity(claims)

        assert ErrorMessages.Auth.azure_cli_identity_claims_missing() in str(
            exc_info.value
        )
        assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
        assert auth.get_identity_type() == "azure_cli"
        assert auth.get_tenant_id() == "tenant-A"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-A"

    def test_unchanged_identity_does_not_reset_state_success(
        self, azure_cli_auth_fixture
    ):
        """A matching identity should not rewrite or clear authentication state."""
        auth = FabAuth()
        auth._set_auth_properties(
            {
                con.IDENTITY_TYPE: "azure_cli",
                con.FAB_TENANT_ID: "tenant-A",
                con.FAB_PRINCIPAL_ID: "principal-A",
            }
        )

        with (
            patch.object(auth, "_set_auth_properties") as mock_set_properties,
            patch.object(auth, "logout") as mock_logout,
            patch.object(fab_mem_store, "clear_caches") as mock_clear_caches,
            patch.object(Context(), "reset_context") as mock_reset_context,
        ):
            auth._check_azure_cli_identity({"tid": "tenant-A", "oid": "principal-A"})

        mock_set_properties.assert_not_called()
        mock_logout.assert_not_called()
        mock_clear_caches.assert_not_called()
        mock_reset_context.assert_not_called()
        assert auth.get_identity_type() == "azure_cli"
        assert auth.get_tenant_id() == "tenant-A"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-A"

    @pytest.mark.parametrize(
        ("stored_properties", "expected_tenant", "expected_principal"),
        [
            (
                {con.FAB_TENANT_ID: "tenant-A"},
                "tenant-A",
                "principal-A",
            ),
            (
                {con.FAB_PRINCIPAL_ID: "principal-A"},
                "tenant-A",
                "principal-A",
            ),
        ],
    )
    def test_partial_identity_baseline_is_completed_success(
        self,
        stored_properties,
        expected_tenant,
        expected_principal,
        azure_cli_auth_fixture,
    ):
        """A partial stored baseline should be completed from matching claims."""
        auth = FabAuth()
        auth._set_auth_properties(stored_properties)

        auth._check_azure_cli_identity({"tid": "tenant-A", "oid": "principal-A"})

        assert auth.get_tenant_id() == expected_tenant
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == expected_principal

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_first_token_acquisition_stores_identity_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """First token acquisition should store tenant and principal from JWT."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None

        assert auth.get_tenant_id() is None
        with (
            patch.object(
                auth,
                "_decode_jwt_token",
                return_value={"tid": "discovered-tenant", "oid": "principal-A"},
            ),
            patch.object(auth, "logout", wraps=auth.logout) as mock_logout,
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "discovered-tenant"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-A"
        mock_logout.assert_not_called()

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_tenant_drift_logs_out_failure(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """A changed Azure CLI tenant should log out and reset cached state."""
        mock_credential, _ = _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None
        context = Context()
        with (
            patch.object(
                auth,
                "_decode_jwt_token",
                side_effect=[
                    {"tid": "original-tenant", "oid": "principal-A"},
                    {"tid": "new-tenant", "oid": "principal-A"},
                ],
            ),
            patch.object(auth, "logout", wraps=auth.logout) as mock_logout,
            patch.object(
                fab_mem_store, "clear_caches", wraps=fab_mem_store.clear_caches
            ) as mock_clear_caches,
            patch.object(
                context, "reset_context", wraps=context.reset_context
            ) as mock_reset_context,
            patch("fabric_cli.core.fab_auth.fab_logger.log_warning") as mock_warning,
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
            fab_mem_store._get_workspaces_from_cache.cache.update({"key": "value"})
            fab_mem_store._get_workspace_folders_from_cache.cache.update(
                {"key": "value"}
            )
            with pytest.raises(FabricCLIError) as exc_info:
                auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert "Run `fab auth login --azure-cli`" in exc_info.value.message
        assert auth.get_tenant_id() is None
        assert auth.get_identity_type() is None
        assert auth._azure_cli_credential is None
        assert fab_mem_store._get_workspaces_from_cache.cache.currsize == 0
        assert fab_mem_store._get_workspace_folders_from_cache.cache.currsize == 0
        mock_credential_class.assert_called_once()
        assert mock_credential.get_token.call_count == 2
        mock_logout.assert_called_once_with()
        mock_clear_caches.assert_called_once_with()
        mock_reset_context.assert_called_once_with()
        mock_warning.assert_called_once_with("Change detected in Azure CLI Tenant ID")

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_principal_drift_logs_out_failure(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """A changed Azure CLI principal should log out and reset cached state."""
        mock_credential, _ = _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None
        context = Context()
        with (
            patch.object(
                auth,
                "_decode_jwt_token",
                side_effect=[
                    {"tid": "tenant-A", "oid": "principal-A"},
                    {"tid": "tenant-A", "oid": "principal-B"},
                ],
            ),
            patch.object(auth, "logout", wraps=auth.logout) as mock_logout,
            patch.object(
                fab_mem_store, "clear_caches", wraps=fab_mem_store.clear_caches
            ) as mock_clear_caches,
            patch.object(
                context, "reset_context", wraps=context.reset_context
            ) as mock_reset_context,
            patch("fabric_cli.core.fab_auth.fab_logger.log_warning") as mock_warning,
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
            fab_mem_store._get_workspaces_from_cache.cache.update({"key": "value"})
            fab_mem_store._get_workspace_folders_from_cache.cache.update(
                {"key": "value"}
            )
            with pytest.raises(FabricCLIError) as exc_info:
                auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert "Run `fab auth login --azure-cli`" in exc_info.value.message
        assert auth.get_tenant_id() is None
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) is None
        assert auth.get_identity_type() is None
        assert auth._azure_cli_credential is None
        assert fab_mem_store._get_workspaces_from_cache.cache.currsize == 0
        assert fab_mem_store._get_workspace_folders_from_cache.cache.currsize == 0
        mock_credential_class.assert_called_once()
        assert mock_credential.get_token.call_count == 2
        mock_logout.assert_called_once_with()
        mock_clear_caches.assert_called_once_with()
        mock_reset_context.assert_called_once_with()
        mock_warning.assert_called_once_with(
            "Change detected in Azure CLI Principal ID"
        )

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_tenant_and_principal_drift_logs_out_failure(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """Changed Azure CLI tenant and principal should report both changes."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None
        context = Context()
        with (
            patch.object(
                auth,
                "_decode_jwt_token",
                side_effect=[
                    {"tid": "tenant-A", "oid": "principal-A"},
                    {"tid": "tenant-B", "oid": "principal-B"},
                ],
            ),
            patch.object(auth, "logout", wraps=auth.logout) as mock_logout,
            patch.object(
                fab_mem_store, "clear_caches", wraps=fab_mem_store.clear_caches
            ) as mock_clear_caches,
            patch.object(
                context, "reset_context", wraps=context.reset_context
            ) as mock_reset_context,
            patch("fabric_cli.core.fab_auth.fab_logger.log_warning") as mock_warning,
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
            with pytest.raises(FabricCLIError):
                auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert auth.get_tenant_id() is None
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) is None
        assert auth.get_identity_type() is None
        assert auth._azure_cli_credential is None
        mock_logout.assert_called_once_with()
        mock_clear_caches.assert_called_once_with()
        mock_reset_context.assert_called_once_with()
        mock_warning.assert_called_once_with(
            "Change detected in Azure CLI Tenant ID and Principal ID"
        )


class TestAzureCliTokenAcquisition:
    """Test token acquisition via AzureCliCredential."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_acquire_token_dispatches_to_azure_cli_success(
        self, mock_credential_class, azure_cli_auth_fixture
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
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_acquire_token_credential_inherits_azure_cli_context_success(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_acquire_token_from_azure_cli_credential_unavailable_failure(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_sdk_exception_surfaces_message_failure(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_unknown_exception_returns_safe_message_failure(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_singleton_credential_reused_across_calls_success(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_different_scopes_use_same_credential_success(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_logout_clears_credential_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
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
    def test_onelake_scope_success(self, mock_credential_class, azure_cli_auth_fixture):
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
    def test_azure_management_scope_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
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
    def test_logout_then_login_records_new_identity_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """Explicit logout should allow a different identity to become the baseline."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")

        with patch.object(
            auth,
            "_decode_jwt_token",
            side_effect=[
                {"tid": "tenant-A", "oid": "principal-A"},
                {"tid": "tenant-B", "oid": "principal-B"},
            ],
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
            auth.logout()
            auth.set_access_mode("azure_cli")
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert auth.get_identity_type() == "azure_cli"
        assert auth.get_tenant_id() == "tenant-B"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-B"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_first_acquisition_discovers_tenant_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """First token acquisition should discover tenant from JWT claims."""
        _mock_credential(mock_credential_class)

        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        auth._azure_cli_credential = None
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "discovered-tenant", "oid": "principal-A"},
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "discovered-tenant"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_re_login_resets_state_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """Re-login in azure_cli mode clears the identity baseline so a new
        identity is adopted without a drift error."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "tenant-A", "oid": "principal-A"},
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "tenant-A"

        # Re-login (set_access_mode again while already azure_cli) must clear baseline
        auth.set_access_mode("azure_cli")
        assert auth.get_tenant_id() is None
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) is None

        # A different identity now becomes the new baseline, no drift error
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "tenant-B", "oid": "principal-B"},
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth.get_tenant_id() == "tenant-B"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-B"

    @patch("fabric_cli.utils.fab_version_check.check_and_notify_update")
    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_relogin_after_identity_switch_success(
        self, mock_credential_class, _mock_version_check, azure_cli_auth_fixture
    ):
        """`fab auth login --azure-cli` after switching the az identity must
        succeed on the first attempt and adopt the new identity as baseline."""
        import argparse

        from fabric_cli.commands.auth import fab_auth as auth_cmd

        _mock_credential(mock_credential_class)
        auth = FabAuth()

        def _login_args():
            return argparse.Namespace(
                azure_cli=True,
                identity=False,
                username=None,
                password=None,
                tenant=None,
                certificate=None,
                federated_token=None,
            )

        # First login establishes identity A as the baseline
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "tenant-A", "oid": "principal-A"},
        ):
            assert auth_cmd.init(_login_args()) is True
        assert auth.get_tenant_id() == "tenant-A"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-A"

        # After `az login` to identity B, re-login must NOT raise a drift error
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "tenant-B", "oid": "principal-B"},
        ):
            assert auth_cmd.init(_login_args()) is True

        assert auth.get_identity_type() == "azure_cli"
        assert auth.get_tenant_id() == "tenant-B"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-B"


class TestNonAzureCliIsolation:
    """Verify each auth method uses only its own credential path — no overlap."""

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_user_identity_does_not_invoke_azure_cli_success(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_service_principal_does_not_invoke_azure_cli_success(
        self, mock_credential_class, azure_cli_auth_fixture
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
    def test_azure_cli_does_not_invoke_msal_app_success(
        self, mock_credential_class, azure_cli_auth_fixture
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


class TestAuthModeTransitions:
    """Guard set_access_mode transitions affected by the azure_cli baseline reset."""

    @pytest.mark.parametrize("mode", ["user", "service_principal", "managed_identity"])
    def test_same_mode_relogin_preserves_state_non_azure_cli_success(
        self, mode, azure_cli_auth_fixture
    ):
        """Re-login in a non-azure_cli mode must not reset stored state."""
        auth = FabAuth()
        auth.set_access_mode(mode)
        auth._set_auth_property(con.FAB_TENANT_ID, "seed-tenant")
        auth._set_auth_property(con.FAB_PRINCIPAL_ID, "seed-principal")

        auth.set_access_mode(mode)

        assert auth.get_identity_type() == mode
        assert auth.get_tenant_id() == "seed-tenant"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "seed-principal"

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_switch_from_azure_cli_to_user_clears_principal_baseline_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """Leaving azure_cli for another mode must clear the identity baseline."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("azure_cli")
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "tenant-A", "oid": "principal-A"},
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-A"

        auth.set_access_mode("user")

        assert auth.get_identity_type() == "user"
        assert auth.get_tenant_id() is None
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) is None

    @patch("fabric_cli.core.fab_auth.AzureCliCredential")
    def test_switch_from_user_to_azure_cli_starts_clean_success(
        self, mock_credential_class, azure_cli_auth_fixture
    ):
        """Entering azure_cli from another mode must not carry a stale principal."""
        _mock_credential(mock_credential_class)
        auth = FabAuth()
        auth.set_access_mode("user")
        auth._set_auth_property(con.FAB_PRINCIPAL_ID, "stale-principal")

        auth.set_access_mode("azure_cli")
        with patch.object(
            auth,
            "_decode_jwt_token",
            return_value={"tid": "tenant-B", "oid": "principal-B"},
        ):
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        assert auth.get_tenant_id() == "tenant-B"
        assert auth._get_auth_property(con.FAB_PRINCIPAL_ID) == "principal-B"
