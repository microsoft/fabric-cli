# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from pathlib import Path
from typing import Optional

from fabric_cli.commands.api import fab_api_request as api_request
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_util as utils


@handle_exceptions()
@set_command_context()
def request_command(args: Namespace) -> None:
    args.headers = utils.process_nargs(args.headers)
    args.params = utils.process_nargs(args.params)
    args.endpoint = utils.process_nargs(args.endpoint)

    _parse_config_args(args)
    _build_query_parameters(args)
    _build_headers(args)
    api_request.exec_command(args)


# Utils
def _build_key_value_pairs(
    input_str: Optional[str], error_message: str
) -> dict[str, str]:
    result = {}
    if input_str:
        try:
            for pair in input_str.split(","):
                key, value = map(str.strip, pair.split("=", 1))
                result[key] = value
        except ValueError:
            raise FabricCLIError(error_message, fab_constant.ERROR_INVALID_INPUT)
    return result


def _build_query_parameters(args: Namespace) -> None:
    args.request_params = _build_key_value_pairs(
        args.params,
        "Invalid format for query parameters. Use key=value pairs separated by commas.",
    )


def _build_headers(args: Namespace) -> None:
    args.headers = _build_key_value_pairs(
        args.headers,
        "Invalid format for headers. Use key=value pairs separated by commas.",
    )


def _parse_config_args(args: Namespace) -> None:
    # Helper function to parse the execution data into a correct json format
    if not args.input:
        args.file_path = None
        return

    configuration = None
    file_path = None
    # Normalize the content array to a single string without quotes
    normalized_content = " ".join(args.input).strip("\"'")

    if normalized_content.startswith("{") and normalized_content.endswith("}"):
        configuration = json.loads(normalized_content)
    else:
        # Validate that the content is a valid file path
        try:
            path = Path(normalized_content)
            if path.exists() and path.is_file():
                if path.suffix == ".json":
                    with open(normalized_content, "r") as f:
                        configuration = json.load(f)
                else:
                    file_path = normalized_content
        except Exception as e:
            raise FabricCLIError(
                ErrorMessages.Common.invalid_json_content(normalized_content, str(e)),
                fab_constant.ERROR_INVALID_JSON,
            )
    args.input = configuration
    args.file_path = file_path
