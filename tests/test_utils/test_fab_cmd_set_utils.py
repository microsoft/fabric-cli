# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

import pytest

from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils.fab_cmd_set_utils import (
    extract_updated_properties,
    update_fabric_element,
    validate_item_query,
)
from fabric_cli.utils.fab_jmespath import has_filter_or_wildcard


def test_update_fabric_element_with_json_input_success():
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


def test_has_filter_or_wildcard_with_wildcard():
    assert has_filter_or_wildcard("items[*].name") is True


def test_has_filter_or_wildcard_with_filter():
    assert has_filter_or_wildcard("items[?price > 100]") is True


def test_has_filter_or_wildcard_with_flatten():
    assert has_filter_or_wildcard("items[].name") is True


def test_has_filter_or_wildcard_with_or_expression():
    assert has_filter_or_wildcard("name || displayName") is True


def test_has_filter_or_wildcard_without_filters():
    assert has_filter_or_wildcard("config.settings.name") is False


def test_has_filter_or_wildcard_with_array_index():
    assert has_filter_or_wildcard("items[0].name") is False


def test_validate_item_query_with_wildcard_failure():
    with pytest.raises(FabricCLIError) as exc_info:
        validate_item_query("properties.items[*].name")
    assert "filters or wildcards" in str(exc_info.value)


def test_validate_item_query_with_filter_failure():
    with pytest.raises(FabricCLIError) as exc_info:
        validate_item_query("properties.items[?price > 100]")
    assert "filters or wildcards" in str(exc_info.value)


def test_validate_item_query_with_flatten_failure():
    with pytest.raises(FabricCLIError) as exc_info:
        validate_item_query("definition.items[].name")
    assert "filters or wildcards" in str(exc_info.value)


def test_validate_item_query_valid_display_name_success():
    validate_item_query("displayName")


def test_validate_item_query_valid_description_success():
    validate_item_query("description")


def test_validate_item_query_valid_properties_success():
    validate_item_query("properties")


def test_validate_item_query_valid_definition_success():
    validate_item_query("definition.parts[0].path")


def test_validate_item_query_invalid_key_failure():
    with pytest.raises(FabricCLIError) as exc_info:
        validate_item_query("invalidKey")
    assert "Invalid query 'invalidKey'" in str(exc_info.value)
    assert "displayName" in str(exc_info.value)
    assert "description" in str(exc_info.value)
    assert "properties" in str(exc_info.value)
    assert "definition" in str(exc_info.value)


def test_validate_item_query_invalid_key_with_dot_failure():
    with pytest.raises(FabricCLIError) as exc_info:
        validate_item_query("invalidKey.subkey")
    assert "Invalid query 'invalidKey.subkey'" in str(exc_info.value)


def test_validate_item_query_definition_with_item_supports_export_success():
    from unittest.mock import Mock

    from fabric_cli.core.fab_commands import Command

    mock_item = Mock()
    mock_item.check_command_support.return_value = True
    mock_item.item_type = "Lakehouse"

    validate_item_query("definition.parts[0].payload", item=mock_item)
    mock_item.check_command_support.assert_called_once_with(Command.FS_EXPORT)


def test_validate_item_query_definition_with_item_not_supports_export_failure():
    from unittest.mock import Mock

    from fabric_cli.core.fab_commands import Command

    mock_item = Mock()
    mock_item.check_command_support.return_value = False
    mock_item.item_type = "Dashboard"

    with pytest.raises(FabricCLIError) as exc_info:
        validate_item_query("definition.metadata", item=mock_item)

    assert "does not support definition updates" in str(exc_info.value)
    mock_item.check_command_support.assert_called_once_with(Command.FS_EXPORT)


def test_validate_item_query_definition_without_item_success():
    validate_item_query("definition.parts[0]")


def test_validate_item_query_properties_with_item_success():
    from unittest.mock import Mock

    mock_item = Mock()
    mock_item.item_type = "Lakehouse"

    validate_item_query("properties.settings", item=mock_item)
