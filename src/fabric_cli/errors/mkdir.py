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

    @staticmethod
    def invalid_restore_point_in_time() -> str:
        return (
            "Invalid restorePointInTime format. "
            "Please provide an ISO 8601 timestamp with timezone (e.g., '2024-01-15T10:30:00Z' or '2024-01-15T10:30:00+00:00')"
        )

    @staticmethod
    def missing_restore_params() -> str:
        return (
            "Missing required parameter(s) for restore mode. "
            "Required: restorePointInTime, itemId, workspaceId. "
            "Example: -P mode=restore,restorePointInTime=2024-01-15T10:30:00Z,itemId=<guid>,workspaceId=<guid>"
        )

    @staticmethod
    def invalid_creation_mode(mode: str) -> str:
        return (
            f"Invalid mode '{mode}' for SQLDatabase creation. "
            "Supported modes: 'restore'. "
            "Omit mode parameter for standard database creation."
        )
