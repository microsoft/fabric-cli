import json
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from fabric_cli.commands.fs.mv.fab_fs_mv_folder import _change_folder_parent
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_workspace import Workspace


@pytest.fixture
def mock_workspace():
    workspace = Mock(spec=Workspace)
    workspace.id = "workspace-123"
    workspace.name = "TestWorkspace"
    return workspace


@pytest.fixture
def mock_parent_folder(mock_workspace):
    parent_folder = Mock(spec=Folder)
    parent_folder.id = "parent-folder-456"
    parent_folder.name = "ParentFolder"
    parent_folder.workspace = mock_workspace
    return parent_folder


@pytest.fixture
def mock_new_parent_folder(mock_workspace):
    new_parent = Mock(spec=Folder)
    new_parent.id = "new-parent-789"
    new_parent.name = "NewParentFolder"
    new_parent.workspace = mock_workspace
    return new_parent


@pytest.fixture
def mock_folder(mock_workspace, mock_parent_folder):
    folder = Mock(spec=Folder)
    folder.id = "folder-999"
    folder.name = "TestFolder"
    folder.workspace = mock_workspace
    folder.parent = mock_parent_folder
    folder._parent = mock_parent_folder
    return folder


@pytest.fixture
def mock_api_response_success():
    response = Mock()
    response.status_code = 200
    return response


@pytest.fixture
def mock_api_response_failure():
    response = Mock()
    response.status_code = 400
    return response


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent__folder_target_success(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
    mock_api_response_success,
):
    mock_move_folder_api.return_value = mock_api_response_success

    _change_folder_parent(mock_folder, mock_new_parent_folder)

    mock_move_folder_api.assert_called_once()
    args, payload_json = mock_move_folder_api.call_args

    args_namespace = args[0]
    assert isinstance(args_namespace, Namespace)
    assert args_namespace.ws_id == mock_folder.workspace.id
    assert args_namespace.folder_id == mock_folder.id

    payload_json_str = mock_move_folder_api.call_args[0][1]
    payload = json.loads(payload_json_str)
    assert payload["targetFolderId"] == mock_new_parent_folder.id

    assert mock_folder._parent == mock_new_parent_folder

    mock_upsert_folder_cache.assert_called_once_with(mock_folder)

    mock_print_output.assert_called_once()
    call_args, call_kwargs = mock_print_output.call_args
    assert "message" in call_kwargs
    message = call_kwargs["message"]
    assert "Move Completed" in message
    assert mock_folder.name in message
    assert mock_new_parent_folder.name in message


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_workspace_target_success(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_workspace,
    mock_api_response_success,
):
    mock_move_folder_api.return_value = mock_api_response_success

    _change_folder_parent(mock_folder, mock_workspace)

    mock_move_folder_api.assert_called_once()
    args, payload_json = mock_move_folder_api.call_args

    args_namespace = args[0]
    assert isinstance(args_namespace, Namespace)
    assert args_namespace.ws_id == mock_folder.workspace.id
    assert args_namespace.folder_id == mock_folder.id

    payload_json_str = mock_move_folder_api.call_args[0][1]
    payload = json.loads(payload_json_str)
    assert payload == {}

    assert mock_folder._parent == mock_workspace

    mock_upsert_folder_cache.assert_called_once_with(mock_folder)

    mock_print_output.assert_called_once()


@patch("fabric_cli.utils.fab_ui.print_warning")
def test_change_folder_parent_already_in_target_parent_success(
    mock_print_warning,
    mock_folder,
    mock_parent_folder,
):
    mock_folder.parent = mock_parent_folder

    _change_folder_parent(mock_folder, mock_parent_folder)

    mock_print_warning.assert_called_once()
    warning_message = mock_print_warning.call_args[0][0]
    assert "already in the target parent" in warning_message
    assert mock_folder.name in warning_message


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_api_failure(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
    mock_api_response_failure,
):
    mock_move_folder_api.return_value = mock_api_response_failure

    _change_folder_parent(mock_folder, mock_new_parent_folder)

    mock_move_folder_api.assert_called_once()

    assert mock_folder._parent == mock_folder.parent

    mock_upsert_folder_cache.assert_not_called()

    mock_print_output.assert_not_called()


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_api_call_structure(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
    mock_api_response_success,
):
    mock_move_folder_api.return_value = mock_api_response_success

    _change_folder_parent(mock_folder, mock_new_parent_folder)

    mock_move_folder_api.assert_called_once()
    args, payload_json = mock_move_folder_api.call_args

    args_namespace = args[0]
    assert hasattr(args_namespace, "ws_id")
    assert hasattr(args_namespace, "folder_id")
    assert args_namespace.ws_id == mock_folder.workspace.id
    assert args_namespace.folder_id == mock_folder.id

    payload_json_str = mock_move_folder_api.call_args[0][1]
    assert isinstance(payload_json_str, str)
    payload = json.loads(payload_json_str)
    assert isinstance(payload, dict)


