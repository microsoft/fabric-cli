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

        with pytest.raises(FabricCLIError) as exc_info:
            auth._acquire_token_from_azure_cli(con.SCOPE_FABRIC_DEFAULT)

        # Should not contain the raw token
        assert "eyJ0eXAi" not in str(exc_info.value)
        assert "manually to diagnose" in str(exc_info.value)


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

        auth._acquire_token_from_azure_cli(con.SCOPE_AZURE_DEFAULT)

        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )
