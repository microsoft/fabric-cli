# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_job_utils as utils_job
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace, item: Item) -> None:

    fab_ui.print_grey(
        f"Cancelling job instance for item {item.path} with id: '{args.id}'..."
    )
    args.instance_id = args.id
    response = jobs_api.cancel_item_job_instance(args)

    if response.status_code == 202:
        if args.wait:
            utils_job.wait_for_job_completion(
                args,
                args.id,
                response,
                custom_polling_interval=None
            )
        else:
            fab_ui.print_output_format(
                args, message=f"Job instance '{args.id}' cancelled (async)"
            )
            fab_ui.print_grey(
                f"→ To see status run 'job run-status {item.path} --id {args.id}'"
            )
