# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for lazy loading utilities and startup performance."""

import importlib
import sys
import time

import pytest


class TestLazyLoad:
    """Test suite for lazy loading utilities."""

    def test_lazy_command__deferred_import(self):
        """Test that lazy_command defers the module import until invocation."""
        from fabric_cli.utils.fab_lazy_load import lazy_command

        mod_path = "fabric_cli.commands.auth.fab_auth"

        # Ensure clean state
        saved_mod = sys.modules.pop(mod_path, None)

        try:
            wrapper = lazy_command(mod_path, "init")

            # The wrapper should be callable
            assert callable(wrapper)

            # Module should not be imported at wrapper creation time
            assert mod_path not in sys.modules, (
                "Module should not be imported at wrapper creation time"
            )
        finally:
            if saved_mod is not None:
                sys.modules[mod_path] = saved_mod

    def test_lazy_command__invokes_target_function(self):
        """Test that lazy_command correctly resolves and calls the target function."""
        from unittest.mock import MagicMock

        from fabric_cli.utils.fab_lazy_load import lazy_command

        # Create a test module with a mock function
        import types

        test_mod = types.ModuleType("_test_lazy_mod")
        test_mod.my_func = MagicMock(return_value=42)
        sys.modules["_test_lazy_mod"] = test_mod

        try:
            wrapper = lazy_command("_test_lazy_mod", "my_func")
            mock_args = MagicMock()
            result = wrapper(mock_args)

            test_mod.my_func.assert_called_once_with(mock_args)
            assert result == 42
        finally:
            del sys.modules["_test_lazy_mod"]

    def test_lazy_command__raises_on_missing_module(self):
        """Test that lazy_command raises ModuleNotFoundError for invalid modules."""
        from fabric_cli.utils.fab_lazy_load import lazy_command

        wrapper = lazy_command("nonexistent.module", "func")
        with pytest.raises(ModuleNotFoundError):
            wrapper(None)

    def test_lazy_command__raises_on_missing_function(self):
        """Test that lazy_command raises AttributeError for invalid function names."""
        from fabric_cli.utils.fab_lazy_load import lazy_command

        wrapper = lazy_command("fabric_cli.core.fab_constant", "nonexistent_func")
        with pytest.raises(AttributeError):
            wrapper(None)


class TestStartupPerformance:
    """Test suite for CLI startup performance."""

    def test_main_module_import__under_threshold(self):
        """Test that importing the main module stays under performance threshold."""
        # Remove cached modules to get a fresh import measurement
        modules_to_remove = [
            key for key in sys.modules if key.startswith("fabric_cli")
        ]
        saved_modules = {}
        for mod in modules_to_remove:
            saved_modules[mod] = sys.modules.pop(mod)

        try:
            start = time.perf_counter()
            importlib.import_module("fabric_cli.main")
            elapsed_ms = (time.perf_counter() - start) * 1000

            # The import should complete in under 500ms (generous threshold)
            # Before optimization: ~737ms, after: ~54ms
            assert elapsed_ms < 500, (
                f"fabric_cli.main import took {elapsed_ms:.0f}ms, expected < 500ms"
            )
        finally:
            # Restore modules
            for mod_name, mod in saved_modules.items():
                sys.modules[mod_name] = mod

    def test_heavy_modules_not_imported_at_startup(self):
        """Test that heavy dependencies are NOT loaded during main module import."""
        # Remove cached modules
        modules_to_remove = [
            key for key in sys.modules if key.startswith("fabric_cli")
        ]
        saved_modules = {}
        for mod in modules_to_remove:
            saved_modules[mod] = sys.modules.pop(mod)

        # Also remove the heavy dependencies
        heavy_modules = ["msal", "jwt", "cryptography"]
        saved_heavy = {}
        for mod_name in heavy_modules:
            keys_to_remove = [k for k in sys.modules if k.startswith(mod_name)]
            for k in keys_to_remove:
                saved_heavy[k] = sys.modules.pop(k)

        try:
            importlib.import_module("fabric_cli.main")

            # These heavy modules should NOT be imported during startup
            for mod_name in heavy_modules:
                assert mod_name not in sys.modules, (
                    f"'{mod_name}' should not be imported at startup"
                )
        finally:
            # Restore all modules
            for mod_name, mod in saved_modules.items():
                sys.modules[mod_name] = mod
            for mod_name, mod in saved_heavy.items():
                sys.modules[mod_name] = mod
