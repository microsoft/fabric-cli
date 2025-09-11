# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace, context: Item) -> None:
    # Both enabled and disabled cannot be provided
    if args.enable and not (args.disable):
        raise FabricCLIError(
            "You must specify one of --enable --disable",
            fab_constant.ERROR_INVALID_INPUT,
        )

    # Get the existing job schedule information to update
    response = jobs_api.get_item_schedule(args)
    if response.status_code == 200:
        content = json.loads(response.text)

        # If the configuration is not provided then we only need to update the enabled key
        if not args.configuration:
            if args.enable != args.disable:
                raise FabricCLIError(
                    "You must specify one of --enable --disable",
                    fab_constant.ERROR_INVALID_INPUT,
                )
            _configuration = content["configuration"]
            payload = json.dumps(
                {"configuration": _configuration, "enabled": args.enable}
            )
        else:
            # If not enabled or disabled is provided, get the existing configuration
            if not args.enable and args.disable:
                args.enable = content["enabled"]

            _configuration = json.loads(args.configuration)
            if "enabled" in _configuration and "configuration" in _configuration:
                payload = args.configuration
            else:
                payload = json.dumps(
                    {"configuration": _configuration, "enabled": args.enable}
                )

        response = jobs_api.update_item_schedule(args, payload)

        if response.status_code == 200:
            content = json.loads(response.text)
            instance_id = content["id"]
            fab_ui.print_output_format(
                args, message=f"Job schedule {instance_id} updated"
            )
