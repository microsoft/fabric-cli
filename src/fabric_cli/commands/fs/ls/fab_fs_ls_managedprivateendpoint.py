# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItemContainer
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vic: VirtualItemContainer, args, show_details):
    mngd_pvt_endpoints = utils_mem_store.get_managed_private_endpoints(vic)

    if mngd_pvt_endpoints:
        sorted_managed_private_endpoints = utils_ls.sort_elements(
            [{"name": mpe.name, "id": mpe.id} for mpe in mngd_pvt_endpoints]
        )
        base_cols = ["name"]
        if show_details:
            mpe_detail_cols = [
                "id",
                "connectionState",
                "provisioningState",
                "targetPrivateLinkResourceId",
                "targetSubresourceType",
            ]

            args.ws_id = vic.workspace.id
            response = workspace_api.ls_workspace_managed_private_endpoints(args)
            if response.status_code in {200, 201}:
                _managed_private_endpoints: list = json.loads(response.text)["value"]
                for managed_private_endpoint in sorted_managed_private_endpoints:
                    mpe_details: dict[str, str] = next(
                        (
                            c
                            for c in _managed_private_endpoints
                            if c["id"] == managed_private_endpoint["id"]
                        ),
                        {},
                    )
                    for col in mpe_detail_cols:
                        managed_private_endpoint[col] = mpe_details.get(col, "Unknown")

        columns = base_cols + mpe_detail_cols if show_details else base_cols

        utils_ls.format_and_print_output(
            data=sorted_managed_private_endpoints,
            columns=columns,
            args=args,
            show_details=show_details
        )
