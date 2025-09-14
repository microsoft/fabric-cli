# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class HierarchyErrors:
    @staticmethod
    def invalid_parent_type(parent_type: str) -> str:
        return f"The parent type '{parent_type}' is invalid"
    
    @staticmethod
    def invalid_type(name: str) -> str:
        return f"Invalid type '{name}'"

    @staticmethod
    def command_not_supported(command: str) -> str:
        return f"not supported for command '{command}'"

    @staticmethod
    def item_type_not_valid(item_type: str) -> str:
        return f"Item type {item_type} is not a valid ItemType"

    @staticmethod
    def key_not_found_in_properties(key: str) -> str:
        return f"The key '{key}' could not be found in item mutable properties"

    @staticmethod
    def item_type_doesnt_support_definition_payload(item_type: str) -> str:
        return f"{item_type} doesn't support definition payload"

    @staticmethod
    def item_name_contains_unsupported_characters(item_type: str, name: str) -> str:
        return f"{item_type} name '{name}' contains unsupported special characters"

    @staticmethod
    def invalid_item_name(name: str) -> str:
        return f"Invalid item name '{name}'"