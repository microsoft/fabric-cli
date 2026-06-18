# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import Mock, patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils.fab_cmd_mkdir_utils import (
    find_mpe_connection,
    get_connection_config_from_params,
)


def test_fabric_data_pipelines_workspace_identity_no_params_success():
    """Test FabricDataPipelines with WorkspaceIdentity credential type when no parameters are required."""
    # Arrange
    payload = {
        "displayName": "test-connection",
        "connectivityType": "ShareableCloud"
    }
    
    con_type = "FabricDataPipelines"
    con_type_def = {
        "type": "FabricDataPipelines",
        "creationMethods": [
            {
                "name": "FabricDataPipelines.Actions",
                "parameters": []  # No parameters required for this creation method
            }
        ],
        "supportedCredentialTypes": ["WorkspaceIdentity"]
    }
    
    params = {
        "connectiondetails": {
            "type": "FabricDataPipelines",
            "creationmethod": "FabricDataPipelines.Actions"
            # No parameters provided since none are required
        },
        "credentialdetails": {
            "type": "WorkspaceIdentity"
            # No credential parameters provided since WorkspaceIdentity doesn't require any
        }
    }
    
    result = get_connection_config_from_params(payload, con_type, con_type_def, params)
    
    # Assert
    assert result["privacyLevel"] == "None"
    assert result["connectionDetails"]["type"] == "FabricDataPipelines"
    assert result["connectionDetails"]["creationMethod"] == "FabricDataPipelines.Actions"
    assert "parameters" not in result["connectionDetails"]
    assert result["credentialDetails"]["credentials"]["credentialType"] == "WorkspaceIdentity"
    assert len(result["credentialDetails"]["credentials"].keys()) == 1


def test_connection_with_required_params_missing_failure():
    """Test that connection creation fails when required parameters are missing."""
    # Arrange
    payload = {
        "displayName": "test-connection",
        "connectivityType": "ShareableCloud"
    }
    
    con_type = "SQL"
    con_type_def = {
        "type": "SQL",
        "creationMethods": [
            {
                "name": "SQL",
                "parameters": [
                    {"name": "server", "required": True, "dataType": "Text"},
                    {"name": "database", "required": True, "dataType": "Text"}
                ]
            }
        ],
        "supportedCredentialTypes": ["Basic"]
    }
    
    params = {
        "connectiondetails": {
            "type": "SQL",
            "creationmethod": "SQL"
            # No parameters provided, but they are required
        },
        "credentialdetails": {
            "type": "Basic",
            "username": "testuser",
            "password": "testpass"
        }
    }
    
    with pytest.raises(FabricCLIError) as exc_info:
        get_connection_config_from_params(payload, con_type, con_type_def, params)
    
    assert "Parameters are required for the connection creation method" in str(exc_info.value.message)
    assert "server, database" in str(exc_info.value.message)


def test_workspace_identity_with_unsupported_params_ignored_success():
    """Test that WorkspaceIdentity ignores unsupported credential parameters with warning."""
    # Arrange
    payload = {
        "displayName": "test-connection",
        "connectivityType": "ShareableCloud"
    }
    
    con_type = "FabricDataPipelines"
    con_type_def = {
        "type": "FabricDataPipelines",
        "creationMethods": [
            {
                "name": "FabricDataPipelines.Actions",
                "parameters": []
            }
        ],
        "supportedCredentialTypes": ["WorkspaceIdentity"]
    }
    
    params = {
        "connectiondetails": {
            "type": "FabricDataPipelines",
            "creationmethod": "FabricDataPipelines.Actions"
        },
        "credentialdetails": {
            "type": "WorkspaceIdentity",
            "username": "should_be_ignored",  # This should be ignored for WorkspaceIdentity
            "password": "should_be_ignored"   # This should be ignored for WorkspaceIdentity
        }
    }
    
    # Act
    with patch('fabric_cli.utils.fab_ui.print_warning') as mock_warning:
        result = get_connection_config_from_params(payload, con_type, con_type_def, params)
        
        mock_warning.assert_called_once()
        assert "username" in str(mock_warning.call_args)
        assert "password" in str(mock_warning.call_args)
    
    assert result["credentialDetails"]["credentials"]["credentialType"] == "WorkspaceIdentity"


