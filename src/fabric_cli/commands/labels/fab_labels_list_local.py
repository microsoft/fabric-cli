# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace) -> None:
    try:
        with open(args.input, "r") as file:
            data = json.load(file)
    except json.decoder.JSONDecodeError:
        raise FabricCLIError(
            ErrorMessages.Common.invalid_json_format(), fab_constant.ERROR_INVALID_JSON
        )
    except Exception:
        raise FabricCLIError(
            ErrorMessages.Common.file_or_directory_not_exists(),
            fab_constant.ERROR_INVALID_PATH,
        )

    try:
        utils_ui.print_output_format(args, text_style=TextFormatStyle.UNIX, data=data["labels"])
    except Exception:
        raise FabricCLIError(
            ErrorMessages.Labels.invalid_entries_format(),
            fab_constant.ERROR_INVALID_ENTRIES_FORMAT,
        )
