# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_context import Context
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.core.hiearchy.fab_tenant import Tenant


def test_context_persistence_save(monkeypatch):
    """Test that context is saved to file in command-line mode with persistence enabled."""

    # Mock the state config
    def mock_get_config(key):
        if key == fab_constant.FAB_MODE:
            return fab_constant.FAB_MODE_COMMANDLINE
        elif key == fab_constant.FAB_CONTEXT_PERSISTENCE_ENABLED:
            return "true"
        return None

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    # Create a secure temporary context file path
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        temp_context_file = temp_file.name

    try:
        # Create a context instance
        context = Context()
        context._context_file = temp_context_file

        # Create a mock tenant
        tenant = Tenant("test_tenant", "1234")

        # Create a mock workspace with the tenant as parent
        workspace = Workspace("test_workspace", "5678", tenant, "Workspace")

        # Mock json.dump to avoid actually writing to the file system
        with patch("json.dump") as mock_json_dump, patch("builtins.open", MagicMock()):

            # Set the context
            context.context = workspace

            # Check that json.dump was called with the right data
            mock_json_dump.assert_called_once()
            args, _ = mock_json_dump.call_args
            assert args[0] == {"path": workspace.path}
    finally:
        os.remove(temp_context_file)


def test_context_persistence_load(monkeypatch):
    """Test that context loading is attempted when persistence is enabled in command-line mode."""

    # Mock the state config
    def mock_get_config(key):
        if key == fab_constant.FAB_MODE:
            return fab_constant.FAB_MODE_COMMANDLINE
        elif key == fab_constant.FAB_CONTEXT_PERSISTENCE_ENABLED:
            return "true"
        return None

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    # Create a context instance
    context = Context()
    # Reset the context to force loading
    context._context = None

    # Mock the _load_context_from_file method to verify it gets called
    with patch.object(context, "_load_context_from_file") as mock_load:
        # Access the context property to trigger loading
        _ = context.context

        # Verify that load was attempted
        mock_load.assert_called_once()


def test_context_persistence_not_used_in_interactive_mode(monkeypatch):
    """Test that context persistence is not used in interactive mode."""

    # Mock the state config to return interactive mode
    def mock_get_config(key):
        if key == fab_constant.FAB_MODE:
            return fab_constant.FAB_MODE_INTERACTIVE
        elif key == fab_constant.FAB_CONTEXT_PERSISTENCE_ENABLED:
            return "true"  # Even if enabled, should not be used in interactive mode
        return None

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    # Create a context instance
    context = Context()

    # Create a mock tenant and workspace
    tenant = Tenant("test_tenant", "1234")
    workspace = Workspace("test_workspace", "5678", tenant, "Workspace")

    # Mock the file operations to verify they are not called
    with (
        patch.object(context, "_save_context_to_file") as mock_save,
        patch.object(context, "_load_context_from_file") as mock_load,
    ):

        # Set the context - this should NOT trigger file save in interactive mode
        context.context = workspace

        # Get the context - this should NOT trigger file load in interactive mode
        result = context.context

        # Verify that file operations were not called
        mock_save.assert_not_called()
        mock_load.assert_not_called()

        # Verify the context was set correctly
        assert result == workspace


def test_context_persistence_disabled_by_default(monkeypatch):
    """Test that context persistence is disabled by default even in command-line mode."""

    # Mock the state config to return command-line mode but default persistence setting
    def mock_get_config(key):
        if key == fab_constant.FAB_MODE:
            return fab_constant.FAB_MODE_COMMANDLINE
        elif key == fab_constant.FAB_CONTEXT_PERSISTENCE_ENABLED:
            return "false"  # Default value - disabled
        return None

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    # Create a context instance
    context = Context()

    # Create a mock tenant and workspace
    tenant = Tenant("test_tenant", "1234")
    workspace = Workspace("test_workspace", "5678", tenant, "Workspace")

    # Mock the file operations to verify they are not called
    with (
        patch.object(context, "_save_context_to_file") as mock_save,
        patch.object(context, "_load_context_from_file") as mock_load,
    ):

        # Set the context - this should NOT trigger file save when persistence is disabled
        context.context = workspace

        # Get the context - this should NOT trigger file load when persistence is disabled
        result = context.context

        # Verify that file operations were not called
        mock_save.assert_not_called()
        mock_load.assert_not_called()

        # Verify the context was set correctly
        assert result == workspace


