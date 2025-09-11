# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.core import fab_constant, fab_logger, fab_state_config
from fabric_cli.utils import fab_ui as utils_ui


def read_labels_definition(args: Namespace) -> bool:
    args.input = fab_state_config.get_config(fab_constant.FAB_LOCAL_DEFINITION_LABELS)
    if not args.input:
        fab_logger.log_warning("Label definitions for CLI not set")
        utils_ui.print_grey("→ Run 'config set local_definition_labels <json_path>'")
        return False
    return True


def get_label_id_by_name(args: Namespace) -> str | None:
    with open(args.input, "r") as file:
        data = json.load(file)

    for label in data.get("labels", []):
        if label.get("name") == args.name:
            return label.get("id")

    return None
