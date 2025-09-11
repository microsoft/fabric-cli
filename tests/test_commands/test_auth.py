# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from unittest.mock import MagicMock, patch

import pytest
import questionary

from fabric_cli.commands.auth import fab_auth
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import Tenant
from fabric_cli.errors import ErrorMessages


class TestAuth:
    def test_init_with_interactive_auth(self, mock_fab_auth, mock_fab_context):
        # Arrange
        with patch(
            "fabric_cli.utils.fab_ui.prompt_select_item",
            return_value="Interactive with a web browser",
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with("user", None)
            assert_get_access_token(mock_fab_auth_instance)
            assert result is True

            assert_fab_context(mock_fab_context)

    def test_init_with_interactive_auth_tenant_args(
        self,
        mock_fab_auth,
        mock_fab_context,
    ):
        # Arrange
        with patch(
            "fabric_cli.utils.fab_ui.prompt_select_item",
            return_value="Interactive with a web browser",
        ):
            args = prepare_auth_args({"tenant": "mock_tenant"})

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with(
                "user", "mock_tenant"
            )
            assert_get_access_token(mock_fab_auth_instance)
            assert result is True

            assert_fab_context(mock_fab_context)

    def test_init_with_spn_empty_client_secret(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with secret",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch("fabric_cli.utils.fab_ui.prompt_password", return_value=""),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_called_once()
            assert (
                mock_fab_ui_print_error.call_args[0][0].message
                == ErrorMessages.Auth.spn_auth_missing_client_secret()
            )
            assert (
                mock_fab_ui_print_error.call_args[0][0].status_code
                == fab_constant.ERROR_SPN_AUTH_MISSING
            )

            assert_fab_auth_not_called(mock_fab_auth)

    def test_init_with_spn_no_client_secret_ctrlc(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
        capsys,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with secret",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password", side_effect=cancelled_prompt
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_not_called()  # No error message for CTRL+C
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)

    def test_init_with_spn_client_secret_auth(
        self, mock_fab_auth, mock_fab_context, mock_fab_logger_log_warning
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with secret",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password", return_value="mock_password"
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_logger_log_warning.assert_called_once()

            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with(
                "service_principal", "mocked_tenant_id"
            )
            mock_fab_auth_instance.set_spn.assert_called_with(
                "mocked_client_id", password="mock_password"
            )
            assert_get_access_token(mock_fab_auth_instance)
            assert result is True

            mock_fab_context_instance = mock_fab_context.get("instance")
            assert mock_fab_context_instance.context == Tenant(
                name="Unknown", id="mocked_tenant_id"
            )

    def test_init_with_spn_federated_token_auth(
        self, mock_fab_auth, mock_fab_context, mock_fab_logger_log_warning
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with federated credential",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_federated_token",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_logger_log_warning.assert_called_once()

            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with(
                "service_principal", "mocked_tenant_id"
            )
            mock_fab_auth_instance.set_spn.assert_called_with(
                "mocked_client_id", client_assertion="mocked_federated_token"
            )
            assert_get_access_token(mock_fab_auth_instance)
            assert result is True

            assert_fab_context(mock_fab_context)

    def test_init_with_spn_empty_federated_token(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with federated credential",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_called_once()
            assert (
                mock_fab_ui_print_error.call_args[0][0].message
                == ErrorMessages.Auth.spn_auth_missing_federated_token()
            )
            assert (
                mock_fab_ui_print_error.call_args[0][0].status_code
                == fab_constant.ERROR_SPN_AUTH_MISSING
            )
            assert_fab_auth_not_called(mock_fab_auth)

    def test_init_with_spn_no_federated_token_ctrlc(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
        capsys,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with federated credential",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                side_effect=cancelled_prompt,
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_not_called()  # No error message for CTRL+C
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)

    def test_init_with_spn_cert_auth(
        self, mock_fab_auth, mock_fab_context, mock_fab_logger_log_warning
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            elif ask == "Enter certificate path (PEM, PKCS12 formats):":
                return "mocked_cert_path"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_cert_password",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_logger_log_warning.assert_called_once()

            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with(
                "service_principal", "mocked_tenant_id"
            )
            mock_fab_auth_instance.set_spn.assert_called_with(
                "mocked_client_id",
                cert_path="mocked_cert_path",
                password="mocked_cert_password",
            )
            mock_fab_auth_instance.get_access_token.assert_any_call(
                scope=fab_constant.SCOPE_FABRIC_DEFAULT
            )
            mock_fab_auth_instance.get_access_token.assert_any_call(
                scope=fab_constant.SCOPE_ONELAKE_DEFAULT
            )
            mock_fab_auth_instance.get_access_token.assert_any_call(
                scope=fab_constant.SCOPE_AZURE_DEFAULT
            )
            assert result is True

            mock_fab_context_instance = mock_fab_context.get("instance")
            assert mock_fab_context_instance.context == Tenant(
                name="Unknown", id="mocked_tenant_id"
            )

    def test_init_with_spn_cert_auth_no_tenant_id_ctrlc(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
        capsys,
    ):
        # Arrange
        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=cancelled_prompt),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_not_called()  # No error message for CTRL+C
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)

    def test_init_with_spn_cert_auth_empty_tenant_id(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter tenant ID:":
                return ""  # Empty string
            return "mock_value"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_cert_password",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_called_once()
            assert (
                mock_fab_ui_print_error.call_args[0][0].message
                == ErrorMessages.Auth.spn_auth_missing_tenant_id()
            )
            assert (
                mock_fab_ui_print_error.call_args[0][0].status_code
                == fab_constant.ERROR_SPN_AUTH_MISSING
            )
            assert_fab_auth_not_called(mock_fab_auth)

    def test_init_with_spn_cert_auth_no_client_id_ctrlc(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
        capsys,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            if ask == "Enter client ID:":
                cancelled_prompt()
            else:
                return "mock_value"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_cert_password",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_not_called()  # No error message for CTRL+C
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)

    def test_init_with_spn_cert_auth_empty_client_id(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            if ask == "Enter client ID:":
                return ""  # Empty string
            return "mock_value"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_cert_password",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_called_once()
            assert (
                mock_fab_ui_print_error.call_args[0][0].message
                == ErrorMessages.Auth.spn_auth_missing_client_id()
            )
            assert (
                mock_fab_ui_print_error.call_args[0][0].status_code
                == fab_constant.ERROR_SPN_AUTH_MISSING
            )
            assert_fab_auth_not_called(mock_fab_auth)

    def test_init_with_spn_cert_auth_no_certificate_ctrlc(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
        capsys,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            elif ask == "Enter certificate path (PEM, PKCS12 formats):":
                cancelled_prompt()
            else:
                return "mock_value"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_cert_password",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_not_called()  # No error message for CTRL+C
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)

    def test_init_with_spn_cert_auth_empty_certificate(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID:":
                return "mocked_client_id"
            elif ask == "Enter tenant ID:":
                return "mocked_tenant_id"
            elif ask == "Enter certificate path (PEM, PKCS12 formats):":
                return ""  # Empty string
            return "mock_value"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Service principal authentication with certificate",
            ),
            patch("fabric_cli.utils.fab_ui.prompt_ask", side_effect=mock_prompt_ask),
            patch(
                "fabric_cli.utils.fab_ui.prompt_password",
                return_value="mocked_cert_password",
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_called_once()
            assert (
                mock_fab_ui_print_error.call_args[0][0].message
                == ErrorMessages.Auth.spn_auth_missing_cert_path()
            )
            assert (
                mock_fab_ui_print_error.call_args[0][0].status_code
                == fab_constant.ERROR_SPN_AUTH_MISSING
            )
            assert_fab_auth_not_called(mock_fab_auth)

    def test_init_with_mi_auth_system_assigned(
        self,
        mock_fab_auth,
        mock_fab_context,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID (only for User Assigned):":
                return ""
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Managed identity authentication",
            ),
            patch(
                "fabric_cli.utils.fab_ui.prompt_ask",
                side_effect=mock_prompt_ask,
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with(
                "managed_identity"
            )
            mock_fab_auth_instance.set_managed_identity.assert_called_with("")
            mock_fab_auth_instance.get_access_token.assert_any_call(
                scope=fab_constant.SCOPE_FABRIC_DEFAULT
            )
            mock_fab_auth_instance.get_access_token.assert_any_call(
                scope=fab_constant.SCOPE_ONELAKE_DEFAULT
            )
            mock_fab_auth_instance.get_access_token.assert_any_call(
                scope=fab_constant.SCOPE_AZURE_DEFAULT
            )
            assert result is True

            mock_fab_context_instance = mock_fab_context.get("instance")
            assert mock_fab_context_instance.context == Tenant(
                name="Unknown", id="mocked_tenant_id"
            )

    def test_init_with_mi_auth_user_assigned(self, mock_fab_auth, mock_fab_context):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID (only for User Assigned):":
                return "mocked_client_id"
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Managed identity authentication",
            ),
            patch(
                "fabric_cli.utils.fab_ui.prompt_ask",
                side_effect=mock_prompt_ask,
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            mock_fab_auth_instance = mock_fab_auth.get("instance")
            mock_fab_auth_instance.set_access_mode.assert_called_with(
                "managed_identity"
            )
            mock_fab_auth_instance.set_managed_identity.assert_called_with(
                "mocked_client_id"
            )
            assert_get_access_token(mock_fab_auth_instance)
            assert result is True

            assert_fab_context(mock_fab_context)

    def test_init_with_mi_auth_system_assigned_command_line(
        self, mock_fab_auth, mock_fab_context
    ):
        args = prepare_auth_args({"identity": True})

        # Act
        fab_auth.init(args)

        # Assert
        mock_fab_auth_instance = mock_fab_auth.get("instance")
        mock_fab_auth_instance.set_access_mode.assert_called_with("managed_identity")
        mock_fab_auth_instance.set_managed_identity.assert_called_with(None)
        assert_get_access_token(mock_fab_auth_instance)

        mock_fab_context_instance = mock_fab_context.get("instance")
        assert mock_fab_context_instance.context == Tenant(
            name="Unknown", id="mocked_tenant_id"
        )

    def test_init_with_mi_auth_ctrlc(
        self,
        mock_fab_auth,
        mock_fab_logger_log_warning,
        mock_fab_ui_print_error,
        capsys,
    ):
        # Arrange
        def mock_prompt_ask(ask):
            if ask == "Enter client ID (only for User Assigned):":
                return cancelled_prompt()
            else:
                return "unknown ask"

        with (
            patch(
                "fabric_cli.utils.fab_ui.prompt_select_item",
                return_value="Managed identity authentication",
            ),
            patch(
                "fabric_cli.utils.fab_ui.prompt_ask",
                side_effect=mock_prompt_ask,
            ),
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is None
            mock_fab_logger_log_warning.assert_called_once()
            mock_fab_ui_print_error.assert_not_called()  # No error message for CTRL+C
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)

    def test_init_with_tenant_args_auth(
        self, mock_fab_auth, mock_fab_context, mock_fab_logger_log_warning
    ):
        # Arrange
        args = prepare_auth_args(
            {
                "username": "mock_user_name",
                "password": "mock_password",
                "tenant": "mock_tenant",
            }
        )

        # Act
        fab_auth.init(args)

        # Assert
        mock_fab_auth_instance = mock_fab_auth.get("instance")
        mock_fab_auth_instance.set_access_mode.assert_called_with(
            "service_principal", "mock_tenant"
        )
        mock_fab_auth_instance.set_spn.assert_called_with(
            "mock_user_name", password="mock_password"
        )
        assert_get_access_token(mock_fab_auth_instance)

        mock_fab_context_instance = mock_fab_context.get("instance")
        assert mock_fab_context_instance.context == Tenant(
            name="Unknown", id="mocked_tenant_id"
        )

    def test_init_with_tenant_and_cert_args_auth(
        self, mock_fab_auth, mock_fab_context, mock_fab_logger_log_warning
    ):
        # Arrange
        args = prepare_auth_args(
            {
                "username": "mock_user_name",
                "certificate": "mock_cert",
                "tenant": "mock_tenant",
            }
        )

        # Act
        fab_auth.init(args)

        # Assert
        mock_fab_auth_instance = mock_fab_auth.get("instance")
        mock_fab_auth_instance.set_access_mode.assert_called_with(
            "service_principal", "mock_tenant"
        )
        mock_fab_auth_instance.set_spn.assert_called_with(
            "mock_user_name", cert_path="mock_cert", password=None
        )
        assert_get_access_token(mock_fab_auth_instance)

        mock_fab_context_instance = mock_fab_context.get("instance")
        assert mock_fab_context_instance.context == Tenant(
            name="Unknown", id="mocked_tenant_id"
        )

    def test_init_with_args_auth_missing_arg_raise_exception(self):
        # Test without tenant
        # Arrange
        args_without_tenant = argparse.Namespace(
            username="mock_user_name",
            password="mock_password",
            tenant=None,
            identity=None,
            certificate=None,
            federated_token=None,
        )

        # Act
        with pytest.raises(FabricCLIError) as ex:
            fab_auth.init(args_without_tenant)
        assert ex.value.status_code == fab_constant.ERROR_INVALID_INPUT

        # Test without password
        # Arrange
        args_without_password_nor_cert = argparse.Namespace(
            username="mock_user_name",
            password=None,
            tenant="mock_tenant",
            identity=None,
            certificate=None,
            federated_token=None,
        )

        # Act
        with pytest.raises(FabricCLIError) as ex:
            fab_auth.init(args_without_password_nor_cert)
        assert ex.value.status_code == fab_constant.ERROR_INVALID_INPUT

        # Test without username
        # Arrange
        args_without_user = argparse.Namespace(
            username=None,
            password="mock_password",
            tenant="mock_tenant",
            identity=None,
            certificate=None,
            federated_token=None,
        )

        # Act
        with pytest.raises(FabricCLIError) as ex:
            fab_auth.init(args_without_user)
        assert ex.value.status_code == fab_constant.ERROR_INVALID_INPUT

    def test_auth_logout(
        self, mock_fab_context, mock_print_done, mock_fab_state_config
    ):
        # Arrange
        args = argparse.Namespace()

        # Act
        fab_auth.logout(args)

        # Assert
        mock_fab_context_instance = mock_fab_context.get("instance")
        mock_fab_context_instance.reset_context.assert_called_once()

        mock_fab_state_config_instance = mock_fab_state_config.get("instance")
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_DEFAULT_CAPACITY, ""
        )
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_DEFAULT_CAPACITY_ID, ""
        )
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_LOCAL_DEFINITION_LABELS, ""
        )
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, ""
        )
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_DEFAULT_AZ_ADMIN, ""
        )
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, ""
        )
        mock_fab_state_config_instance.set_config.assert_any_call(
            fab_constant.FAB_DEFAULT_AZ_LOCATION, ""
        )

        mock_print_done.assert_called_once()

    def test_auth_status(self, mock_fab_auth, mock_questionary_print):
        # Arrange
        args = MagicMock()
        with patch(
            "fabric_cli.commands.auth.fab_auth._get_token_info_from_bearer_token",
            return_value={
                "appid": "mocked_appid",
                "upn": "mocked_upn",
                "oid": "mocke_oid",
            },
        ):
            # Act
            fab_auth.status(args)

            # Assert
            assert any(
                "Account" in call.args[0] for call in mock_questionary_print.mock_calls
            )
            assert any(
                "Tenant ID" in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                "App ID" in call.args[0] for call in mock_questionary_print.mock_calls
            )
            assert any(
                "Token (fabric/powerbi)" in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                "Token (storage)" in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                "Token (azure)" in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                "mock************************************" in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_init_when_user_cancels_the_prompt(
        self, mock_fab_auth, mock_fab_context, mock_fab_logger_log_warning, capsys
    ):

        # Arrange
        with patch(
            "fabric_cli.utils.fab_ui.prompt_select_item",
            side_effect=cancelled_prompt,
        ):
            args = prepare_auth_args()

            # Act
            result = fab_auth.init(args)

            # Assert
            assert result is False
            mock_fab_logger_log_warning.assert_not_called()
            assert_fab_auth_not_called(mock_fab_auth)
            assert_prompt_cancelled(capsys)


# Helpers


def assert_fab_context(mock_fab_context):
    mock_fab_context_instance = mock_fab_context.get("instance")
    assert mock_fab_context_instance.context == Tenant(
        name="Unknown", id="mocked_tenant_id"
    )


def prepare_auth_args(args=None):
    args = args or {}  # Ensure args is a dictionary
    return MagicMock(
        **{
            key: args.get(key)
            for key in [
                "username",
                "password",
                "tenant",
                "identity",
                "certificate",
                "federated_token",
            ]
        }
    )


def assert_fab_auth_not_called(mock_fab_auth):
    mock_fab_auth_instance = mock_fab_auth.get("instance")
    mock_fab_auth_instance.set_access_mode.assert_not_called()
    mock_fab_auth_instance.set_tenant.assert_not_called()
    mock_fab_auth_instance.set_spn.assert_not_called()
    mock_fab_auth_instance.get_access_token.assert_not_called()


def assert_get_access_token(mock_fab_auth_instance):
    mock_fab_auth_instance.get_access_token.assert_any_call(
        scope=fab_constant.SCOPE_FABRIC_DEFAULT
    )
    mock_fab_auth_instance.get_access_token.assert_any_call(
        scope=fab_constant.SCOPE_ONELAKE_DEFAULT
    )
    mock_fab_auth_instance.get_access_token.assert_any_call(
        scope=fab_constant.SCOPE_AZURE_DEFAULT
    )


def assert_prompt_cancelled(capsys):
    captured = capsys.readouterr()
    assert "Cancelled by user" in captured.out


def cancelled_prompt(*args, **kwargs):
    # Questionary shows this when the user aborts with Ctrl-C
    print(questionary.constants.DEFAULT_KBI_MESSAGE)
    return None


@pytest.fixture()
def mock_fab_auth():
    fab_auth_instance = FabAuth()
    with patch.multiple(
        fab_auth_instance,
        get_access_token=MagicMock(return_value="mocked_access_token"),
        get_tenant_id=MagicMock(return_value="mocked_tenant_id"),
        set_access_mode=MagicMock(),
        set_tenant=MagicMock(),
        set_spn=MagicMock(),
        set_managed_identity=MagicMock(),
        logout=MagicMock(),
        # add more methods if needed
    ) as mocks:
        # mocks is a dictionary containing the mock objects for each method
        yield {"instance": fab_auth_instance, **mocks}


@pytest.fixture()
def mock_fab_context():
    fab_context_instance = Context()
    with patch.multiple(
        fab_context_instance,
        reset_context=MagicMock(),
        # add more methods if needed
    ) as mocks:
        yield {"instance": fab_context_instance, **mocks}


@pytest.fixture()
def mock_fab_state_config():
    fab_state_config_instance = fab_state_config
    with patch.multiple(fab_state_config_instance, set_config=MagicMock()) as mocks:
        yield {"instance": fab_state_config_instance, **mocks}
