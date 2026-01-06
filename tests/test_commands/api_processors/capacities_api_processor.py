# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import re

from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.utils import (
    load_request_json_body,
    load_response_json_body,
)
from tests.test_commands.data.static_test_data import get_mock_data, get_static_data


class CapacitiesAPIProcessor(BaseAPIProcessor):
    CAPACITIES_URI = "https://api.fabric.microsoft.com/v1/capacities"
    AZURE_CAPACITIES_URI = r".*/subscriptions/[0-9a-fA-F-]+/providers/Microsoft\.Fabric/capacities\?api-version=.*"
    AZURE_CAPACITY_URI = r".*/subscriptions/[0-9a-fA-F-]+/resourceGroups/[^/]+/providers/Microsoft\.Fabric/capacities/[^/?]+(\?api-version=[^&]+)?$"
    AZURE_CAPACITY_RESUME_SUSPEND_URI = r".*/subscriptions/[0-9a-fA-F-]+/resourceGroups/[^/]+/providers/Microsoft\.Fabric/capacities/[^/?]+/(resume|suspend)(\?api-version=[^&]+)?$"

    def __init__(self, generated_name_mapping):
        self.generated_name_mapping = generated_name_mapping

    def try_process_request(self, request) -> bool:
        if re.fullmatch(self.AZURE_CAPACITY_URI, request.uri, re.IGNORECASE):
            method = request.method
            if method in ("GET", "PATCH", "DELETE", "PUT"):
                self._handle_azure_capacity_request(request)
            return True
        if re.fullmatch(
            self.AZURE_CAPACITY_RESUME_SUSPEND_URI, request.uri, re.IGNORECASE
        ):
            method = request.method
            if method == "POST":
                self._handle_azure_capacity_request(request)
            return True
        return False

    def try_process_response(self, request, response) -> bool:
        uri = request.uri

        # Handle core capacities
        if uri.lower() == self.CAPACITIES_URI.lower():
            """https://learn.microsoft.com/en-us/rest/api/fabric/core/capacities/list-capacities?tabs=HTTP"""
            method = request.method
            if method == "GET":
                self._handle_get_fabric_response(response)
            return True

        # Handle Azure capacities list-by-subscription
        # Example: /subscriptions/{subscriptionId}/providers/Microsoft.Fabric/capacities?api-version=2023-11-01-preview
        if re.fullmatch(self.AZURE_CAPACITIES_URI, uri, re.IGNORECASE):
            """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/list-by-subscription?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
            method = request.method
            if method == "GET":
                self._handle_get_azure_response(response)
            return True

        if re.fullmatch(self.AZURE_CAPACITY_URI, uri, re.IGNORECASE):
            """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/get?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
            method = request.method
            if method == "GET":
                self._handle_get_azure_capacity_response(response)
            return True

        return False

    def _handle_azure_capacity_request(self, request):
        # Replace the capacity name in the URI with the mocked capacity name, but only if it matches the static data capacity name
        static_name = get_static_data().capacity.name
        mock_name = get_mock_data().capacity.name
        # Only replace if the current capacity name is the static one
        request.uri = re.sub(
            rf"/capacities/{re.escape(static_name)}",
            f"/capacities/{mock_name}",
            request.uri,
            re.IGNORECASE,
        )

        request_body = load_request_json_body(request)
        if (
            request_body
            and request_body["location"]
            and request_body["location"] == get_static_data().azure_location
        ):
            request_body["location"] = get_mock_data().azure_location
            new_body_str = json.dumps(request_body)
            request.body = new_body_str

    def _handle_get_fabric_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        new_value = []
        for item in data["value"]:
            # 2 capacities ids are relevant, the one that was defined as test input and the one created by the test
            if item["id"].lower() == get_static_data().capacity.id.lower():
                item["id"] = get_mock_data().capacity.id
                item["displayName"] = get_mock_data().capacity.name
                new_value.append(item)
            elif item["displayName"] in self.generated_name_mapping:
                new_value.append(item)

        data["value"] = new_value

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_get_azure_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        new_value = []
        for item in data["value"]:
            # 2 capacities ids are relevant, the one that was defined as test input and the one created by the test
            if (
                item["id"].endswith(
                    f"/capacities/{get_static_data().capacity.name}", re.IGNORECASE
                )
                and item["name"].lower() == get_static_data().capacity.name.lower()
            ):
                # Replace the id suffix with /capacities/{mock_id}
                item["id"] = re.sub(
                    r"/capacities/[^/]+$",
                    f"/capacities/{get_mock_data().capacity.name}",
                    item["id"],
                    re.IGNORECASE,
                )
                item["name"] = get_mock_data().capacity.name
                new_value.append(item)
            elif item["name"] in self.generated_name_mapping:
                new_value.append(item)

        data["value"] = new_value

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_get_azure_capacity_response(self, response):
        data = load_response_json_body(response)
        if not data:
            return

        if (
            data["id"].endswith(
                f"/capacities/{get_static_data().capacity.name}", re.IGNORECASE
            )
            and data["name"].lower() == get_static_data().capacity.name.lower()
        ):
            data["id"] = re.sub(
                r"/capacities/[^/]+$",
                f"/capacities/{get_mock_data().capacity.name}",
                data["id"],
                re.IGNORECASE,
            )
            data["name"] = get_mock_data().capacity.name

        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")
