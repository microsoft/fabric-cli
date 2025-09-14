# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.utils import load_response_json_body


class ConnectionAPIProcessor(BaseAPIProcessor):
    CONNECTIONS_URI = "https://api.fabric.microsoft.com/v1/connections"

    def __init__(self, generated_name_mapping):
        self.generated_name_mapping = generated_name_mapping

    def try_process_request(self, request) -> bool:
        return False

    def try_process_response(self, request, response) -> bool:
        uri = request.uri
        # Handle list_connections
        if uri.lower() == self.CONNECTIONS_URI.lower():
            method = request.method
            if method == "GET":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/list-connections?tabs=HTTP"""
                self._handle_get_response(response)
            return True
        return False

    def _handle_get_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        new_value = []
        for item in data["value"]:
            if item.get("displayName") in self.generated_name_mapping:
                new_value.append(item)

        data["value"] = new_value

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")
