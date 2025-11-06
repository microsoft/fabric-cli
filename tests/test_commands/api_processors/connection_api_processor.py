# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.utils import (
    load_request_json_body,
    load_response_json_body,
)
from tests.test_commands.data.static_test_data import get_mock_data, get_static_data


class ConnectionAPIProcessor(BaseAPIProcessor):
    CONNECTIONS_URI = "https://api.fabric.microsoft.com/v1/connections"

    def __init__(self, generated_name_mapping):
        self.generated_name_mapping = generated_name_mapping

    def try_process_request(self, request) -> bool:
        uri = request.uri
        self._mock_gateway_id_in_uri(request)
        
        # Handle connection creation and listing
        if uri.lower() == self.CONNECTIONS_URI.lower():
            method = request.method
            if method == "POST":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/create-connection?tabs=HTTP"""
                self._handle_post_request(request)
            return True
        
        # Handle supported connection types with gateway ID query parameter
        if uri.lower().startswith(f"{self.CONNECTIONS_URI.lower()}/supportedconnectiontypes"):
            return True
        
        return False

    def try_process_response(self, request, response) -> bool:
        uri = request.uri
        # Handle list_connections
        if uri.lower() == self.CONNECTIONS_URI.lower():
            method = request.method
            if method == "GET":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/list-connections?tabs=HTTP"""
                self._handle_get_response(response)
            if method == "POST":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/create-connection?tabs=HTTP"""
                self._handle_post_response(response)
            return True
        return False

    def _handle_get_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        new_value = []
        for item in data["value"]:
            if item.get("displayName") in self.generated_name_mapping:
                self._mock_gateway_references(item)
                new_value.append(item)

        data["value"] = new_value

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_post_request(self, request):
        """Handle POST request for connection creation"""
        data = load_request_json_body(request)
        if not data:
            return

        self._mock_gateway_references(data)

        new_body_str = json.dumps(data)
        request.body = new_body_str

    def _handle_post_response(self, response):
        """Handle POST response for connection creation"""
        data = load_response_json_body(response)
        if not data:
            return

        self._mock_gateway_references(data)

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _mock_gateway_references(self, obj):
        """Mock gateway ID references in connection objects"""
        static_gateway_id = get_static_data().onpremises_gateway_details.id
        mock_gateway_id = get_mock_data().onpremises_gateway_details.id
        
        # Mock direct gatewayId field
        if "gatewayId" in obj and obj["gatewayId"] == static_gateway_id:
            obj["gatewayId"] = f"{mock_gateway_id}"
        
        # Mock gatewayId in credentialDetails.values arrays
        if "credentialDetails" in obj and "values" in obj["credentialDetails"]:
            for cred_value in obj["credentialDetails"]["values"]:
                if isinstance(cred_value, dict) and "gatewayId" in cred_value:
                    if cred_value["gatewayId"] == static_gateway_id:
                        cred_value["gatewayId"] = mock_gateway_id

    def _mock_gateway_id_in_uri(self, request):
        """Mock gateway IDs in request URIs and query parameters"""
        static_gateway_id = get_static_data().onpremises_gateway_details.id
        mock_gateway_id = get_mock_data().onpremises_gateway_details.id
        
        # Replace gateway ID in URI path and query parameters
        request.uri = request.uri.replace(static_gateway_id, mock_gateway_id)
