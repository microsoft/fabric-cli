# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import re
from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.utils import (
    load_request_json_body,
    load_response_json_body,
)
from tests.test_commands.data.static_test_data import get_mock_data


class GatewayAPIProcessor(BaseAPIProcessor):

    GATEWAYS_URI = "https://api.fabric.microsoft.com/v1/gateways"

    def __init__(self, generated_name_mapping):
        self.generated_name_mapping = generated_name_mapping

    def try_process_request(self, request) -> bool:
        uri = request.uri
        # Handle list_gateways
        if uri.lower() == self.GATEWAYS_URI.lower():
            method = request.method
            if method == "POST":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/create-gateway?tabs=HTTP"""
                self._handle_post_request(request)
            return True
        return False

    def try_process_response(self, request, response) -> bool:
        uri = request.uri
        # Handle list_gateways
        if uri.lower() == self.GATEWAYS_URI.lower():
            method = request.method
            if method == "GET":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/list-gateways?tabs=HTTP"""
                self._handle_get_response(response)
            if method == "POST":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/create-gateway?tabs=HTTP"""
                self._handle_post_response(response)
            return True

        if re.fullmatch(rf"{re.escape(self.GATEWAYS_URI)}/[0-9a-fA-F-]{{36}}", uri):
            method = request.method
            if method == "GET" or method == "PATCH":
                """https://learn.microsoft.com/en-us/rest/api/fabric/core/gateways/get-gateway?tabs=HTTP"""
                self._handle_get_gateway_response(response)
            return True
        return False

    def _handle_get_gateway_response(self, response):
        data = load_response_json_body(response)
        if not data:
            return
        self._mock_virtual_network_azure_resource(data)
        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_get_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        new_value = []
        for item in data["value"]:
            if item.get("displayName") in self.generated_name_mapping:
                self._mock_virtual_network_azure_resource(item)
                new_value.append(item)

        data["value"] = new_value

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_post_response(self, response):
        data = load_response_json_body(response)
        if not data:
            return

        self._mock_virtual_network_azure_resource(data)

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_post_request(self, request):
        data = load_request_json_body(request)
        if not data:
            return

        self._mock_virtual_network_azure_resource(data)

        new_body_str = json.dumps(data)
        request.body = new_body_str

    def _mock_virtual_network_azure_resource(self, obj):
        if "virtualNetworkAzureResource" in obj:
            if "virtualNetworkName" in obj["virtualNetworkAzureResource"]:
                obj["virtualNetworkAzureResource"][
                    "virtualNetworkName"
                ] = get_mock_data().vnet.name
            if "subnetName" in obj["virtualNetworkAzureResource"]:
                obj["virtualNetworkAzureResource"][
                    "subnetName"
                ] = get_mock_data().vnet.subnet
            if "resourceGroupName" in obj["virtualNetworkAzureResource"]:
                obj["virtualNetworkAzureResource"][
                    "resourceGroupName"
                ] = get_mock_data().azure_resource_group
