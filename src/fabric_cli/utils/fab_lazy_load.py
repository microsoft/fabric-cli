# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Lazy loading utilities for fabric CLI.
This module provides lazy loading for external dependencies to avoid
importing them until they are actually needed.
The module will be loaded only when the function is called for the first time and cached afterwards.
"""

import importlib


def questionary():
    import questionary

    return questionary


def lazy_command(module_path: str, func_name: str):
    """Create a lazy-loading wrapper for a command function.

    Returns a callable that defers importing the command module until the
    command is actually invoked.  This avoids pulling in heavy dependencies
    (API clients, auth, etc.) at parser-registration time.

    Args:
        module_path: Dotted Python module path, e.g. ``"fabric_cli.commands.fs.fab_fs"``.
        func_name: Name of the callable inside *module_path*, e.g. ``"ls_command"``.
    """

    def wrapper(args):
        mod = importlib.import_module(module_path)
        return getattr(mod, func_name)(args)

    return wrapper
