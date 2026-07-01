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
    def missing_restore_params() -> str:
        return (
            "Missing required parameter(s) for restore mode. "
            "Required: restorePointInTime, itemId, workspaceId. "
            "Example: -P mode=Restore,restorePointInTime=2024-01-15T10:30:00Z,itemId=<item-id>,workspaceId=<workspace-id>"
        )

    @staticmethod
    def missing_restore_deleted_params() -> str:
        return (
            "Missing required parameter(s) for RestoreDeletedDatabase mode. "
            "Required: restorableDeletedDatabaseName, restorePointInTime. "
            "Example: -P mode=RestoreDeletedDatabase,restorableDeletedDatabaseName=<name>,restorePointInTime=2024-01-15T10:30:00Z"
        )

    @staticmethod
    def unsupported_creation_mode(mode: str) -> str:
        return (
            f"Unsupported creation mode '{mode}'. "
            "Supported modes: New, Restore, RestoreDeletedDatabase"
        )

    @staticmethod
    def invalid_backup_retention_days(value: str) -> str:
        return f"Invalid backupRetentionDays value '{value}'. It must be an integer"
