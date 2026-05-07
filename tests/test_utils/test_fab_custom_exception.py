# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.core.fab_exceptions import FabricAPIError, FabricCLIError


def test_custom_error_message():
    error = FabricCLIError("An error occurred.")
    assert error.message == "An error occurred"


def test_custom_error_message_without_period():
    error = FabricCLIError("An error occurred")
    assert error.message == "An error occurred"


def test_custom_error_formatted_message_with_status_code():
    error = FabricCLIError("An error occurred.", status_code=404)
    assert error.formatted_message() == "[404] An error occurred"


def test_fabric_api_error_valid_json_with_request_id():
    payload = json.dumps(
        {
            "errorCode": "ItemNotFound",
            "message": "The requested item was not found.",
            "requestId": "abc-123",
            "moreDetails": [],
        }
    )
    error = FabricAPIError(payload)

    assert error.status_code == "ItemNotFound"
    assert error.message == "The requested item was not found"
    assert error.request_id == "abc-123"
    assert error.more_details == []


def test_fabric_api_error_valid_json_without_request_id():
    payload = json.dumps(
        {
            "errorCode": "Unauthorized",
            "message": "Access denied.",
        }
    )
    error = FabricAPIError(payload)

    assert error.status_code == "Unauthorized"
    assert error.request_id is None
    # formatted_message should not append a request-id line
    assert "Request Id" not in error.formatted_message(verbose=True)


def test_fabric_api_error_non_json_body_falls_back_to_raw_text():
    raw = "Internal Server Error"
    error = FabricAPIError(raw)

    assert error.message == raw.rstrip(".")
    assert error.status_code is None
    assert error.request_id is None
    assert error.more_details == []


def test_fabric_api_error_non_dict_json_falls_back_to_raw_text():
    # Valid JSON but not an object — should be treated like a non-JSON body.
    for raw in ('"just a string"', "[1, 2, 3]", "42", "true"):
        error = FabricAPIError(raw)
        assert error.message == raw.rstrip(".")
        assert error.status_code is None
        assert error.request_id is None
        assert error.more_details == []


def test_fabric_api_error_formatted_message_non_json__no_request_id_line():
    error = FabricAPIError("Gateway Timeout")
    formatted = error.formatted_message(verbose=True)
    assert "Request Id" not in formatted
    assert "Gateway Timeout" in formatted
