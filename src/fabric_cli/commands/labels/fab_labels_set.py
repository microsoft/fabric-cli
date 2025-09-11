# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_labels as api_labels
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Item
from fabric_cli.utils import fab_cmd_label_utils as utils_label
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace, context: FabricElement) -> None:
    if isinstance(context, Item):
        _set_label_item(context, args)


def _set_label_item(item: Item, args: Namespace) -> None:
    if args.force or utils_ui.prompt_confirm():
        item_id = item.id
        item_type = item.item_type.value
        label_id = utils_label.get_label_id_by_name(args)

        if label_id is None:
            raise FabricCLIError(
                f"Id not found for label '{args.name}'",
                fab_constant.ERROR_INVALID_INPUT,
            )

        payload = json.dumps(
            {
                "items": [{"id": item_id, "type": item_type}],
                "labelId": label_id,
                "assignmentMethod": "Standard",
            }
        )

        utils_ui.print_grey(f"Setting '{args.name}' label...")
        response = api_labels.set_sensi_labels(args, payload)

        if response.status_code == 403:
            raise FabricCLIError(
                f"Not sufficient permissions to perform this operation",
                fab_constant.ERROR_FORBIDDEN,
            )
        elif response.status_code == 200:
            utils_ui.print_output_format(args, message="Label set")
