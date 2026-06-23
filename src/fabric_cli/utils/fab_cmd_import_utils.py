# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
import os
import time
from argparse import Namespace
from typing import Any, Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_ui as utils_ui


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
    # Sort dirs and files to ensure deterministic ordering across platforms
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for file in sorted(files):
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


# Environments


def check_environment_publish_ready(args: Namespace) -> None:
    """Check if environment is ready for import (no publish in progress).

    Before modifying any Environment definitions, we check the current publish
    state. This ensures we don't attempt to import new definitions while a
    previous publish is still in progress.
    """
    _wait_for_environment_publish_state(
        args,
        pass_states=["success", "failed", "cancelled"],
        fail_states=[],
        message_prefix="Existing Environment publish is in progress",
    )


def trigger_environment_publish(args: Namespace) -> None:
    """Trigger environment publish after definition import.

    Immediately after import, call the Environment-specific publish API
    to start the async library publishing.
    """
    item_api.environment_publish(args)
    utils_ui.print_info("Environment publish triggered")


def wait_for_environment_publish(args: Namespace) -> None:
    """Wait for environment publish to complete.

    Poll the GET Environment publish details API until the environment
    reaches a success or failure state, with retries as needed.
    """
    _wait_for_environment_publish_state(
        args,
        pass_states=["success"],
        fail_states=["failed", "cancelled"],
        message_prefix="Environment publish in progress",
    )
    utils_ui.print_info("Environment publish completed")


def _wait_for_environment_publish_state(
    args: Namespace,
    pass_states: list[str],
    fail_states: list[str],
    message_prefix: str,
) -> None:
    """Wait for environment to reach the published state."""
    publishing = True
    iteration = 1
    max_retries = 60

    while publishing:
        response = item_api.environment_get_publish_details(args)
        data = response.json()

        current_state = (
            data.get("properties", {})
            .get("publishDetails", {})
            .get("state", "Unknown")
            .lower()
        )

        if current_state in pass_states:
            publishing = False
        elif current_state in fail_states:
            msg = f"Environment publish {current_state}"
            raise FabricCLIError(msg, fab_constant.ERROR_UNEXPECTED_ERROR)
        else:
            _handle_retry(
                attempt=iteration,
                base_delay=5,
                max_retries=max_retries,
                prepend_message=message_prefix,
            )
            iteration += 1


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
