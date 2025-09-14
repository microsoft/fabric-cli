# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
import os

from fabric_cli.utils import fab_storage as utils_storage


def decode_payload(item_def: dict) -> dict:
    # Check if item_def has the required structure
    if "definition" in item_def and "parts" in item_def["definition"]:
        for part in item_def["definition"]["parts"]:

            # Check if the part has a payload that needs decoding
            if "payload" in part:
                payload_base64 = part["payload"]

                if payload_base64:
                    path = part.get("path", "")

                    try:
                        decoded_bytes = base64.b64decode(payload_base64)

                        try:
                            decoded_payload = decoded_bytes.decode("utf-8")

                            # If it's a JSON file, parse it
                            if path.endswith(
                                (".json", ".ipynb", ".pbir", ".platform", ".pbism")
                            ):
                                decoded_payload = json.loads(decoded_payload)
                        except UnicodeDecodeError:
                            # If it's binary, store the raw bytes
                            decoded_payload = decoded_bytes  # type: ignore[assignment]

                        part["payload"] = decoded_payload
                        part["payloadType"] = "DecodeBase64"

                    except Exception as e:
                        part["error"] = f"Decoding error: {e}"

            # Recursively check for nested parts if applicable
            if (
                "nested_parts" in part
            ):  # Assuming 'nested_parts' is a key for potential nested structures
                decode_payload(part)

    return item_def


def export_json_parts(args, definition: dict, export_path: dict) -> None:
    """
    Export each 'payload' in the 'parts' array to a file named based on 'path' in 'parts'.
    The 'payload' content will be saved as the file's content.
    """
    original_path = export_path["path"]

    if export_path["type"] == "local":
        if not os.path.exists(original_path):
            os.makedirs(original_path)

    parts = definition.get("parts", [])
    for part in parts:
        path = part.get("path", "").lstrip(
            "/"
        )  # Strip leading slashes to make a valid file name
        payload = part.get("payload", {})
        export_path["path"] = os.path.join(original_path, path)
        utils_storage.write_to_storage(args, export_path, payload, export=True)


def clean_notebook_cells(ntbk_json: dict, tags_to_clean: list) -> dict:
    if (
        "definition" in ntbk_json
        and "parts" in ntbk_json["definition"]
        and len(ntbk_json["definition"]["parts"]) > 0
        and "payload" in ntbk_json["definition"]["parts"][0]
        and "cells" in ntbk_json["definition"]["parts"][0]["payload"]
    ):
        for cell in ntbk_json["definition"]["parts"][0]["payload"]["cells"]:
            for tag in tags_to_clean:
                if tag in cell:
                    cell[tag] = []

    return ntbk_json
