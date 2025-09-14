# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class TableErrors:
    @staticmethod
    def invalid_table_path() -> str:
        return "Invalid path. Please provide a valid table path"

    @staticmethod
    def invalid_format_argument(part: str) -> str:
        return f"Invalid format argument: '{part}' (missing '=')"

    @staticmethod
    def invalid_key(key: str, allowed_keys: str) -> str:
        return f"Invalid key: '{key}'. Allowed keys are: {allowed_keys}"