# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Separate module for API types to avoid circular imports.
This module contains shared types used across the client modules.
"""

import json

from requests.structures import CaseInsensitiveDict

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages


class ApiResponse:
    def __init__(
        self,
        status_code: int,
        text: str,
        content: bytes,
        headers: CaseInsensitiveDict[str],
    ):
        self.status_code = status_code
        self.text = text
        self.headers = headers
        self.content = content

    def append_text(self, text: str, total_pages: int = 0):
        try:
            original_text = json.loads(self.text)
            new_text = json.loads(text)

            for key, value in original_text.items():
                if isinstance(value, list) and key in new_text:
                    original_text[key].extend(new_text[key])

            original_text.pop("continuationToken", None)
            original_text.pop("continuationUri", None)
            original_text["total_pages"] = total_pages + 1

            self.text = json.dumps(original_text)
        except json.JSONDecodeError as e:
            raise FabricCLIError(
                ErrorMessages.Common.json_decode_error(str(e)),
                fab_constant.ERROR_INVALID_JSON,
            )

    def json(self):
        return json.loads(self.text)
