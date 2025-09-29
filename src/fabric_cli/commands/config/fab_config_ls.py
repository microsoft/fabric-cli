# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls


def exec_command(args: Namespace) -> None:
    configs = fab_state_config.list_configs()

    all_configs = [
        {"setting": key, "value": configs.get(key, "")}
        for key in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES
    ]

    columns = ["setting", "value"]
    utils_ls.format_and_print_output(
        data=all_configs,
        columns=columns,
        args=args,
        show_details=True,
    )