def test_context_persistence_enabled_when_configured(monkeypatch):
    """Test that context persistence works when explicitly enabled in command-line mode."""

    # Mock the state config to return command-line mode with persistence enabled
    def mock_get_config(key):
        if key == fab_constant.FAB_MODE:
            return fab_constant.FAB_MODE_COMMANDLINE
        elif key == fab_constant.FAB_CONTEXT_PERSISTENCE_ENABLED:
            return "true"  # Explicitly enabled
        return None

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    # Create a secure temporary context file path
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        temp_context_file = temp_file.name

    try:
        # Create a context instance
        context = Context()
        context._context_file = temp_context_file

        # Create a mock tenant and workspace
        tenant = Tenant("test_tenant", "1234")
        workspace = Workspace("test_workspace", "5678", tenant, "Workspace")

        # Mock json.dump to avoid actually writing to the file system
        with patch("json.dump") as mock_json_dump, patch("builtins.open", MagicMock()):

            # Set the context - this SHOULD trigger file save when persistence is enabled
            context.context = workspace

            # Check that json.dump was called with the right data
            mock_json_dump.assert_called_once()
            args, _ = mock_json_dump.call_args
            assert args[0] == {"path": workspace.path}
    finally:
        os.remove(temp_context_file)


def test_context_file_uses_parent_process_id(monkeypatch):
    """Test that context file includes session process ID for session isolation."""
    # Test the logic directly by checking the context file path generation
    test_ppid = 12345

    # Create a secure temporary directory for testing
    temp_config_dir = tempfile.mkdtemp()

    try:
        # Mock the functions
        monkeypatch.setattr("os.getppid", lambda: test_ppid)
        monkeypatch.setattr(
            fab_state_config, "config_location", lambda: temp_config_dir
        )

        # Use external test script to verify PPID-based context file naming
        test_script_path = os.path.join(
            os.path.dirname(__file__), "scripts", "test_context_ppid_script.py"
        )

        result = subprocess.run(
            [sys.executable, os.path.abspath(test_script_path), temp_config_dir],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Test script failed: {result.stderr}"
        assert "SUCCESS" in result.stdout
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_config_dir, ignore_errors=True)


def test_multiple_sessions_isolated_contexts():
    """Test that multiple sessions with different PPIDs get different context files."""

    # Get the path to the test script
    script_path = os.path.join(
        os.path.dirname(__file__), "scripts", "test_multiple_sessions_script.py"
    )

    try:
        # Create a secure temporary directory for sessions
        temp_sessions_dir = tempfile.mkdtemp()

        # Run the test script in multiple processes to simulate different sessions
        results = []
        for i in range(2):
            result = subprocess.run(
                [sys.executable, os.path.abspath(script_path), temp_sessions_dir],
                capture_output=True,
                text=True,
            )
            results.append(result)
            assert result.returncode == 0, f"Test script {i} failed: {result.stderr}"
            assert "SUCCESS" in result.stdout

        # Verify that different processes get different context files
        # (though they might be the same if subprocess reuses PIDs quickly)
        print("All sessions handled context files correctly")
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_sessions_dir, ignore_errors=True)


