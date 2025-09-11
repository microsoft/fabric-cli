# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List
from tests.test_commands.api_processors.base_api_processor import BaseAPIProcessor
from tests.test_commands.api_processors.capacities_api_processor import (
    CapacitiesAPIProcessor,
)
from tests.test_commands.api_processors.gateway_api_processor import GatewayAPIProcessor
from tests.test_commands.api_processors.subscriptions_api_processor import (
    SubscriptionsAPIProcessor,
)
from tests.test_commands.api_processors.workspace_api_processor import (
    WorkspaceAPIProcessor,
)
from tests.test_commands.api_processors.domains_api_processor import DomainsAPIProcessor
from tests.test_commands.api_processors.connection_api_processor import (
    ConnectionAPIProcessor,
)


class APIProcessorHandler:
    def __init__(self, generated_name_mapping):
        self._api_handlers: List[BaseAPIProcessor] = [
            CapacitiesAPIProcessor(generated_name_mapping),
            WorkspaceAPIProcessor(generated_name_mapping),
            GatewayAPIProcessor(generated_name_mapping),
            ConnectionAPIProcessor(generated_name_mapping),
            DomainsAPIProcessor(generated_name_mapping),
            SubscriptionsAPIProcessor(generated_name_mapping),
        ]

    def handle_request(self, request):
        for handler in self._api_handlers:
            if handler.try_process_request(request):
                break

    def handle_response(self, request, response):
        for handler in self._api_handlers:
            if handler.try_process_response(request, response):
                break
