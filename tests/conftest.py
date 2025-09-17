# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch

import pytest

import fabric_cli.core.fab_state_config as state_config


@pytest.fixture
def mock_questionary_print():
    with patch("questionary.print") as mock:
        yield mock


@pytest.fixture
def mock_print_warning():
    """Mock fab_ui.print_warning function."""
    with patch("fabric_cli.utils.fab_ui.print_warning") as mock:
        yield mock


@pytest.fixture
def mock_os_path_exists():
    with patch("os.path.exists") as mock:
        yield mock


@pytest.fixture
def mock_json_load():
    with patch("json.load") as mock:
        yield mock


@pytest.fixture
def mock_os_remove():
    with patch("os.remove") as mock:
        yield mock


@pytest.fixture
def mock_glob_glob():
    with patch("glob.glob") as mock:
        yield mock


@pytest.fixture
def mock_fab_set_state_config():
    original_values = {}

    def _set_config(key: str, value: str):
        # Store original value if it exists
        try:
            original_values[key] = state_config.get_config(key)
        except KeyError:
            # Key didn't exist before, mark it for deletion after test
            original_values[key] = None

        # Set the new value
        state_config.set_config(key, value)

    yield _set_config

    # Restore original values after test
    for key, original_value in original_values.items():
        # Restore original value
        state_config.set_config(key, original_value)


@pytest.fixture
def reset_context():
    """Reset the Context singleton before test to prevent state leakage."""
    from fabric_cli.core.fab_context import Context

    context_instance = Context()
    context_instance._context = None
    context_instance._command = None
    context_instance._loading_context = False

    yield context_instance
