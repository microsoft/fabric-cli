# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class CpErrors:
    @staticmethod
    def item_exists_different_path() -> str:
        return (
            "An item with the same name exists in a different path within the workspace"
        )
