# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json

from fabric_cli.commands.api import fab_api
from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_types import ItemType
from tests.test_commands.conftest import assert_fabric_cli_error
from tests.test_commands.data.static_test_data import StaticTestData


class TestAPI:
    def test_api_get_workspace_success(
        self, workspace, cli_executor, mock_questionary_print
    ):
        # Execute command
        cli_executor.exec_command(f"api workspaces")

        # # Assert
        mock_questionary_print.assert_called_once()
        assert '"status_code": 200,' in mock_questionary_print.mock_calls[0].args[0]
        assert workspace.display_name in mock_questionary_print.mock_calls[0].args[0]
        assert "headers:" not in mock_questionary_print.mock_calls[0].args[0]

    def test_api_get_workspace_with_query_failure(
        self, workspace, cli_executor, assert_fabric_cli_error
    ):
        # Execute command
        cli_executor.exec_command(f"api workspaces -q '.nonexistent'")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "Invalid jmespath query (https://jmespath.org)",
        )

    def test_api_add_workspace_role_assignment_show_headers_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_id = _get_workspace_id(workspace.name, mock_questionary_print)
        mock_questionary_print.reset_mock()

        input = json.dumps(
            {
                "principal": {"id": test_data.user.id, "type": "User"},
                "role": "Member",
            }
        )

        # Execute command
        cli_executor.exec_command(
            f"api workspaces/{workspace_id}/roleAssignments --method post --input '{input}' --show_headers"
        )

        # Assert
        mock_questionary_print.assert_called_once()
        assert '"status_code": 201,' in mock_questionary_print.mock_calls[0].args[0]
        assert test_data.user.id in mock_questionary_print.mock_calls[0].args[0]
        assert "Member" in mock_questionary_print.mock_calls[0].args[0]
        assert '"headers":' in mock_questionary_print.mock_calls[0].args[0]

    def test_api_add_workspace_role_assignment_file_input_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        tmp_path,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_id = _get_workspace_id(workspace.name, mock_questionary_print)
        mock_questionary_print.reset_mock()
        input = {
            "principal": {
                "id": test_data.service_principal.id,
                "type": "ServicePrincipal",
            },
            "role": "Viewer",
        }

        temp_file = tmp_path / "temp.json"
        with open(temp_file, "w") as file:
            json.dump(input, file)

        # Execute command
        cli_executor.exec_command(
            f"api workspaces/{workspace_id}/roleAssignments --method post --audience fabric -i '{str(temp_file)}'"
        )

        # Assert
        mock_questionary_print.assert_called_once()
        assert '"status_code": 201,' in mock_questionary_print.mock_calls[0].args[0]
        assert (
            test_data.service_principal.id
            in mock_questionary_print.mock_calls[0].args[0]
        )
        assert "Viewer" in mock_questionary_print.mock_calls[0].args[0]

    def test_api_file_input_invalid_json_failure(
        self,
        workspace,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        tmp_path,
    ):
        # Setup
        workspace_id = _get_workspace_id(workspace.name, mock_questionary_print)
        mock_questionary_print.reset_mock()
        invalid_json = "random,  string"

        temp_file = tmp_path / "temp.json"
        with open(temp_file, "w") as file:
            file.write(invalid_json)

        # Execute command
        cli_executor.exec_command(
            f"api workspaces/{workspace_id}/roleAssignments --method post -i '{str(temp_file)}'"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_JSON)

    def test_api_list_items_with_params_success(
        self, workspace, item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        workspace_id = _get_workspace_id(workspace.name, mock_questionary_print)
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"api workspaces/{workspace_id}/items")

        # # Assert
        mock_questionary_print.assert_called_once()
        assert '"status_code": 200,' in mock_questionary_print.mock_calls[0].args[0]
        assert lakehouse.display_name in mock_questionary_print.mock_calls[0].args[0]

    def test_api_upload_local_file_to_environment_success(
        self, workspace, item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        environment = item_factory(ItemType.ENVIRONMENT)
        workspace_id = _get_workspace_id(workspace.name, mock_questionary_print)
        environment_id = _get_item_id(workspace_id, environment, mock_questionary_print)

        lib_name = "environment.yml"
        file_path = f"tests/test_commands/data/sample_libs/{lib_name}"
        mock_questionary_print.reset_mock()

        # Execute command for yml file
        cli_executor.exec_command(
            f"api workspaces/{workspace_id}/environments/{environment_id}/staging/libraries --method post --audience fabric -i '{file_path}'"
        )

        # Assert
        mock_questionary_print.assert_called_once()
        assert '"status_code": 200,' in mock_questionary_print.mock_calls[0].args[0]


# region Helper Methods
def api(
    endpoint,
    method,
    params=None,
    input=None,
    audience="fabric",
    headers=None,
    show_headers=False,
):
    args = _build_api_args(
        endpoint, method, params, input, audience, headers, show_headers
    )
    fab_api.request_command.__wrapped__(
        args
    )  # __wrapped__ is used to access the original function without the exception handling decorator


def _build_api_args(endpoint, method, params, input, audience, headers, show_headers):
    return argparse.Namespace(
        command="api",
        command_path="api",
        endpoint=endpoint,
        method=method,
        params=params,
        input=[input] if input else None,
        audience=audience,
        headers=headers,
        show_headers=show_headers,
        query=None,
    )


def _get_workspace_id(workspace, mock_questionary_print) -> str:
    mock_questionary_print.reset_mock()

    api("workspaces", "get")

    # Extract the arguments passed to the mock
    workspace_id = None
    workspace_display_name = workspace.removesuffix(".Workspace")

    for call in mock_questionary_print.mock_calls:
        if workspace_display_name in call.args[0]:
            workspaces_list = json.loads(call.args[0])["text"]["value"]
            index = _find_first_index_containing(
                workspaces_list, workspace_display_name
            )
            workspace_id = workspaces_list[index]["id"]

    assert workspace_id is not None
    return workspace_id


def _get_item_id(workspace_id, item, mock_questionary_print) -> str:
    mock_questionary_print.reset_mock()
    
    api(f"workspaces/{workspace_id}/items", "get")

    # Extract the arguments passed to the mock
    item_id = None
    item_display_name = item.display_name

    for call in mock_questionary_print.mock_calls:
        if item_display_name in call.args[0]:
            items_list = json.loads(call.args[0])["text"]["value"]
            index = _find_first_index_containing(items_list, item_display_name)
            item_id = items_list[index]["id"]

    assert item_id is not None
    return item_id


def _find_first_index_containing(data, search_text):
    for index, obj in enumerate(data):
        if any(search_text in str(value) for value in obj.values()):
            return index
    raise ValueError(f"Could not find '{search_text}' in the provided data.")


# endregion
