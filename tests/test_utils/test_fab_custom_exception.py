# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core.fab_exceptions import FabricCLIError


def test_custom_error_message():
    error = FabricCLIError("An error occurred.")
    assert error.message == "An error occurred"


def test_custom_error_message_without_period():
    error = FabricCLIError("An error occurred")
    assert error.message == "An error occurred"


def test_custom_error_formatted_message_with_status_code():
    error = FabricCLIError("An error occurred.", status_code=404)
    assert error.formatted_message() == "[404] An error occurred"
