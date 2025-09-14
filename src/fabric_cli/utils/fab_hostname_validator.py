# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Hostname validation utilities for Microsoft Fabric CLI endpoints.
"""
import os
import re
import sys

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages

# Define a regular expression for valid hostnames with wildcards
VALID_HOSTNAME_REGEX = re.compile(
    r"^([\w-]+\.)?(fabric\.microsoft\.com|dfs\.fabric\.microsoft\.com|powerbi\.com|management\.[\w-]+\.[\w-]+)$"
)

def validate_and_get_env_variable(env_var_name: str, default_value: str) -> str:
    """
    Validates and returns the hostname from an environment variable.
    Handles error printing and program exit if validation fails.

    Args:
        env_var_name (str): Name of the environment variable
        default_value (str): Default value if environment variable is not set

    Returns:
        str: The validated hostname
    """
    value = os.environ.get(env_var_name, default_value)
    value = value.split("/")[0]  # Extract the hostname part (before any path)

    if not VALID_HOSTNAME_REGEX.match(value):
        raise FabricCLIError(
            ErrorMessages.Common.invalid_hostname(env_var_name),
            fab_constant.ERROR_INVALID_HOSTNAME,
        )

    return value
