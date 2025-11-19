# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

import pytest

from fabric_cli.utils.fab_cmd_set_utils import (
    extract_updated_properties,
    update_fabric_element,
)


def test_update_fabric_element_with_json_input():
    resource_def = {"definition": {"parts": [{"x": "old_value"}]}}

    json_string_input = '{"transparency":{"Value":"70D"}}'

    json_payload, updated_def = update_fabric_element(
        resource_def=resource_def,
        query="definition.parts[0].x",
        input=json_string_input,
        decode_encode=False,
    )

    assert isinstance(updated_def["definition"]["parts"][0]["x"], dict)
    assert updated_def["definition"]["parts"][0]["x"]["transparency"]["Value"] == "70D"

    parsed_payload = json.loads(json_payload)
    assert isinstance(parsed_payload["definition"]["parts"][0]["x"], dict)
    assert (
        parsed_payload["definition"]["parts"][0]["x"]["transparency"]["Value"] == "70D"
    )


def test_extract_updated_properties_preserves_sibling_properties_success():
    updated_metadata = {"k": {"k1": "v1", "k2": {"k3": "value"}}}
    query_path = "k.k2.k3"

    update_payload_dict = extract_updated_properties(updated_metadata, query_path)

    assert "k" in update_payload_dict
    assert update_payload_dict["k"]["k1"] == "v1"
    assert update_payload_dict["k"]["k2"]["k3"] == "value"


def test_extract_updated_properties_top_level_query_replaces_json_object_success():
    updated_metadata = {"k": {"k2": {"k3": "value"}}}
    query_path = "k"

    update_payload_dict = extract_updated_properties(updated_metadata, query_path)

    assert "k" in update_payload_dict
    assert update_payload_dict["k"]["k2"]["k3"] == "value"
