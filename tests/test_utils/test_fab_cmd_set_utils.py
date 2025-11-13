# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.utils.fab_cmd_set_utils import update_fabric_element


def test_update_fabric_element_with_raw_string_flag():
    resource_def = {"definition": {"parts": [{"x": "old_value"}]}}

    json_string_input = '{"transparency":{"Value":"70D"}}'

    json_payload, updated_def = update_fabric_element(
        resource_def=resource_def,
        query="definition.parts[0].x",
        input=json_string_input,
        decode_encode=False,
        raw_string=True,
    )

    assert updated_def["definition"]["parts"][0]["x"] == json_string_input
    assert isinstance(updated_def["definition"]["parts"][0]["x"], str)

    parsed_payload = json.loads(json_payload)
    assert parsed_payload["definition"]["parts"][0]["x"] == json_string_input


def test_update_fabric_element_without_raw_string_flag():
    resource_def = {"definition": {"parts": [{"x": "old_value"}]}}

    json_string_input = '{"transparency":{"Value":"70D"}}'

    json_payload, updated_def = update_fabric_element(
        resource_def=resource_def,
        query="definition.parts[0].x",
        input=json_string_input,
        decode_encode=False,
        raw_string=False,
    )

    assert isinstance(updated_def["definition"]["parts"][0]["x"], dict)
    assert updated_def["definition"]["parts"][0]["x"]["transparency"]["Value"] == "70D"

    parsed_payload = json.loads(json_payload)
    assert isinstance(parsed_payload["definition"]["parts"][0]["x"], dict)
    assert (
        parsed_payload["definition"]["parts"][0]["x"]["transparency"]["Value"] == "70D"
    )
