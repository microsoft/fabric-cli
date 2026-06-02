# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class FindErrors:
    @staticmethod
    def unrecognized_type(type_name: str, hint: str) -> str:
        return f"'{type_name}' isn't a recognized item type.{hint}"

    @staticmethod
    def search_failed(message: str) -> str:
        return f"Catalog search failed: {message}"
