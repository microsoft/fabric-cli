# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.utils import load_response_json_body


class DomainsAPIProcessor(BaseAPIProcessor):
    DOMAINS_URI = "https://api.fabric.microsoft.com/v1/admin/domains"

    def __init__(self, generated_name_mapping):
        self.generated_name_mapping = generated_name_mapping

    def try_process_request(self, request) -> bool:
        return False

    def try_process_response(self, request, response) -> bool:
        uri = request.uri
        if uri.lower() == self.DOMAINS_URI.lower():
            method = request.method
            if method == "GET":
                self._handle_get_response(response)
            return True
        return False

    def _handle_get_response(self, response):
        data = load_response_json_body(response)
        if not data or "domains" not in data:
            return

        new_value = []
        for item in data["domains"]:
            if item.get("displayName") in self.generated_name_mapping:
                new_value.append(item)

        data["domains"] = new_value

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")
