# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import re
from argparse import Namespace
from xml.sax.saxutils import escape

from fabric_cli.core import fab_constant
from fabric_cli.errors import ErrorMessages
from fabric_cli.core.fab_exceptions import FabricCLIError


def parse_json(args: Namespace) -> None:
    """Helper function to parse the --input argument into a correct json format"""
    # Normalize the content array to a single string without quotes
    normalized_content = " ".join(args.input).strip("\"'")

    # Override ' for " to make it a valid JSON
    try:
        target_json = json.loads(normalized_content.replace("'", '"'))

        args.target_json = json.dumps(target_json)
        args.input = None
    except json.JSONDecodeError:
        raise FabricCLIError(
            ErrorMessages.Common.invalid_json_format(), fab_constant.ERROR_INVALID_JSON
        )


def validate_shortcut_name(name: str) -> None:
    invalid_chars = r"[\"\\:|<>*?.%+]"
    if re.search(invalid_chars, name):
        raise FabricCLIError(
            f"Invalid shortcut name. The name should not include any of the following characters: {escape(invalid_chars)}",
            fab_constant.ERROR_INVALID_PATH,
        )