class TestFindMpeConnection:
    """Test cases for find_mpe_connection function."""
    
    def test_find_mpe_connection_return_403_success(self):
        """Test that find_mpe_connection handles 403 forbidden error correctly when session.request returns 403."""
        # Arrange
        mock_managed_private_endpoint = Mock()
        mock_managed_private_endpoint.workspace.id = "test-workspace-id"
        mock_managed_private_endpoint.short_name = "test-mpe-name"
        
        target_resource_id = "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Sql/servers/test-server"
        
        # Mock the session.request response to return 403
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"error": {"code": "Forbidden", "message": "Access denied"}}'
        mock_response.headers = {}
        
        with patch('requests.Session.request') as mock_session_request, \
             patch('fabric_cli.client.fab_api_utils.get_api_version') as mock_get_api_version, \
             patch('fabric_cli.core.fab_auth.FabAuth') as mock_fab_auth_class, \
             patch('fabric_cli.core.fab_context.Context') as mock_fab_context_class:
            
            mock_session_request.return_value = mock_response
            mock_get_api_version.return_value = "2023-11-01"
            
            # Mock FabAuth().get_access_token(scope)
            mock_fab_auth_instance = Mock()
            mock_fab_auth_instance.get_access_token.return_value = "mock-access-token"
            mock_fab_auth_class.return_value = mock_fab_auth_instance
            
            # Mock FabContext().command
            mock_fab_context_instance = Mock()
            mock_fab_context_instance.command = "test-command"
            mock_fab_context_class.return_value = mock_fab_context_instance
            
            # Act & Assert
            with pytest.raises(FabricCLIError) as exc_info:
                find_mpe_connection(mock_managed_private_endpoint, target_resource_id)
            
            # Verify the exception details - this tests that do_request properly handles 403
            assert exc_info.value.status_code == fab_constant.ERROR_FORBIDDEN
            assert exc_info.value.message == ErrorMessages.Common.forbidden()
            
            # Verify session.request was called
            mock_session_request.assert_called_once()
            
            # Verify get_api_version was called with the target resource ID
            mock_get_api_version.assert_called_once_with(target_resource_id)
            
            # Verify authentication and context calls
            mock_fab_auth_class.assert_called_once()
            mock_fab_auth_instance.get_access_token.assert_called_once()
            mock_fab_context_class.assert_called_once()
            
            # Verify the call was made with correct method and URL contains expected parts
            call_args = mock_session_request.call_args
            assert call_args[1]['method'] == 'get' or call_args.kwargs['method'] == 'get'
            # The URL should contain the target resource ID and privateEndpointConnections
            called_url = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs['url']
            assert "privateEndpointConnections" in called_url
            assert "api-version=2023-11-01" in called_url


