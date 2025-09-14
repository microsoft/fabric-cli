# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import sys
from ast import Constant

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils.fab_hostname_validator import validate_and_get_env_variable


# region mock fixtures
@pytest.fixture(autouse=True)
def setup_default_format(mock_fab_set_state_config):
    mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "text")
    yield


def test_validate_and_get_env_variable_valid_hostnames(capsys):
    """Test validation of valid hostname names"""
    valid_hostnames = [
        "api.fabric.microsoft.com",
        "dfs.fabric.microsoft.com",
        "api.powerbi.com",
        "management.azure.com",
        "management.test.hostname"
    ]

    for hostname in valid_hostnames:
        os.environ["TEST_HOSTNAME"] = hostname
        result = validate_and_get_env_variable("TEST_HOSTNAME", "default.com")
        assert result == hostname
        assert capsys.readouterr().out == ""  # No error output

def test_validate_and_get_env_variable_invalid_hostnames(capsys, monkeypatch):
    """Test validation of invalid hostname names exits with error"""
    invalid_hostnames = [
        "invalid.com",
        "notfabric.microsoft.com",
        "api.fabric.other.com",
        "management",
        "http://api.fabric.microsoft.com",
    ]

    # Mock sys.exit to prevent actual exit
    def mock_exit(code):
        assert code == 1
        raise SystemExit(code)
    monkeypatch.setattr(sys, "exit", mock_exit)

    for hostname in invalid_hostnames:
        os.environ["TEST_HOSTNAME"] = hostname
        with pytest.raises(FabricCLIError) as ex:
            validate_and_get_env_variable("TEST_HOSTNAME", "default.com")

        # Verify error output
        assert ex.value.message == ErrorMessages.Common.invalid_hostname("TEST_HOSTNAME")
        assert ex.value.status_code == fab_constant.ERROR_INVALID_HOSTNAME

def test_validate_and_get_env_variable_default_value(capsys):
    """Test that default value is used when environment variable is not set"""
    if "TEST_HOSTNAME" in os.environ:
        del os.environ["TEST_HOSTNAME"]
    
    result = validate_and_get_env_variable("TEST_HOSTNAME", "api.fabric.microsoft.com")
    assert result == "api.fabric.microsoft.com"
    assert capsys.readouterr().out == ""  # No error output

def test_validate_and_get_env_variable_strips_path(capsys):
    """Test that paths are stripped from hostname values"""
    os.environ["TEST_HOSTNAME"] = "api.powerbi.com/v1.0/myorg"
    result = validate_and_get_env_variable("TEST_HOSTNAME", "default.com")
    assert result == "api.powerbi.com"
    assert capsys.readouterr().out == ""  # No error output

@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test"""
    yield
    if "TEST_HOSTNAME" in os.environ:
        del os.environ["TEST_HOSTNAME"]
