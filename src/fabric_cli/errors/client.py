# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class ClientErrors:
    @staticmethod
    def response_payload_not_dictionary() -> str:
        return "Response payload is not a dictionary"

    @staticmethod
    def unexpected_error_response(http_status_code: int, message: str) -> str:
        return f"An unexpected error occurred with status code: {http_status_code} and message: {message}"

    @staticmethod
    def resource_type_not_found_in_provider(resource_type: str, provider_namespace: str) -> str:
        return f"Resource type '{resource_type}' not found in provider '{provider_namespace}'"