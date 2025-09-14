# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils.fab_storage import (
    get_export_path,
    get_import_path,
    write_to_storage,
)


def test_write_to_storage_local_success(mock_fab_set_state_config):
    # Setup
    mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "text")

    """Test basic local file storage operations"""
    export_path = {"type": "local", "path": "item_folder/test"}
    data = {"test": "test"}
    args = argparse.Namespace(command="test-storage")
    write_to_storage(args, export_path, data, export=False)
    assert os.path.exists("item_folder/test.json")
    os.remove("item_folder/test.json")

    export_path = {"type": "local", "path": "item_folder/test.json"}
    data = {"test": "test"}
    write_to_storage(args, export_path, data, export=True)
    assert os.path.exists("item_folder/test.json")
    os.remove("item_folder/test.json")

    export_path = {"type": "local", "path": "item_folder/test.txt"}
    data = "test"
    write_to_storage(args, export_path, data, export=False)
    assert os.path.exists("item_folder/test.txt")
    os.remove("item_folder/test.txt")

    data = 22
    write_to_storage(args, export_path, data, export=False)
    assert os.path.exists("item_folder/test.txt")
    os.remove("item_folder/test.txt")


def test_write_to_storage_local_with_nested_path(mock_fab_set_state_config):
    """Test writing to storage with nested directory paths"""
    # Setup
    mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "text")

    export_path = {"type": "local", "path": "item_folder/nested/dir/test.json"}
    data = {"test": "nested"}
    args = argparse.Namespace(command="test-storage")
    write_to_storage(args, export_path, data, export=True)

    # Verify nested directories were created
    assert os.path.exists("item_folder/nested/dir/test.json")
    os.remove("item_folder/nested/dir/test.json")
    os.removedirs("item_folder/nested/dir")


def test_get_export_path_success():
    """Test get_export_path with valid local path"""
    # Create a test file
    test_file = "test_export.txt"
    Path(test_file).touch()

    # Test with local path
    result = get_export_path(test_file)
    assert result == {"type": "local", "path": test_file}

    # Clean up
    os.remove(test_file)


@patch('os.path.exists')
@patch('os.path.expanduser')
@patch('fabric_cli.utils.fab_storage.handle_context.get_command_context')
def test_get_export_path_with_home_dir_success(mock_get_command_context, mock_expanduser, mock_exists):
    """Test get_export_path with ~/path"""
    # Setup mocks
    mock_expanduser.return_value = "/home/user/test.txt"
    mock_exists.return_value = True
    # Mock the get_command_context to raise an exception
    mock_get_command_context.side_effect = Exception("Not a valid Fabric context")
    
    # Test with path containing ~/
    result = get_export_path("~/test.txt")
    
    # Verify
    mock_expanduser.assert_called_once_with("~/test.txt")
    assert result == {"type": "local", "path": "/home/user/test.txt"}

def test_get_export_path_failure():
    """Test get_export_path with non-existent path"""
    with pytest.raises(FabricCLIError) as exc:
        get_export_path("nonexistent.txt")
    assert "No such file or directory" in str(exc.value)


@patch('os.path.exists')
@patch('os.path.expanduser')
@patch('fabric_cli.utils.fab_storage.handle_context.get_command_context')
def test_get_import_path_with_home_dir_success(mock_get_command_context, mock_expanduser, mock_exists):
    """Test get_import_path with ~/path"""
    # Setup mocks
    mock_expanduser.return_value = "/home/user/test.txt"
    mock_exists.return_value = True
    # Mock the get_command_context to raise an exception
    mock_get_command_context.side_effect = Exception("Not a valid Fabric context")
    
    # Test with path containing ~/
    result = get_import_path("~/test.txt")
    
    # Verify
    mock_expanduser.assert_called_once_with("~/test.txt")
    assert result == {"type": "local", "path": "/home/user/test.txt"}

def test_get_import_path_success():
    """Test get_import_path with valid local path"""
    # Create a test file
    test_file = "test_import.txt"
    Path(test_file).touch()

    # Test with local path
    result = get_import_path(test_file)
    assert result == {"type": "local", "path": test_file}

    # Clean up
    os.remove(test_file)


def test_get_import_path_failure():
    """Test get_import_path with non-existent path"""
    with pytest.raises(FabricCLIError) as exc:
        get_import_path("nonexistent.txt")
    assert "No such file or directory" in str(exc.value)
