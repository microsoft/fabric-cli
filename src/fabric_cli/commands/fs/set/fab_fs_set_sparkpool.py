# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_sparkpool as sparkpool_api
from fabric_cli.commands.fs.get import fab_fs_get_sparkpool as get_sparkpool
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(virtual_item: VirtualItem, args: Namespace) -> None:
    query = args.query

    utils_set.validate_query_not_in_blocklist(query)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        vi_spark_pool_def = get_sparkpool.exec(virtual_item, args, verbose=False)

        updated_def = utils_set.update_fabric_element(
            vi_spark_pool_def, query, args.input
        )

        def _prep_for_updated_def(data):
            data.pop("id", None)  # Remove 'id' if it exists
            data.pop("type", None)  # Remove 'type' if it exists
            return json.dumps(data)

        spark_pool_update_def = _prep_for_updated_def(updated_def)

        args.ws_id = virtual_item.workspace.id
        args.id = virtual_item.id
        utils_ui.print_grey(f"Setting new property for '{virtual_item.name}'...")
        response = sparkpool_api.update_spark_pool(args, spark_pool_update_def)

        if response.status_code == 200:
            utils_set.update_cache(
                updated_def,
                virtual_item,
                utils_mem_store.upsert_spark_pool_to_cache,
                element_name_key="name",
            )

            utils_ui.print_output_format(args, message="Spark Pool updated")
