# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_get_utils as utils_get
from fabric_cli.utils import fab_item_util as item_utils


def exec(
    item: Item,
    args: Namespace,
    verbose: bool = True,
    decode: Optional[bool] = True,
) -> dict:
    # Determine if we need to obtain definition based on query
    obtain_definition = utils_get.should_retrieve_definition(args.query)

    item_def = item_utils.get_item_with_definition(
        item, args, decode, obtain_definition
    )

    # Connections
    try:
        args.ws_id = item.workspace.id
        args.id = item.id
        connections = item_api.get_item_connections(args)

        connections_def = json.loads(connections.text)
        item_def["connections"] = connections_def["value"]
    except Exception:
        pass

    # Schedules
    try:
        args.item_id = item.id
        args.jobType = item.job_type.value

        if args.jobType is not None:
            schedules = jobs_api.list_item_schedules(args)

            if schedules.status_code == 200:
                schedules_def = json.loads(schedules.text)
                item_def["schedules"] = schedules_def["value"]
    except Exception:
        pass

    # Environment
    if item.item_type == ItemType.ENVIRONMENT:
        try:
            item_def = utils_get.get_environment_metadata(item_def, args)
        except Exception:
            pass

    # Mirrored Database
    if item.item_type == ItemType.MIRRORED_DATABASE:
        try:
            item_def = utils_get.get_mirroreddb_metadata(item_def, args)
        except Exception:
            pass

    utils_get.query_and_export(item_def, args, item.full_name, verbose)

    return item_def