@patch("fabric_cli.utils.fab_ui.print_warning")
def test_change_folder_parent_same_instance_check(
    mock_print_warning,
    mock_folder,
):
    current_parent = mock_folder.parent

    _change_folder_parent(mock_folder, current_parent)

    mock_print_warning.assert_called_once()


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_memory_update_order(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
    mock_api_response_success,
):
    mock_move_folder_api.return_value = mock_api_response_success
    original_parent = mock_folder.parent

    _change_folder_parent(mock_folder, mock_new_parent_folder)

    assert mock_folder._parent == mock_new_parent_folder
    assert mock_folder._parent != original_parent

    mock_upsert_folder_cache.assert_called_once_with(mock_folder)


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_different_status_codes(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
):
    test_cases = [
        (200, True),
        (201, False),
        (400, False),
        (404, False),
        (500, False),
    ]

    for status_code, should_update in test_cases:
        mock_move_folder_api.reset_mock()
        mock_upsert_folder_cache.reset_mock()
        mock_print_output.reset_mock()

        mock_response = Mock()
        mock_response.status_code = status_code
        mock_move_folder_api.return_value = mock_response
        original_parent = mock_folder.parent

        _change_folder_parent(mock_folder, mock_new_parent_folder)

        if should_update:
            mock_upsert_folder_cache.assert_called_once()
            mock_print_output.assert_called_once()
            assert mock_folder._parent == mock_new_parent_folder
        else:
            mock_upsert_folder_cache.assert_not_called()
            mock_print_output.assert_not_called()
            mock_folder._parent = original_parent


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_api_exception_handling(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
):
    mock_move_folder_api.side_effect = Exception("API Error")
    original_parent = mock_folder._parent

    with pytest.raises(Exception, match="API Error"):
        _change_folder_parent(mock_folder, mock_new_parent_folder)

    assert mock_folder._parent == original_parent

    mock_upsert_folder_cache.assert_not_called()

    mock_print_output.assert_not_called()


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_json_serialization(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
    mock_api_response_success,
):
    mock_move_folder_api.return_value = mock_api_response_success

    _change_folder_parent(mock_folder, mock_new_parent_folder)

    payload_json_str = mock_move_folder_api.call_args[0][1]

    payload = json.loads(payload_json_str)

    assert isinstance(payload, dict)
    assert "targetFolderId" in payload
    assert payload["targetFolderId"] == mock_new_parent_folder.id


@patch("fabric_cli.utils.fab_ui.print_warning")
def test_change_folder_parent_none_comparison(
    mock_print_warning,
    mock_folder,
):
    mock_folder.parent = None

    _change_folder_parent(mock_folder, None)

    mock_print_warning.assert_called_once()
    warning_message = mock_print_warning.call_args[0][0]
    assert "already in the target parent" in warning_message


@patch("fabric_cli.utils.fab_ui.print_output_format")
@patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache")
@patch("fabric_cli.client.fab_api_folders.move_folder")
def test_change_folder_parent_namespace_attributes(
    mock_move_folder_api,
    mock_upsert_folder_cache,
    mock_print_output,
    mock_folder,
    mock_new_parent_folder,
    mock_api_response_success,
):
    mock_move_folder_api.return_value = mock_api_response_success

    _change_folder_parent(mock_folder, mock_new_parent_folder)

    args_namespace = mock_move_folder_api.call_args[0][0]

    assert hasattr(args_namespace, "ws_id")
    assert hasattr(args_namespace, "folder_id")

    assert args_namespace.ws_id == mock_folder.workspace.id
    assert args_namespace.folder_id == mock_folder.id

    assert isinstance(args_namespace, Namespace)
