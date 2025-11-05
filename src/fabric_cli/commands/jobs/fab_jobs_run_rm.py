# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace, context: Item) -> None:
    if args.force or utils_ui.prompt_confirm():
        response = jobs_api.remove_item_schedule(args)

        if response.status_code == 200:
            utils_ui.print_output_format(
                args,
                message=f"Job schedule {args.schedule_id} removed",
            )
        else:
            try:
                content = json.loads(response.text)
                error_message = content.get("error", {}).get("message", "")
            except json.JSONDecodeError:
                error_message = response.text

            raise FabricCLIError(
                f"Failed to remove job schedule {args.schedule_id}: {error_message}",
                fab_constant.ERROR_API_FAILURE,
            )