# SQLDatabase creation payload tests
class TestBuildSqlDatabaseCreationPayload:
    """Test cases for _build_sql_database_creation_payload function."""

    def test_build_sql_database_creation_payload_no_params_returns_none(self):
        """Test that no creationPayload is returned when no SQLDatabase params provided."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        result = _build_sql_database_creation_payload({})
        assert result is None

    def test_build_sql_database_creation_payload_unrelated_params_returns_none(self):
        """Test that no creationPayload is returned when unrelated params provided."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        result = _build_sql_database_creation_payload({"description": "test"})
        assert result is None

    def test_build_sql_database_creation_payload_mode_new_explicit_success(self):
        """Test SQLDatabase creation with explicit mode=New."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "new"}
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "New"

    def test_build_sql_database_creation_payload_backup_retention_days_success(self):
        """Test SQLDatabase creation with backupRetentionDays infers mode=New."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "21"}
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "New"
        assert result["backupRetentionDays"] == 21

    def test_build_sql_database_creation_payload_collation_success(self):
        """Test SQLDatabase creation with collation infers mode=New."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"collation": "SQL_Latin1_General_CP1_CI_AS"}
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "New"
        assert result["collation"] == "SQL_Latin1_General_CP1_CI_AS"

    def test_build_sql_database_creation_payload_both_properties_success(self):
        """Test SQLDatabase creation with both backupRetentionDays and collation."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {
            "mode": "New",
            "backupretentiondays": "7",
            "collation": "Latin1_General_100_CI_AS_KS_WS_SC_UTF8",
        }
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "New"
        assert result["backupRetentionDays"] == 7
        assert result["collation"] == "Latin1_General_100_CI_AS_KS_WS_SC_UTF8"

    def test_build_sql_database_creation_payload_mode_case_insensitive_success(self):
        """Test that mode parameter is case-insensitive."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "NEW", "backupretentiondays": "14"}
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "New"
        assert result["backupRetentionDays"] == 14

    def test_build_sql_database_creation_payload_backup_retention_min_success(self):
        """Test backupRetentionDays with minimum value (1)."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "1"}
        result = _build_sql_database_creation_payload(params)

        assert result["backupRetentionDays"] == 1

    def test_build_sql_database_creation_payload_backup_retention_max_success(self):
        """Test backupRetentionDays with maximum value (35)."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "35"}
        result = _build_sql_database_creation_payload(params)

        assert result["backupRetentionDays"] == 35

    def test_build_sql_database_creation_payload_backup_retention_out_of_range_failure(
        self,
    ):
        """Test that backupRetentionDays outside 1-35 range raises error."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "36"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "36" in str(exc_info.value.message)
        assert "1" in str(exc_info.value.message)
        assert "35" in str(exc_info.value.message)

    def test_build_sql_database_creation_payload_backup_retention_zero_failure(self):
        """Test that backupRetentionDays of 0 raises error."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "0"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT

    def test_build_sql_database_creation_payload_backup_retention_not_integer_failure(
        self,
    ):
        """Test that non-integer backupRetentionDays raises error."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "seven"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "seven" in str(exc_info.value.message)

    def test_build_sql_database_creation_payload_backup_retention_negative_failure(
        self,
    ):
        """Test that negative backupRetentionDays raises error."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"backupretentiondays": "-5"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT

    def test_build_sql_database_creation_payload_invalid_mode_failure(self):
        """Test that invalid creation mode raises error."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "InvalidMode"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "InvalidMode" in str(exc_info.value.message)
        assert "New" in str(exc_info.value.message)
        assert "Restore" in str(exc_info.value.message)

    def test_build_sql_database_creation_payload_restore_mode_no_properties_success(
        self,
    ):
        """Test Restore mode without backupRetentionDays or collation is valid."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "Restore"}
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "Restore"
        assert "backupRetentionDays" not in result
        assert "collation" not in result

    def test_build_sql_database_creation_payload_restore_mode_backup_retention_failure(
        self,
    ):
        """Test that backupRetentionDays is not allowed in Restore mode."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "Restore", "backupretentiondays": "21"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "backupRetentionDays" in str(exc_info.value.message)
        assert "Restore" in str(exc_info.value.message)

    def test_build_sql_database_creation_payload_restore_mode_collation_failure(self):
        """Test that collation is not allowed in Restore mode."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "Restore", "collation": "SQL_Latin1_General_CP1_CI_AS"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "collation" in str(exc_info.value.message)
        assert "Restore" in str(exc_info.value.message)

    def test_build_sql_database_creation_payload_restore_deleted_mode_success(self):
        """Test RestoreDeletedDatabase mode is valid."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "RestoreDeletedDatabase"}
        result = _build_sql_database_creation_payload(params)

        assert result is not None
        assert result["creationMode"] == "RestoreDeletedDatabase"

    def test_build_sql_database_creation_payload_restore_deleted_mode_properties_failure(
        self,
    ):
        """Test that properties are not allowed in RestoreDeletedDatabase mode."""
        from fabric_cli.utils.fab_cmd_mkdir_utils import _build_sql_database_creation_payload

        params = {"mode": "RestoreDeletedDatabase", "backupretentiondays": "7"}
        with pytest.raises(FabricCLIError) as exc_info:
            _build_sql_database_creation_payload(params)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "backupRetentionDays" in str(exc_info.value.message)
        assert "RestoreDeletedDatabase" in str(exc_info.value.message)
