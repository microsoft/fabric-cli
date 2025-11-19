# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json

from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors.common import CommonErrors
from fabric_cli.utils import fab_jmespath as utils_jmespath


def validate_item_query(query_value: str) -> None:
    """Validate that a query string is allowed for item metadata modification.

    Args:
        query_value: Query string to validate. Must be an allowed metadata key,
            or start with "definition." or "properties.".

    Raises:
        FabricCLIError: If the query is not in an allowed format.
    """
    if not (
        query_value in fab_constant.ITEM_SET_ALLOWED_METADATA_KEYS
        or query_value == fab_constant.ITEM_QUERY_DEFINITION
        or query_value.startswith(f"{fab_constant.ITEM_QUERY_DEFINITION}.")
        or query_value.startswith(f"{fab_constant.ITEM_QUERY_PROPERTIES}.")
    ):
        raise FabricCLIError(
            CommonErrors.invalid_item_set_query(query_value),
            fab_constant.ERROR_INVALID_QUERY,
        )


def validate_expression(expression: str, allowed_keys: list[str]) -> None:
    if not any(
        expression == key or expression.startswith(f"{key}.") for key in allowed_keys
    ):
        allowed_expressions = "\n  ".join(allowed_keys)
        raise FabricCLIError(
            f"Invalid query '{expression}'\n\nAvailable queries:\n  {allowed_expressions}",
            fab_constant.ERROR_INVALID_INPUT,
        )


def ensure_notebook_dependency(decoded_item_def: dict, query: str) -> dict:
    dependency_types = ["lakehouse", "warehouse", "environment"]

    for dep in dependency_types:
        if f"dependencies.{dep}" in query:
            metadata = decoded_item_def["definition"]["parts"][0]["payload"].get(
                "metadata", {}
            )
            metadata.setdefault("dependencies", {}).setdefault(dep, {})
            decoded_item_def["definition"]["parts"][0]["payload"]["metadata"] = metadata

    return decoded_item_def


def update_fabric_element(
    resource_def: dict,
    query: str,
    input: str,
    decode_encode: bool = False,
) -> tuple[str, dict]:
    """Update a Fabric resource element using a JMESPath query.

    Args:
        resource_def: Resource definition dictionary to modify.
        query: JMESPath expression specifying the path to update.
        input: New value to set.
        decode_encode: If True, decode/encode base64 payloads. Default False.

    Returns:
        Tuple of (json_payload, updated_def) where json_payload is the JSON string
        and updated_def is the updated dictionary.
    """
    try:
        input = json.loads(input)
    except (TypeError, json.JSONDecodeError):
        # If it's not a JSON string, keep it as is
        pass

    # Decode > replace > encode
    if decode_encode:
        decoded_item_def = _decode_payload(resource_def)
        decoded_item_def = ensure_notebook_dependency(decoded_item_def, query)
        updated_item_def = utils_jmespath.replace(decoded_item_def, query, input)
        updated_def = _encode_payload(updated_item_def)
        json_payload = json.dumps(updated_def)
    else:
        updated_def = utils_jmespath.replace(resource_def, query, input)
        json_payload = json.dumps(updated_def)

    return json_payload, updated_def


def print_set_warning() -> None:
    fab_logger.log_warning("Modifying properties may lead to unintended consequences")


def extract_json_schema(schema: dict, definition: bool = True) -> tuple:
    name_description_properties = {
        "displayName": schema.get("displayName", ""),
        "description": schema.get("description", ""),
    }

    definition_properties = None

    if definition:
        definition_properties = {"definition": schema.get("definition", {})}

    return definition_properties, name_description_properties


def extract_updated_properties(updated_data: dict, query_path: str) -> dict:
    result = {}
    top_level_key = query_path.split(".")[0]

    if top_level_key in updated_data:
        result[top_level_key] = updated_data[top_level_key]

    return result


def _encode_payload(item_def: dict) -> dict:
    is_ipynb = False

    # Check if item_def has the required structure
    if "definition" in item_def and "parts" in item_def["definition"]:
        for part in item_def["definition"]["parts"]:
            # Check if the part has a payload that needs encoding
            if "payload" in part:
                payload = part["payload"]
                path = part.get("path", "")

                # Only encode if the path ends with .json or .ipynb

                if path.endswith(".ipynb"):
                    is_ipynb = True

                if isinstance(payload, dict):
                    # Convert the payload to a JSON string
                    payload_json = json.dumps(payload)
                    # Encode the JSON string into Base64
                    encoded_payload = base64.b64encode(
                        payload_json.encode("utf-8")
                    ).decode("utf-8")
                    part["payload"] = encoded_payload
                    part["payloadType"] = "InlineBase64"

                elif isinstance(payload, str):
                    # If payload is a string, encode it directly to Base64
                    encoded_payload = base64.b64encode(payload.encode("utf-8")).decode(
                        "utf-8"
                    )
                    part["payload"] = encoded_payload
                    part["payloadType"] = "InlineBase64"

            # Recursively check for nested parts if applicable
            if "nested_parts" in part:
                _encode_payload(part["nested_parts"])

    if is_ipynb:
        item_def["definition"]["format"] = "ipynb"

    return item_def


def _decode_payload(item_def: dict) -> dict:
    # Check if item_def has the required structure
    if "definition" in item_def and "parts" in item_def["definition"]:
        for part in item_def["definition"]["parts"]:
            # Check if the part has a payload that needs decoding
            if "payload" in part:
                payload_base64 = part["payload"]

                if payload_base64:
                    decoded_payload = base64.b64decode(payload_base64).decode("utf-8")
                    decoded_payload = json.loads(decoded_payload)
                    # Store the decoded payload
                    part["payload"] = decoded_payload
                    part["payloadType"] = "DecodeBase64"

            # Recursively check for nested parts if applicable
            if (
                "nested_parts" in part
            ):  # Assuming 'nested_parts' is a key for potential nested structures
                _decode_payload(part)

    return item_def
