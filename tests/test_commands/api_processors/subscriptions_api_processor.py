# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import re

from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.utils import load_response_json_body
from tests.test_commands.data.static_test_data import get_mock_data, get_static_data


class SubscriptionsAPIProcessor(BaseAPIProcessor):
    SUBSCRIPTIONS_URI_PREFIX = "https://management.azure.com/subscriptions?api-version="
    VNETS_URI_REGEX = re.compile(
        r"https://management\.azure\.com/subscriptions/[^/]+/providers/Microsoft\.Network/virtualNetworks\?api-version=",
        re.IGNORECASE,
    )

    def __init__(self, generated_name_mapping):
        self.generated_name_mapping = generated_name_mapping

    def try_process_request(self, request) -> bool:
        return False

    def try_process_response(self, request, response) -> bool:
        uri = request.uri
        method = getattr(request, "method", None)
        if self._is_subscriptions_uri(uri) and method == "GET":
            self._handle_get_subscriptions_response(response)
            return True
        elif self._is_vnets_uri(uri) and method == "GET":
            self._handle_vnets_get_response(response)
            return True
        return False

    def _is_subscriptions_uri(self, uri: str) -> bool:
        # Match URI like https://management.azure.com/subscriptions?api-version=ANYTHING
        return uri.lower().startswith(self.SUBSCRIPTIONS_URI_PREFIX.lower())

    def _is_vnets_uri(self, uri: str) -> bool:
        # Match URI like https://management.azure.com/subscriptions/<id>/providers/Microsoft.Network/virtualNetworks?api-version=ANYTHING
        return bool(self.VNETS_URI_REGEX.match(uri))

    def _handle_get_subscriptions_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        new_value = []
        for subscription in data["value"]:
            subscription_id = subscription["id"]
            if get_static_data().azure_subscription_id in subscription_id:
                new_value.append({"id": subscription_id})

        data["value"] = new_value
        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")

    def _handle_vnets_get_response(self, response):
        data = load_response_json_body(response)
        if not data or "value" not in data:
            return

        vnet_name = get_static_data().vnet.name
        new_value = []
        for vnet in data["value"]:
            name = vnet.get("name", "")
            if vnet_name == name:
                mock_vnet_name = get_mock_data().vnet.name
                vnet_id = vnet.get("id", "")
                vnet_id = re.sub(
                    r"virtualNetworks/[^/]+$",
                    f"virtualNetworks/{mock_vnet_name}",
                    vnet_id,
                )
                vnet_dict = {
                    "name": mock_vnet_name,
                    "id": vnet_id,
                }

                properties = vnet.get("properties", {})
                subnets = properties.get("subnets", [])
                vnet_subnet = get_static_data().vnet.subnet
                mock_subnet_name = get_mock_data().vnet.subnet
                vnet_dict["properties"] = {
                    "subnets": [
                        {
                            "name": mock_subnet_name,
                            "id": re.sub(
                                r"virtualNetworks/[^/]+/subnets/[^/]+$",
                                f"virtualNetworks/{mock_vnet_name}/subnets/{mock_subnet_name}",
                                subnet.get("id", ""),
                            ),
                        }
                        for subnet in subnets
                        if subnet.get("name") == vnet_subnet
                    ]
                }
                new_value.append(vnet_dict)

        data["value"] = new_value
        new_body_str = json.dumps(data)
        response["body"]["string"] = new_body_str.encode("utf-8")
