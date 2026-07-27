# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class BulkExportErrors:
    @staticmethod
    def invalid_target(full_name: str) -> str:
        return (
            f"'bulk-export' requires a workspace or folder path, but got '{full_name}'"
        )

    @staticmethod
    def recursive_flag_required() -> str:
        return f"The --recursive flag is required when bulk-exporting a Workspace or Folder"

    @staticmethod
    def empty_target(full_name: str) -> str:
        return f"No items found in '{full_name}'"

    @staticmethod
    def no_exportable_items() -> str:
        return "No exportable items found. All items have unsupported types"

    @staticmethod
    def invalid_export_path(path: str) -> str:
        return f"Export path '{path}' is not a valid directory"

    @staticmethod
    def path_mismatch() -> str:
        return "The path in the definition payload does not match the expected path based on the item name and type"

    @staticmethod
    def path_mismatch_full_export_path() -> str:
        return "The full export path of an item doesn't match the expected export path"
