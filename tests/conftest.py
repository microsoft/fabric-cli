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
