# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import platform
import uuid

import pytest

from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceType
from tests.conftest import mock_questionary_print
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.data.static_test_data import StaticTestData


class TestACLs:
    # region ACL GET
    def test_acls_get_workspace_success(
        self, workspace, mock_questionary_print, cli_executor: CLIExecutor
    ):
        # Execute command
        cli_executor.exec_command(f"acl get {workspace.full_path}")

        mock_questionary_print.assert_called()
        call_args = mock_questionary_print.mock_calls

        # Assert
        assert all(
            any(key in call.args[0] for call in call_args)
            for key in ["id", "principal", "role"]
        )

        assert all("Admin" not in call.args[0] for call in call_args)

    def test_acls_get_workspace_with_query_failure(
        self, workspace, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Execute command
        cli_executor.exec_command(f"acl get {workspace.full_path} -q '.nonexistent'")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "Invalid jmespath query (https://jmespath.org)",
        )

    def test_acls_get_workspace_query_role_success(
        self, workspace, mock_questionary_print, cli_executor: CLIExecutor
    ):
        # Execute command
        cli_executor.exec_command(f"acl get {workspace.full_path} --query [].role")

        call_args, _ = mock_questionary_print.call_args
        mock_questionary_print.assert_called_once()

        # Assert
        assert "Admin" in call_args[0]
        assert "id" not in call_args[0]

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Failed to run on windows due to print format bug",
    )
    def test_acls_get_workspace_output_to_file_success(
        self, workspace, mock_questionary_print, cli_executor: CLIExecutor, tmp_path
    ):
        # Execute command
        cli_executor.exec_command(f"acl get {workspace.full_path} --output {tmp_path}")

        directory = os.path.join(tmp_path, workspace.name)
        files = os.listdir(directory)
        if len(files) != 1:
            raise ValueError(
                f"Expected exactly one file in the directory, but found {len(files)} files."
            )
        file_path = os.path.join(directory, files[0])

        with open(file_path, "r") as file:
            file_content = file.read()

        # Assert
        mock_questionary_print.assert_called()
        assert any(
            str(file_path) in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert "id" in file_content
        assert "principal" in file_content
        assert "role" in file_content
        assert "Admin" not in file_content

    def test_acls_get_lakehouse_success(
        self, item_factory, mock_questionary_print, cli_executor: CLIExecutor
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl get {lakehouse.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        assert any("id" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "principal" in call.args[0] for call in mock_questionary_print.mock_calls
        )

    # Region vistual workspace
    def test_acls_get_connection_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl get {connection.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        assert any("id" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "principal" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any("role" in call.args[0] for call in mock_questionary_print.mock_calls)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"acl get {connection.full_path} --query [*].principal"
        )

        # Assert
        assert any("id" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any("type" in call.args[0] for call in mock_questionary_print.mock_calls)

    def test_acls_get_gateway_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl get {gateway.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        assert any("id" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "principal" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any("role" in call.args[0] for call in mock_questionary_print.mock_calls)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl get {gateway.full_path} --query [*].principal")

        # Assert
        assert any("id" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any("type" in call.args[0] for call in mock_questionary_print.mock_calls)

    def test_acls_get_vws_not_supported_type_failure(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl get {domain.full_path}")

        # Assert
        _validate_unsupported_command_failure(mock_fab_ui_print_error, "get")

    # endregion
    def test_acls_get_onelake_failure(
        self,
        item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Execute command
        cli_executor.exec_command(f"acl get {lakehouse.full_path}/Files")

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert any(
            f"Universal security is disabled for '{lakehouse.name}'"
            in call.args[0].message
            for call in mock_fab_ui_print_error.mock_calls
        )

    # endregion

    # region ACL LS
    def test_acls_ls_workspace_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        role = "member"
        spn_id = test_data.service_principal.id
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {spn_id} --role {role} --force"
        )

        # Execute command
        cli_executor.exec_command(f"acl ls {workspace.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        assert any("acl" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "Admin" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any("type" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            role in call.args[0].lower() for call in mock_questionary_print.mock_calls
        )

        # -l is not passed, therefore `objectId` and `name` should not be in the output
        assert not any(
            "objectId" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert not any(
            "name" in call.args[0] for call in mock_questionary_print.mock_calls
        )

        # Clean up
        _cleanup_acl(cli_executor, workspace.full_path, spn_id)

    def test_acls_ls_workspace_query_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):

        # Test 1: Array projection for single field
        cli_executor.exec_command(f"acl ls {workspace.full_path} -q '[*].identity'")
        mock_questionary_print.assert_called()
        assert any(test_data.admin.upn in call.args[0] for call in mock_questionary_print.mock_calls)

        mock_questionary_print.reset_mock()

        # Test 2: Multiple fields using array syntax
        cli_executor.exec_command(f"acl ls {workspace.full_path} -q [].[identity,type]")
        mock_questionary_print.assert_called()
        call_args = mock_questionary_print.mock_calls[0].args[0]
        assert test_data.admin.upn in call_args and "User" in call_args
        
        mock_questionary_print.reset_mock()

        # Test 3: Object projection with field aliases
        cli_executor.exec_command(f"acl ls {workspace.full_path} -q [].{{principalInfo: identity, accessLevel: acl}}")
        mock_questionary_print.assert_called()
        call_args = mock_questionary_print.mock_calls[0].args[0]
        assert "principalInfo" in call_args and "accessLevel" in call_args
        
        # Cleanup test ACL entry
        _cleanup_acl(cli_executor, workspace.full_path,  test_data.service_principal.id)

    def test_acls_ls_workspace_long_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Execute command
        cli_executor.exec_command(f"acl ls {workspace.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        assert any("acl" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "Admin" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any("type" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "identity" in call.args[0] for call in mock_questionary_print.mock_calls
        )

        assert any(
            "objectId" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any("name" in call.args[0] for call in mock_questionary_print.mock_calls)

    def test_acls_ls_connection_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl ls {connection.full_path}")

        # Assert
        acls_ls_vws_assestion(mock_questionary_print)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl ls {connection.full_path} --long")

        # Assert
        acls_ls_vws_assestion(mock_questionary_print, long=True)

    def test_acls_ls_gateway_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl ls {gateway.full_path}")

        # Assert
        acls_ls_vws_assestion(mock_questionary_print)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl ls {gateway.full_path} --long")

        # Assert
        acls_ls_vws_assestion(mock_questionary_print, long=True)

    def test_acls_ls_lakehouse_success(
        self,
        item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Execute command
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        cli_executor.exec_command(f"acl ls {lakehouse.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        assert any("acl" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any("Read" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "Write" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any(
            "ReShare" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert any(
            "Execute" in call.args[0] for call in mock_questionary_print.mock_calls
        )

        assert any("type" in call.args[0] for call in mock_questionary_print.mock_calls)
        assert any(
            "identity" in call.args[0] for call in mock_questionary_print.mock_calls
        )

        assert not any(
            "objectId" in call.args[0] for call in mock_questionary_print.mock_calls
        )
        assert not any(
            "name" in call.args[0] for call in mock_questionary_print.mock_calls
        )

    # TODO: API Limitation: Once there's a way to enable UniversalSecurityFeature for the test workspace, update the test.
    def test_acls_ls_onelake_failure(
        self,
        item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Execute command
        cli_executor.exec_command(f"acl ls {lakehouse.full_path}/Files")

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert any(
            f"Universal security is disabled for '{lakehouse.name}'"
            in call.args[0].message
            for call in mock_fab_ui_print_error.mock_calls
        )

    def test_acls_ls_vws_not_supported_type_failure(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)
        acl_command_os = "dir" if platform.system() == "Windows" else "ls"

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"acl {acl_command_os} {domain.full_path}")

        # Assert
        _validate_unsupported_command_failure(mock_fab_ui_print_error, acl_command_os)

    # endregion

    # region ACL SET
    def test_acls_set_workspace_sp_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        sp_id = test_data.service_principal.id
        role = "Member"

        # Execute command
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {sp_id} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print,
            cli_executor,
            workspace.full_path,
            sp_id,
            role,
        )

        # Clean up
        _cleanup_acl(cli_executor, workspace.full_path, sp_id)

    def test_acls_set_workspace_user_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Execute command
        user = test_data.user.id
        userUPN = test_data.user.upn
        role = "Member"
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {user} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, workspace.full_path, user, role
        )

        # Clean up
        _cleanup_acl(cli_executor, workspace.full_path, userUPN)

    def test_acls_set_workspace_user_override_existing_role_success(
        self,
        workspace,
        mock_questionary_print,
        mock_questionary_confirm,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Execute command
        user = test_data.user.id
        userUPN = test_data.user.upn
        role = "Member"
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {user} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, workspace.full_path, user, role
        )

        # Override role
        new_role = "Viewer"
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {user} --role {new_role} --force"
        )
        mock_questionary_confirm.assert_not_called()  # force is enabled

        # Assert updated role
        _validate_role_updated(
            mock_questionary_print,
            cli_executor,
            workspace.full_path,
            user,
            new_role,
            role,
        )

        # Clean up
        _cleanup_acl(cli_executor, workspace.full_path, userUPN)

    def test_acls_set_workspace_without_force_success(
        self,
        workspace,
        mock_questionary_confirm,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Execute command
        sp_id = test_data.service_principal.id
        role = "member"
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {sp_id} --role {role}"
        )

        # Assert
        mock_questionary_confirm.assert_called()

    def test_acls_set_workspace_invalid_identity_failure(
        self, workspace, mock_fab_ui_print_error, cli_executor: CLIExecutor
    ):
        # Setup
        sp_id = str(uuid.uuid4())

        # Execute command
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {sp_id} --role member --force"
        )

        # Assert
        _validate_invalid_identity_failure(mock_fab_ui_print_error, sp_id)

    def test_acls_set_workspace_invalid_role_failure(
        self,
        workspace,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        user = test_data.user.id
        invalid_role = "invalid_role"

        # Execute command
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {user} --role {invalid_role} --force"
        )

        # Assert
        _validate_invalid_role_failure(
            mock_fab_ui_print_error, invalid_role, "workspace"
        )

    def test_acls_set_connection_without_force_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_confirm,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        user = test_data.user.id
        role = "User"

        # Execute command - add ACL
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {user} --role {role}"
        )

        # Assert
        mock_questionary_confirm.assert_called()

    def test_acls_set_connection_user_add_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        user = test_data.user.id
        role = "User"

        # Execute command - add ACL
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {user} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, connection.full_path, user, role
        )

        # Clean up
        _cleanup_acl(cli_executor, connection.full_path, user)

    def test_acls_set_connection_sp_add_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        spn_id = test_data.service_principal.id
        role = "User"

        # Execute command - add ACL
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {spn_id} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, connection.full_path, spn_id, role
        )

        # Clean up
        _cleanup_acl(cli_executor, connection.full_path, spn_id)

    def test_acls_set_connection_update_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        user = test_data.user.id
        initial_role = "Owner"
        updated_role = "User"

        # Execute command - add initial ACL
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {user} --role {initial_role} --force"
        )

        # Verify initial role
        _validate_role_added(
            mock_questionary_print,
            cli_executor,
            connection.full_path,
            user,
            initial_role,
        )

        # Execute command - update ACL
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {user} --role {updated_role} --force"
        )

        # Assert updated role
        _validate_role_updated(
            mock_questionary_print,
            cli_executor,
            connection.full_path,
            user,
            updated_role,
            initial_role,
        )

        # Clean up
        _cleanup_acl(cli_executor, connection.full_path, user)

    def test_acls_set_connection_invalid_role_failure(
        self,
        virtual_workspace_item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        user = test_data.user.id
        invalid_role = "invalid_role"

        # Execute command
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {user} --role {invalid_role} --force"
        )

        # Assert
        _validate_invalid_role_failure(
            mock_fab_ui_print_error, invalid_role, "connection"
        )

    def test_acls_set_connection_invalid_identity_failure(
        self,
        virtual_workspace_item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        invalid_identity = str(uuid.uuid4())
        role = "User"

        # Execute command
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {invalid_identity} --role {role} --force"
        )

        # Assert
        _validate_invalid_identity_failure(mock_fab_ui_print_error, invalid_identity)

    def test_acls_set_gateway_without_force_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_confirm,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        user = test_data.user.id
        role = "ConnectionCreator"

        # Execute command - add ACL
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {user} --role {role}"
        )

        # Assert
        mock_questionary_confirm.assert_called()

    def test_acls_set_gateway_user_add_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        user = test_data.user.id
        role = "ConnectionCreator"

        # Execute command - add ACL
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {user} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, gateway.full_path, user, role
        )

        # Clean up
        _cleanup_acl(cli_executor, gateway.full_path, user)

    def test_acls_set_gateway_sp_add_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        spn_id = test_data.service_principal.id
        role = "ConnectionCreator"

        # Execute command - add ACL
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {spn_id} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, gateway.full_path, spn_id, role
        )

        # Clean up
        _cleanup_acl(cli_executor, gateway.full_path, identity=spn_id)

    def test_acls_set_gateway_update_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        user = test_data.user.id
        initial_role = "ConnectionCreator"
        updated_role = "Admin"

        # Execute command - add initial ACL
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {user} --role {initial_role} --force"
        )

        # Verify initial role
        _validate_role_added(
            mock_questionary_print, cli_executor, gateway.full_path, user, initial_role
        )

        # Execute command - update ACL
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {user} --role {updated_role} --force"
        )

        # Assert updated role
        _validate_role_updated(
            mock_questionary_print,
            cli_executor,
            gateway.full_path,
            user,
            updated_role,
            initial_role,
        )

        # Clean up
        _cleanup_acl(cli_executor, gateway.full_path, user)

    def test_acls_set_gateway_invalid_role_failure(
        self,
        virtual_workspace_item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        user = test_data.user.id
        invalid_role = "invalid_role"

        # Execute command
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {user} --role {invalid_role} --force"
        )

        # Assert
        _validate_invalid_role_failure(mock_fab_ui_print_error, invalid_role, "gateway")

    def test_acls_set_gateway_invalid_identity_failure(
        self,
        virtual_workspace_item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        invalid_identity = str(uuid.uuid4())
        role = "Admin"

        # Execute command
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {invalid_identity} --role {role} --force"
        )

        # Assert
        _validate_invalid_identity_failure(mock_fab_ui_print_error, invalid_identity)

    # endregion

    # region ACL RM

    def test_acls_rm_workspace_sp_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        sp_id = test_data.service_principal.id
        role = "Member"
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {sp_id} --role {role} --force"
        )

        # Assert
        _validate_role_added(
            mock_questionary_print, cli_executor, workspace.full_path, sp_id, role
        )

        # Execute command
        cli_executor.exec_command(
            f"acl rm {workspace.full_path} --identity {sp_id} --force"
        )

        # Assert
        _validate_role_removed(
            mock_questionary_print, cli_executor, workspace.full_path, sp_id
        )

    def test_acls_rm_workspace_user_success(
        self,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        user = test_data.user.id
        userUPN = test_data.user.upn
        role = "member"
        cli_executor.exec_command(
            f"acl set {workspace.full_path} --identity {user} --role {role} --force"
        )

        # Execute command
        cli_executor.exec_command(
            f"acl rm {workspace.full_path} --identity {userUPN} --force"
        )

        # Assert
        _validate_role_removed(
            mock_questionary_print, cli_executor, workspace.full_path, user
        )

    def test_acls_rm_workspace_invalid_identity_failure(
        self, workspace, mock_fab_ui_print_error, cli_executor: CLIExecutor
    ):
        # Setup
        sp_id = str(uuid.uuid4())

        # Execute command
        cli_executor.exec_command(
            f"acl rm {workspace.full_path} --identity {sp_id} --force"
        )

        # Assert
        mock_fab_ui_print_error.assert_called()
        error_call = mock_fab_ui_print_error.mock_calls[0]
        assert isinstance(error_call.args[0], FabricCLIError)
        assert error_call.args[0].status_code == constant.ERROR_NOT_FOUND

    def test_acls_rm_connection_user_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        user = test_data.user.id
        role = "User"

        # Execute
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {user} --role {role} --force"
        )

        # Assert set success
        _validate_role_added(
            mock_questionary_print, cli_executor, connection.full_path, user, role
        )

        # Execute command - use user ID for connections since UPN is not available in ACL data
        cli_executor.exec_command(
            f"acl rm {connection.full_path} --identity {user} --force"
        )

        # Assert
        _validate_role_removed(
            mock_questionary_print, cli_executor, connection.full_path, user
        )

    def test_acls_rm_connection_sp_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        spn_id = test_data.service_principal.id
        role = "User"

        # Execute
        cli_executor.exec_command(
            f"acl set {connection.full_path} --identity {spn_id} --role {role} --force"
        )

        # Assert set success
        _validate_role_added(
            mock_questionary_print, cli_executor, connection.full_path, spn_id, role
        )

        # Execute command - use user ID for connections since UPN is not available in ACL data
        cli_executor.exec_command(
            f"acl rm {connection.full_path} --identity {spn_id} --force"
        )

        # Assert
        _validate_role_removed(
            mock_questionary_print, cli_executor, connection.full_path, spn_id
        )

    def test_acls_rm_connection_invalid_identity_failure(
        self,
        virtual_workspace_item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)
        invalid_identity = str(uuid.uuid4())

        # Execute command
        cli_executor.exec_command(
            f"acl rm {connection.full_path} --identity {invalid_identity} --force"
        )

        # Assert
        _validate_invalid_identity_failure(mock_fab_ui_print_error, invalid_identity)

    def test_acls_rm_gateway_user_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)

        user = test_data.user.id
        role = "ConnectionCreator"

        # Execute
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {user} --role {role} --force"
        )

        # Assert set success
        _validate_role_added(
            mock_questionary_print, cli_executor, gateway.full_path, user, role
        )

        # Execute command - use user ID for gateways since UPN is not available in ACL data
        cli_executor.exec_command(
            f"acl rm {gateway.full_path} --identity {user} --force"
        )

        # Assert
        _validate_role_removed(
            mock_questionary_print, cli_executor, gateway.full_path, user
        )

    def test_acls_rm_gateway_sp_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)

        spn_id = test_data.service_principal.id
        role = "ConnectionCreator"

        # Execute
        cli_executor.exec_command(
            f"acl set {gateway.full_path} --identity {spn_id} --role {role} --force"
        )

        # Assert set success
        _validate_role_added(
            mock_questionary_print, cli_executor, gateway.full_path, spn_id, role
        )

        # Execute command - use user ID for gateways since UPN is not available in ACL data
        cli_executor.exec_command(
            f"acl rm {gateway.full_path} --identity {spn_id} --force"
        )

        # Assert
        _validate_role_removed(
            mock_questionary_print, cli_executor, gateway.full_path, spn_id
        )

    def test_acls_rm_gateway_invalid_identity_failure(
        self,
        virtual_workspace_item_factory,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        invalid_identity = str(uuid.uuid4())

        # Execute command
        cli_executor.exec_command(
            f"acl rm {gateway.full_path} --identity {invalid_identity} --force"
        )

        # Assert
        _validate_invalid_identity_failure(mock_fab_ui_print_error, invalid_identity)

    # endregion


# region Helper Methods


def acls_ls_vws_assestion(mock_questionary_print, long=False):
    vws_args = ["principalId", "role", "principalType"]

    # Assert
    mock_questionary_print.assert_called()
    assert all(
        any(arg in call.args[0] for call in mock_questionary_print.mock_calls)
        for arg in vws_args
    )

    # if -l is passed, `id` should be in the output
    if long:
        assert any("id" in call.args[0] for call in mock_questionary_print.mock_calls)
    else:
        assert not any(
            "id" in call.args[0] for call in mock_questionary_print.mock_calls
        )


def _validate_invalid_identity_failure(mock_fab_ui_print_error, invalid_identity):
    """Validates that an invalid identity error was logged correctly."""
    mock_fab_ui_print_error.assert_called()
    error_call = mock_fab_ui_print_error.mock_calls[0]
    assert isinstance(error_call.args[0], FabricCLIError)
    assert error_call.args[0].status_code == constant.ERROR_NOT_FOUND
    assert f"'{invalid_identity}' identity not found" in error_call.args[0].message


def _validate_invalid_role_failure(
    mock_fab_ui_print_error, invalid_role, resource_type
):
    """Validates that an invalid role error was logged correctly."""
    mock_fab_ui_print_error.assert_called()
    error_call = mock_fab_ui_print_error.mock_calls[0]
    assert isinstance(error_call.args[0], FabricCLIError)
    assert error_call.args[0].status_code == constant.ERROR_INVALID_INPUT
    assert (
        f"Invalid role '{invalid_role}' for {resource_type.lower()}"
        in error_call.args[0].message
    )


def _validate_unsupported_command_failure(mock_fab_ui_print_error, command):
    """Validates that an unsupported command error was logged correctly."""
    mock_fab_ui_print_error.assert_called()
    error_call = mock_fab_ui_print_error.mock_calls[0]
    assert f"not supported for command 'acl {command}'" in error_call.args[0].message
    assert error_call.args[0].status_code == constant.ERROR_UNSUPPORTED_COMMAND


def _validate_role_added(
    mock_questionary_print, cli_executor, resource_path, user_id, role
):
    """Validates that a user and role appear in ACL output."""
    mock_questionary_print.reset_mock()
    cli_executor.exec_command(f"acl get {resource_path} --query .")
    call_args, _ = mock_questionary_print.call_args
    mock_questionary_print.assert_called()

    assert user_id in call_args[0]
    assert role in call_args[0]


def _validate_role_removed(
    mock_questionary_print, cli_executor, resource_path, user_id
):
    """Validates that a user does NOT appear in ACL output."""
    cli_executor.exec_command(f"acl get {resource_path} --query .")
    call_args, _ = mock_questionary_print.call_args
    mock_questionary_print.assert_called()

    assert user_id not in call_args[0]


def _validate_role_updated(
    mock_questionary_print,
    cli_executor,
    resource_path,
    user_id,
    expected_role,
    old_role=None,
):
    """Validates role update with JSON parsing for complex verification."""
    mock_questionary_print.reset_mock()
    cli_executor.exec_command(f"acl get {resource_path} --query .")
    mock_questionary_print.assert_called()
    call_args, _ = mock_questionary_print.call_args
    response = json.loads(call_args[0])

    # Find the user's ACL entry and verify the role
    user_acl = next(
        (entry for entry in response if entry["principal"]["id"] == user_id), None
    )
    assert user_acl is not None, f"User {user_id} not found in ACL data"
    assert (
        user_acl["role"] == expected_role
    ), f"Expected role {expected_role}, got {user_acl['role']}"

    # Verify the old role is no longer present for this user
    if old_role:
        assert (
            user_acl["role"] != old_role
        ), f"Old role {old_role} should not be present"


def _cleanup_acl(cli_executor, resource_path, identity, resource_type="workspace"):
    """Removes ACL for cleanup purposes, using appropriate identity format."""
    # For workspaces, we can use UPN if available, otherwise use ID
    # For VWS items (connections/gateways), we must use ID
    cli_executor.exec_command(f"acl rm {resource_path} --identity {identity} --force")


# endregion
