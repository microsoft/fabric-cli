# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
import os
from typing import Any, Optional

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import Item


def get_payload_for_item_type(
    path: str, item: Item, input_format: Optional[str] = None
) -> dict:
    definition = _build_definition(path, input_format)
    return {
        "type": str(item.item_type),
        "folderId": item.folder_id,
        "displayName": item.short_name,
        "definition": definition,
    }


def _build_definition(input_path: Any, input_format: Optional[str] = None) -> dict:
    directory = input_path
    parts = []

    # Recursively traverses the directory and builds the payload structure
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get full path and relative path
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, directory)

            if "definition.pbir" in full_path:
                with open(full_path, "rb") as file:
                    data = json.load(file)

                if data.get("datasetReference", {}).get("byPath") is not None:
                    raise FabricCLIError(
                        "Definition includes byPath; switch to byConnection before importing",
                        fab_constant.ERROR_INVALID_DEFINITION_PAYLOAD,
                    )

            if "cache.abf" in full_path:
                continue

            # Encode the file content to base64
            encoded_content = _encode_file_to_base64(full_path)

            # Add file data to parts
            parts.append(
                {
                    "path": relative_path.replace(
                        "\\", "/"
                    ),  # Ensure cross-platform path formatting
                    "payload": encoded_content,
                    "payloadType": "InlineBase64",
                }
            )

    definition: dict = {"parts": parts}
    if input_format:
        definition["format"] = input_format
    return definition


def _encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")
