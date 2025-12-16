# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class ExportErrors:
    @staticmethod
    def invalid_export_format(valid_formats: list[str]) -> str:
        return (
            f"Invalid format. Only the following formats are supported: {valid_formats}"
        )
