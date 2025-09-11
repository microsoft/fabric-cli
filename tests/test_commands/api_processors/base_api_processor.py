# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod


class BaseAPIProcessor(ABC):
    @abstractmethod
    def try_process_request(
        self,
        request,
    ) -> bool:
        pass

    @abstractmethod
    def try_process_response(self, request, response) -> bool:
        pass
