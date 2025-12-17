# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class ExportErrors:
    @staticmethod
    def invalid_export_format(valid_formats: list[str]) -> str:
        message = "Only the following formats are supported: " + ", ".join(valid_formats) if len(valid_formats) else "No formats are supported"
        return f"Invalid format. {message}"