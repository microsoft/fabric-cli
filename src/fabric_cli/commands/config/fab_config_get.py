# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace) -> None:
    key = fab_state_config.normalize_config_key(args.key.lower())
    if key not in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
        raise FabricCLIError(
            ErrorMessages.Config.unknown_configuration_key(key),
            fab_constant.ERROR_INVALID_INPUT,
        )
    else:
        value = fab_state_config.get_config(key)
        if value:
            utils_ui.print_output_format(args, data=value)
