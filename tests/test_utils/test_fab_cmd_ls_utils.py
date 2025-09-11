# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.utils.fab_cmd_ls_utils import sort_elements


def test_sort_elements_by_default_name():
    # Create test elements with different names
    elements = [{"name": "Beta"}, {"name": "alpha"}, {"name": "charlie"}]

    sorted_elements = sort_elements(elements)

    # Verify case-insensitive sorting by name
    assert [element["name"] for element in sorted_elements] == [
        "alpha",
        "Beta",
        "charlie",
    ]


def test_sort_elements_by_custom_key():
    # Create test elements with a different key to sort by
    elements = [
        {"id": "123", "name": "First"},
        {"id": "ABC", "name": "Second"},
        {"id": "abc", "name": "Third"},
    ]

    sorted_elements = sort_elements(elements, key="id")

    # Verify case-insensitive sorting by id
    assert [element["id"] for element in sorted_elements] == ["123", "ABC", "abc"]


def test_sort_elements_with_missing_keys():
    # Create elements where some are missing the sort key
    elements = [{"name": "Beta"}, {}, {"name": "alpha"}]  # Missing name

    sorted_elements = sort_elements(elements)

    # Verify missing keys are treated as empty strings and sort first
    assert [element.get("name", "") for element in sorted_elements] == [
        "",
        "alpha",
        "Beta",
    ]


def test_sort_elements_empty_list():
    # Test sorting an empty list
    elements = []

    sorted_elements = sort_elements(elements)

    # Verify empty list is handled correctly
    assert sorted_elements == []


def test_sort_elements_case_sensitivity():
    # Test that sorting is truly case-insensitive
    elements = [
        {"name": "alpha"},
        {"name": "BETA"},
        {"name": "Charlie"},
        {"name": "delta"},
        {"name": "ALPHA"},
    ]

    sorted_elements = sort_elements(elements)

    # Verify case-insensitive sorting preserves original case
    assert [element["name"] for element in sorted_elements] == [
        "alpha",
        "ALPHA",
        "BETA",
        "Charlie",
        "delta",
    ]
