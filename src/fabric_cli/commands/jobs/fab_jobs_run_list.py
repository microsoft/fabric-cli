# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace, context: Item) -> None:
    if args.schedule:
        response = jobs_api.list_item_schedules(args)
    else:
        response = jobs_api.list_item_runs(args)

    if response.status_code == 200:
        data = json.loads(response.text)

        if data["value"]:
            _keys = (
                data["value"][0].keys()
                if isinstance(data["value"], list)
                else data["value"].keys()
            )

            utils_ls.format_and_print_output(
                data=data["value"],
                columns=_keys,
                args=args,
                text_style=TextFormatStyle.UNIX,
            )
        else:
            message = "No schedules found" if args.schedule else "No runs found"
            fab_ui.print_output_format(args, message=message)
