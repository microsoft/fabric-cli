# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
import os
import time
from argparse import Namespace
from typing import Any, Optional

import yaml

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_ui as utils_ui


def get_payload_for_item_type(
    path: str, item: Item, input_format: Optional[str] = None
) -> dict:
    # Environment does not support updateDefinition yet, custom payload / dev
    if item.item_type == ItemType.ENVIRONMENT:
        return _build_environment_payload(path)
    else:
        base64_definition = _build_payload(path)
        return item.get_payload(base64_definition, input_format)


def _build_payload(input_path: Any) -> dict:
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

    # Create the final JSON structure
    payload_structure = {"parts": parts}
    return payload_structure


def _encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


# Environments


def publish_environment_item(args: Namespace, payload: dict) -> None:
    # Check for ongoing publish
    _check_environment_publish_state(args, True)

    # Update compute settings
    _update_compute_settings(args, payload)

    # Add libraries to environment, overwriting anything with the same name and return the list of libraries
    _add_libraries(args, payload)

    # Remove libraries from live environment
    _remove_libraries(args, payload)

    # Publish
    item_api.environment_publish(args)

    # Wait for ongoing publish to complete
    _check_environment_publish_state(args)

    utils_ui.print_info(f"Published")


def _check_environment_publish_state(
    args: Namespace, initial_check: bool = False
) -> None:
    publishing = True
    iteration = 1

    while publishing:
        args.item_uri = "environments"
        response = item_api.get_item(args, item_uri=True)
        data = response.json()

        current_state = (
            data.get("properties", {})
            .get("publishDetails", {})
            .get("state", "Unknown")
            .lower()
        )

        if initial_check:

            prepend_message = "Existing Environment publish is in progess"
            pass_values = ["success", "failed", "cancelled"]
            fail_values = []

        else:
            prepend_message = "Operation in progress"
            pass_values = ["success"]
            fail_values = ["failed", "cancelled"]

        if current_state in pass_values:
            publishing = False
        elif current_state in fail_values:
            msg = f"Publish {current_state} for Libraries"
            raise Exception(msg)
        else:
            _handle_retry(
                attempt=iteration,
                base_delay=5,
                max_retries=20,
                response_retry_after=120,
                prepend_message=prepend_message,
            )
            iteration += 1


def _build_environment_payload(input_path: Any) -> dict:
    directory = input_path

    parts: dict[Any, Any] = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get full path and relative path
            full_path = os.path.join(root, file)

            # Spark compute settings
            if "Setting" in full_path:
                with open(full_path, "r") as file:
                    yaml_body = yaml.safe_load(file)
                parts["sparkCompute"] = _convert_environment_compute_to_camel(yaml_body)

            # Spark libraries
            elif "Libraries" in full_path:
                parts["libraries"] = parts.get("libraries", [])
                # Append instead of overwrite
                parts["libraries"].append(full_path)

    return {"parts": parts}


def _convert_environment_compute_to_camel(input_dict: dict) -> dict:
    new_input_dict = {}

    for key, value in input_dict.items():
        if key == "spark_conf":
            new_key = "sparkProperties"
        else:
            # Convert the key to camelCase
            key_components = key.split("_")
            # Capitalize the first letter of each component except the first one
            new_key = key_components[0] + "".join(x.title() for x in key_components[1:])

        # Recursively update dictionary values if they are dictionaries
        if isinstance(value, dict):
            value = _convert_environment_compute_to_camel(value)

        new_input_dict[new_key] = value

    return new_input_dict


def _update_compute_settings(args: Namespace, payload: dict) -> None:
    if "sparkCompute" in payload["parts"]:
        spark_compute = payload["parts"]["sparkCompute"]
        _spark_compute_payload = json.dumps(spark_compute)

        args.ext_uri = "/staging/sparkcompute"
        args.item_uri = "environments"

        response = item_api.update_item(
            args, payload=_spark_compute_payload, item_uri=True, ext_uri=True
        )

        if response.status_code == 200:
            utils_ui.print_info("Updated Spark Settings")


def _add_libraries(args: Namespace, payload: dict) -> None:
    if "libraries" in payload["parts"]:
        # Extract the list of libraries
        library_paths = payload["parts"]["libraries"]

        for file_path in library_paths:
            file_name = os.path.basename(file_path)

            # Open the file in binary mode for reading
            with open(file_path, "rb") as file:
                library_file = {"file": (file_name, file)}

                # Upload libraries to the environment
                response = item_api.environment_upload_staging_library(
                    args, library_file
                )

                if response.status_code == 200:
                    utils_ui.print_info(f"Updated Library '{file_name}'")


def _remove_libraries(args: Namespace, payload: dict) -> None:
    args.ext_uri = "/libraries"
    args.item_uri = "environments"

    try:
        response = item_api.get_item(args, item_uri=True, ext_uri=True)
        if response.status_code == 200:
            response_json = response.json()  # Convert to dictionary

            repo_library_files = tuple(
                os.path.basename(file) for file in payload["parts"]["libraries"]
            )

            if (
                "environmentYml" in response_json
                and response_json["environmentYml"]  # Not None or ''
                and "environment.yml" not in repo_library_files
            ):
                _remove_library(args, "environment.yml")

            custom_libraries = response_json.get("customLibraries", {})
            if isinstance(custom_libraries, dict):
                for files in custom_libraries.values():
                    if isinstance(files, list):
                        for file in files:
                            if file not in repo_library_files:
                                _remove_library(args, file)

    except Exception as e:
        pass


def _remove_library(args: Namespace, file_name: str) -> None:
    item_api.environment_delete_library_staging(args, file_name)
    utils_ui.print_info(f"Removed {file_name}")


def _handle_retry(
    attempt: int,
    base_delay: float,
    max_retries: int,
    response_retry_after: float = 60,
    prepend_message: str = "",
) -> None:
    if attempt < max_retries:
        retry_after = float(response_retry_after)
        base_delay = float(base_delay)
        delay = min(retry_after, base_delay * (2**attempt))

        # Modify output for proper plurality and formatting
        delay_str = f"{delay:.0f}" if delay.is_integer() else f"{delay:.2f}"
        second_str = "second" if delay == 1 else "seconds"
        prepend_message += " " if prepend_message else ""

        utils_ui.print_progress(
            f"{prepend_message}Checking again in {delay_str} {second_str} (Attempt {attempt}/{max_retries})..."
        )
        time.sleep(delay)
    else:
        msg = f"Maximum retry attempts ({max_retries}) exceeded"
        raise Exception(msg)
