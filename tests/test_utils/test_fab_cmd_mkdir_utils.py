# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
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
        "description": "Created by fab",
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
        "description": "Created by fab",
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
        "description": "Created by fab",
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
            