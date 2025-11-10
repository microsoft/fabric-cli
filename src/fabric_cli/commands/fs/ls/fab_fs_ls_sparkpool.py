# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItemContainer
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vic: VirtualItemContainer, args, show_details):
    spark_pools = utils_mem_store.get_spark_pools(vic)

    if spark_pools:
        sorted_spark_pools = utils_ls.sort_elements(
            [{"name": sp.name, "id": sp.id} for sp in spark_pools]
        )
        base_cols = ["name"]

        if show_details:
            sp_detail_cols = [
                "id",
                "nodeFamily",
                "nodeSize",
                "type",
                "autoScale",
                "dynamicExecutorAllocation",
            ]
            response = workspace_api.ls_workspace_spark_pools(args, vic.workspace.id)
            if response.status_code in {200, 201}:
                _spark_pools: list = json.loads(response.text)["value"]
                for spark_pool in sorted_spark_pools:
                    sp_details: dict[str, str] = next(
                        (c for c in _spark_pools if c["id"] == spark_pool["id"]), {}
                    )
                    for col in sp_detail_cols:
                        spark_pool[col] = sp_details.get(col, "Unknown")

        columns = base_cols + sp_detail_cols if show_details else base_cols

        utils_ls.format_and_print_output(
            data=sorted_spark_pools,
            columns=columns,
            args=args,
            text_style=TextFormatStyle.UNIX
        )
