# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Workspace
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils.fab_cmd_mkdir_utils import (
    add_type_specific_payload,
    find_mpe_connection,
    get_connection_config_from_params,
    get_params_per_item_type,
)
from fabric_cli.utils.fab_util import is_valid_guid, is_valid_iso8601_timestamp


def test_fabric_data_pipelines_workspace_identity_no_params_success():
    """Test FabricDataPipelines with WorkspaceIdentity credential type when no parameters are required."""
    # Arrange
    payload = {"displayName": "test-connection", "connectivityType": "ShareableCloud"}

    con_type = "FabricDataPipelines"
    con_type_def = {
        "type": "FabricDataPipelines",
        "creationMethods": [
            {
                "name": "FabricDataPipelines.Actions",
                "parameters": [],  # No parameters required for this creation method
            }
        ],
        "supportedCredentialTypes": ["WorkspaceIdentity"],
    }

    params = {
        "connectiondetails": {
            "type": "FabricDataPipelines",
            "creationmethod": "FabricDataPipelines.Actions",
            # No parameters provided since none are required
        },
        "credentialdetails": {
            "type": "WorkspaceIdentity"
            # No credential parameters provided since WorkspaceIdentity doesn't require any
        },
    }

    result = get_connection_config_from_params(payload, con_type, con_type_def, params)

    # Assert
    assert result["privacyLevel"] == "None"
    assert result["connectionDetails"]["type"] == "FabricDataPipelines"
    assert (
        result["connectionDetails"]["creationMethod"] == "FabricDataPipelines.Actions"
    )
    assert "parameters" not in result["connectionDetails"]
    assert (
        result["credentialDetails"]["credentials"]["credentialType"]
        == "WorkspaceIdentity"
    )
    assert len(result["credentialDetails"]["credentials"].keys()) == 1


def test_connection_with_required_params_missing_failure():
    """Test that connection creation fails when required parameters are missing."""
    # Arrange
    payload = {"displayName": "test-connection", "connectivityType": "ShareableCloud"}

    con_type = "SQL"
    con_type_def = {
        "type": "SQL",
        "creationMethods": [
            {
                "name": "SQL",
                "parameters": [
                    {"name": "server", "required": True, "dataType": "Text"},
                    {"name": "database", "required": True, "dataType": "Text"},
                ],
            }
        ],
        "supportedCredentialTypes": ["Basic"],
    }

    params = {
        "connectiondetails": {
            "type": "SQL",
            "creationmethod": "SQL",
            # No parameters provided, but they are required
        },
        "credentialdetails": {
            "type": "Basic",
            "username": "testuser",
            "password": "testpass",
        },
    }

    with pytest.raises(FabricCLIError) as exc_info:
        get_connection_config_from_params(payload, con_type, con_type_def, params)

    assert "Parameters are required for the connection creation method" in str(
        exc_info.value.message
    )
    assert "server, database" in str(exc_info.value.message)


def test_workspace_identity_with_unsupported_params_ignored_success():
    """Test that WorkspaceIdentity ignores unsupported credential parameters with warning."""
    # Arrange
    payload = {"displayName": "test-connection", "connectivityType": "ShareableCloud"}

    con_type = "FabricDataPipelines"
    con_type_def = {
        "type": "FabricDataPipelines",
        "creationMethods": [{"name": "FabricDataPipelines.Actions", "parameters": []}],
        "supportedCredentialTypes": ["WorkspaceIdentity"],
    }

    params = {
        "connectiondetails": {
            "type": "FabricDataPipelines",
            "creationmethod": "FabricDataPipelines.Actions",
        },
        "credentialdetails": {
            "type": "WorkspaceIdentity",
            "username": "should_be_ignored",  # This should be ignored for WorkspaceIdentity
            "password": "should_be_ignored",  # This should be ignored for WorkspaceIdentity
        },
    }

    # Act
    with patch("fabric_cli.utils.fab_ui.print_warning") as mock_warning:
        result = get_connection_config_from_params(
            payload, con_type, con_type_def, params
        )

        mock_warning.assert_called_once()
        assert "username" in str(mock_warning.call_args)
        assert "password" in str(mock_warning.call_args)

    assert (
        result["credentialDetails"]["credentials"]["credentialType"]
        == "WorkspaceIdentity"
    )


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
        mock_response.text = (
            '{"error": {"code": "Forbidden", "message": "Access denied"}}'
        )
        mock_response.headers = {}

        with (
            patch("requests.Session.request") as mock_session_request,
            patch(
                "fabric_cli.client.fab_api_utils.get_api_version"
            ) as mock_get_api_version,
            patch("fabric_cli.core.fab_auth.FabAuth") as mock_fab_auth_class,
            patch("fabric_cli.core.fab_context.Context") as mock_fab_context_class,
        ):

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
            assert (
                call_args[1]["method"] == "get" or call_args.kwargs["method"] == "get"
            )
            # The URL should contain the target resource ID and privateEndpointConnections
            called_url = (
                call_args.args[1]
                if len(call_args.args) > 1
                else call_args.kwargs["url"]
            )
            assert "privateEndpointConnections" in called_url
            assert "api-version=2023-11-01" in called_url


