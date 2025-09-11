# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace, context: Item) -> None:
    if args.schedule:
        args.schedule_id = args.id
        response = jobs_api.get_item_schedule(args)
    else:
        args.instance_id = args.id
        response = jobs_api.get_item_job_instance(args)

    if response.status_code == 200:
        content = json.loads(response.text)
        fab_ui.print_output_format(args, data=content, show_headers=True)
