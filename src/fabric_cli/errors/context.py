# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class ContextErrors:

    @staticmethod
    def context_load_failed() -> str:
        return "Context load failed. Context has been reset"