class TestIsValidGuid:
    """Test cases for is_valid_guid function."""

    def test_valid_guid_lowercase(self):
        """Test valid GUID with lowercase letters."""
        assert is_valid_guid("12345678-1234-1234-1234-123456789abc")

    def test_valid_guid_uppercase(self):
        """Test valid GUID with uppercase letters."""
        assert is_valid_guid("12345678-1234-1234-1234-123456789ABC")

    def test_valid_guid_mixed_case(self):
        """Test valid GUID with mixed case letters."""
        assert is_valid_guid("12345678-abcd-ABCD-1234-123456789AbC")

    def test_invalid_guid_wrong_format(self):
        """Test invalid GUID with wrong format."""
        assert not is_valid_guid("not-a-guid")

    def test_invalid_guid_missing_hyphens(self):
        """Test invalid GUID with missing hyphens."""
        assert not is_valid_guid("1234567812341234123412345678abc")

    def test_invalid_guid_extra_characters(self):
        """Test invalid GUID with extra characters."""
        assert not is_valid_guid("12345678-1234-1234-1234-123456789abcd")

    def test_invalid_guid_empty_string(self):
        """Test empty string is not a valid GUID."""
        assert not is_valid_guid("")


class TestIsValidIso8601Timestamp:
    """Test cases for is_valid_iso8601_timestamp function."""

    def test_valid_timestamp_utc_z_suffix(self):
        """Test valid ISO 8601 timestamp with Z suffix."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00Z")

    def test_valid_timestamp_with_milliseconds(self):
        """Test valid ISO 8601 timestamp with milliseconds."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00.123Z")

    def test_valid_timestamp_with_microseconds(self):
        """Test valid ISO 8601 timestamp with microseconds."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00.123456Z")

    def test_valid_timestamp_positive_offset(self):
        """Test valid ISO 8601 timestamp with positive timezone offset."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00+05:30")

    def test_valid_timestamp_negative_offset(self):
        """Test valid ISO 8601 timestamp with negative timezone offset."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00-08:00")

    def test_valid_timestamp_zero_offset(self):
        """Test valid ISO 8601 timestamp with zero offset."""
        assert is_valid_iso8601_timestamp("2024-01-15T10:30:00+00:00")

    def test_invalid_timestamp_no_timezone(self):
        """Test timestamp without timezone is invalid."""
        assert not is_valid_iso8601_timestamp("2024-01-15T10:30:00")

    def test_invalid_timestamp_date_only(self):
        """Test date-only string is invalid."""
        assert not is_valid_iso8601_timestamp("2024-01-15")

    def test_invalid_timestamp_wrong_format(self):
        """Test invalid timestamp format."""
        assert not is_valid_iso8601_timestamp("not-a-timestamp")

    def test_invalid_timestamp_empty_string(self):
        """Test empty string is not a valid timestamp."""
        assert not is_valid_iso8601_timestamp("")


class TestSQLDatabaseRestore:
    """Test cases for SQLDatabase point-in-time restore functionality."""

    @pytest.fixture
    def mock_sql_database_item(self):
        """Create a mock SQL database item."""
        mock_workspace = Mock(spec=Workspace)
        mock_workspace.id = "workspace-id-123"

        item = Mock(spec=Item)
        item.item_type = ItemType.SQL_DATABASE
        item.workspace = mock_workspace
        item.short_name = "test-db"
        return item

    @pytest.fixture
    def mock_args(self):
        """Create mock args namespace."""
        args = Namespace()
        args.params = {}
        return args

    def test_restore_mode_valid_params_success(self, mock_sql_database_item, mock_args):
        """Test SQLDatabase restore with valid parameters."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00Z",
            "itemid": "12345678-1234-1234-1234-123456789abc",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}
        result = add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert "creationPayload" in result
        assert result["creationPayload"]["creationMode"] == "Restore"
        assert result["creationPayload"]["restorePointInTime"] == "2024-01-15T10:30:00Z"
        assert (
            result["creationPayload"]["sourceDatabaseReference"]["referenceType"]
            == "ById"
        )
        assert (
            result["creationPayload"]["sourceDatabaseReference"]["itemId"]
            == "12345678-1234-1234-1234-123456789abc"
        )
        assert (
            result["creationPayload"]["sourceDatabaseReference"]["workspaceId"]
            == "87654321-4321-4321-4321-cba987654321"
        )

    def test_restore_mode_with_offset_timestamp_success(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore with timezone offset timestamp."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00+05:30",
            "itemid": "12345678-1234-1234-1234-123456789abc",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}
        result = add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert "creationPayload" in result
        assert (
            result["creationPayload"]["restorePointInTime"]
            == "2024-01-15T10:30:00+05:30"
        )

    def test_restore_mode_missing_restore_point_in_time_failure(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore fails when restorePointInTime is missing."""
        mock_args.params = {
            "mode": "restore",
            "itemid": "12345678-1234-1234-1234-123456789abc",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "restorePointInTime" in exc_info.value.message

    def test_restore_mode_missing_item_id_failure(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore fails when itemId is missing."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00Z",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "itemId" in exc_info.value.message

    def test_restore_mode_missing_workspace_id_failure(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore fails when workspaceId is missing."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00Z",
            "itemid": "12345678-1234-1234-1234-123456789abc",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "workspaceId" in exc_info.value.message

    def test_restore_mode_invalid_timestamp_format_failure(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore fails with invalid timestamp format."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00",  # Missing timezone
            "itemid": "12345678-1234-1234-1234-123456789abc",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "ISO 8601" in exc_info.value.message

    def test_restore_mode_invalid_item_id_guid_failure(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore fails with invalid itemId GUID."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00Z",
            "itemid": "not-a-valid-guid",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_GUID
        assert "itemId" in exc_info.value.message

    def test_restore_mode_invalid_workspace_id_guid_failure(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore fails with invalid workspaceId GUID."""
        mock_args.params = {
            "mode": "restore",
            "restorepointintime": "2024-01-15T10:30:00Z",
            "itemid": "12345678-1234-1234-1234-123456789abc",
            "workspaceid": "not-a-valid-guid",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_GUID
        assert "workspaceId" in exc_info.value.message

    def test_invalid_mode_failure(self, mock_sql_database_item, mock_args):
        """Test SQLDatabase creation fails with invalid mode."""
        mock_args.params = {
            "mode": "invalid",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}

        with pytest.raises(FabricCLIError) as exc_info:
            add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert exc_info.value.status_code == fab_constant.ERROR_INVALID_INPUT
        assert "mode" in exc_info.value.message.lower()

    def test_standard_creation_no_mode_success(self, mock_sql_database_item, mock_args):
        """Test standard SQLDatabase creation without mode parameter."""
        mock_args.params = {}

        payload = {"displayName": "test-db", "type": "SQLDatabase"}
        result = add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        # Standard creation should not add creationPayload
        assert "creationPayload" not in result

    def test_restore_mode_case_insensitive_success(
        self, mock_sql_database_item, mock_args
    ):
        """Test SQLDatabase restore mode is case-insensitive."""
        mock_args.params = {
            "mode": "RESTORE",
            "restorepointintime": "2024-01-15T10:30:00Z",
            "itemid": "12345678-1234-1234-1234-123456789abc",
            "workspaceid": "87654321-4321-4321-4321-cba987654321",
        }

        payload = {"displayName": "test-db", "type": "SQLDatabase"}
        result = add_type_specific_payload(mock_sql_database_item, mock_args, payload)

        assert "creationPayload" in result


class TestGetParamsPerItemTypeSQLDatabase:
    """Test cases for get_params_per_item_type for SQLDatabase."""

    @pytest.fixture
    def mock_sql_database_item(self):
        """Create a mock SQL database item."""
        item = Mock(spec=Item)
        item.item_type = ItemType.SQL_DATABASE
        return item

    def test_sql_database_params(self, mock_sql_database_item):
        """Test that SQL Database returns correct optional parameters."""
        required, optional = get_params_per_item_type(mock_sql_database_item)

        assert required == []
        assert len(optional) == 4
        assert any("mode" in param for param in optional)
        assert any("restorePointInTime" in param for param in optional)
        assert any("itemId" in param for param in optional)
        assert any("workspaceId" in param for param in optional)
