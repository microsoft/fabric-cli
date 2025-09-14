# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class MkdirErrors:
    @staticmethod
    def workspace_name_exists() -> str:
        return (
            "A workspace with the same name already exists. Please use a different name"
        )

    @staticmethod
    def workspace_capacity_not_found() -> str:
        return (
            "The specified capacity was not found or is invalid. "
            "Please use 'config set default_capacity <capacity_name>' or '-P capacityName=<capacity_name>' to specify a valid capacity"
        )

    @staticmethod
    def folder_name_exists() -> str:
        return "A folder with the same name already exists"