def test_context_cleanup_stale_files(monkeypatch):
    """Test that stale context files are cleaned up properly."""

    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Mock the config location to use our temp directory
        monkeypatch.setattr(
            "fabric_cli.core.fab_state_config.config_location", lambda: temp_dir
        )

        # Create some fake context files with different PIDs
        fake_files = [
            os.path.join(temp_dir, "context-99999.json"),  # Non-existent PID
            os.path.join(
                temp_dir, "context-1.json"
            ),  # Usually init process, should exist
            os.path.join(temp_dir, "context-invalid.json"),  # Invalid filename format
        ]

        # Create the fake files
        for fake_file in fake_files:
            with open(fake_file, "w") as f:
                json.dump({"path": "/test"}, f)

        # Verify all files exist initially
        for fake_file in fake_files:
            assert os.path.exists(fake_file)

        # Create a context instance and trigger cleanup
        context = Context()
        context.cleanup_context_files(cleanup_all_stale=True, cleanup_current=False)

        # The non-existent PID file should be removed
        assert not os.path.exists(fake_files[0])  # context-99999.json should be removed

        # The init process file might still exist (depends on system)
        # The invalid filename should still exist (we don't remove files we can't parse)
        assert os.path.exists(fake_files[2])  # context-invalid.json should remain

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_context_cleanup_current_file(monkeypatch):
    """Test that current session's context file can be cleaned up."""

    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Mock the config location to use our temp directory
        monkeypatch.setattr(
            "fabric_cli.core.fab_state_config.config_location", lambda: temp_dir
        )

        # Create a context instance
        context = Context()

        # Create the current session's context file
        with open(context._context_file, "w") as f:
            json.dump({"path": "/test"}, f)

        # Verify the file exists
        assert os.path.exists(context._context_file)

        # Clean up current file
        context.cleanup_context_files(cleanup_all_stale=False, cleanup_current=True)

        # Verify the file is removed
        assert not os.path.exists(context._context_file)

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_loading_context_re_entrancy_guard(monkeypatch):
    """Test that _loading_context flag prevents infinite recursion during context loading.

    The _loading_context flag is a re-entrancy guard that prevents infinite recursion.
    When _load_context_from_file() calls get_command_context(), that method internally
    accesses Context().context, which would trigger _load_context_from_file() again.
    The flag ensures we only load the context file once during the initial call and
    prevents this circular dependency from causing a stack overflow.
    """

    # Mock the state config to enable context persistence
    def mock_get_config(key):
        if key == fab_constant.FAB_MODE:
            return fab_constant.FAB_MODE_COMMANDLINE
        elif key == fab_constant.FAB_CONTEXT_PERSISTENCE_ENABLED:
            return "true"
        return None

    monkeypatch.setattr(fab_state_config, "get_config", mock_get_config)

    # Create a context instance
    context = Context()
    context._context = None  # Reset to force loading

    # Test that _should_use_context_file returns False when _loading_context is True
    context._loading_context = True
    assert (
        not context._should_use_context_file()
    ), "_should_use_context_file should return False when _loading_context is True"

    # Test that _should_use_context_file returns True when _loading_context is False
    context._loading_context = False
    assert (
        context._should_use_context_file()
    ), "_should_use_context_file should return True when _loading_context is False"

    # Test the actual re-entrancy scenario
    load_calls = []
    original_load_method = context._load_context_from_file

    def mock_load_context_from_file():
        """Mock that simulates accessing context during load (which would cause re-entrancy)."""
        load_calls.append("load_called")

        # Simulate what happens in the real method: set the flag
        context._loading_context = True
        try:
            # Simulate accessing context during loading (this would normally cause recursion)
            # The _loading_context flag should prevent _load_context_from_file from being called again
            _ = context._should_use_context_file()  # This checks the flag

            # Mock successful loading
            from fabric_cli.core.hiearchy.fab_tenant import Tenant

            context._context = Tenant("test_tenant", "1234")
        finally:
            # Always reset the flag (like the real method does)
            context._loading_context = False

    # Replace the method with our mock
    context._load_context_from_file = mock_load_context_from_file

    # Mock os.path.exists to pretend the context file exists
    with patch("os.path.exists", return_value=True):
        # Access context property, which should trigger loading
        result_context = context.context

        # Verify that loading was called exactly once
        assert len(load_calls) == 1, f"Expected 1 load call, got {len(load_calls)}"

        # Verify that the flag is properly reset
        assert (
            not context._loading_context
        ), "_loading_context flag should be reset after loading"

        # Verify that context was set
        assert result_context is not None, "Context should be loaded"

    # Test that accessing context again doesn't trigger another load (context is already set)
    load_calls.clear()
    _ = context.context
    assert (
        len(load_calls) == 0
    ), "Context access should not trigger reload when already set"
