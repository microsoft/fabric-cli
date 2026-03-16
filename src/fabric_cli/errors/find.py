# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class FindErrors:
    @staticmethod
    def unsupported_parameter(key: str) -> str:
        return f"'{key}' isn't a supported parameter. Supported: type"

    @staticmethod
    def invalid_parameter_format(param: str) -> str:
        return f"Invalid parameter format: '{param}'. Use key=value or key!=value."

    @staticmethod
    def unsearchable_type(type_name: str) -> str:
        return f"'{type_name}' isn't searchable via the catalog search API."

    @staticmethod
    def unrecognized_type(type_name: str, hint: str) -> str:
        return f"'{type_name}' isn't a recognized item type.{hint}"

    @staticmethod
    def search_failed(message: str) -> str:
        return f"Catalog search failed: {message}"

    @staticmethod
    def invalid_response() -> str:
        return "Catalog search returned an invalid response."
