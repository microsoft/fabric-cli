# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Dict

from fabric_cli.client import fab_api_sparkpool as sparkpool_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def exec(spark_pool: VirtualItem, args: Namespace) -> None:
    # Params
    optional_params = [
        "autoScale.maxNodeCount",
        "autoScale.minNodeCount",
        "nodeSize",
    ]
    if mkdir_utils.show_params_desc(
        args.params, spark_pool.item_type, optional_params=optional_params
    ):
        return

    # For autoscale, if only minNodeCount is provided, disable autoscale
    # If maxNodeCount is provided, enable autoscale

    payload: Dict = {
        "name": f"{spark_pool.short_name}",
        "nodeFamily": "MemoryOptimized",
        "nodeSize": "Small",
        "autoScale": {"enabled": True, "minNodeCount": 1, "maxNodeCount": 1},
        "dynamicExecutorAllocation": {
            "enabled": False,
            "minExecutors": 1,
            "maxExecutors": 1,
        },
    }

    # Remove all unwanted keys from the params
    utils.remove_keys_from_dict(args.params, ["displayName"])

    # Lowercase params and validate
    params = args.params
    mkdir_utils.validate_spark_pool_params(params)

    try:
        if params.get("autoscale.minnodecount") or params.get("autoscale.maxnodecount"):
            payload["autoScale"]["enabled"] = False

            if params.get("autoscale.minnodecount"):
                payload["autoScale"]["minNodeCount"] = int(
                    params.get("autoscale.minnodecount")
                )
            else:
                payload["autoScale"]["minNodeCount"] = 1

            if params.get("autoscale.maxnodecount"):
                payload["autoScale"]["enabled"] = True
                payload["autoScale"]["maxNodeCount"] = int(
                    params.get("autoscale.maxnodecount")
                )
            else:
                payload["autoScale"]["maxNodeCount"] = payload["autoScale"][
                    "minNodeCount"
                ]
    except Exception as e:
        raise FabricCLIError(
            f"Invalid parameter values: {e}", fab_constant.ERROR_INVALID_INPUT
        )

    if params.get("nodesize"):
        payload["nodeSize"] = params.get("nodesize").lower()

    json_payload = json.dumps(payload)
    args.ws_id = spark_pool.workspace.id

    utils_ui.print_grey(f"Creating a new Spark Pool...")
    response = sparkpool_api.create_spark_pool(args, payload=json_payload)
    if response.status_code in (200, 201):
        utils_ui.print_output_format(args, message=f"'{spark_pool.name}' created")

        data = json.loads(response.text)
        spark_pool._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_spark_pool_to_cache(spark_pool)
