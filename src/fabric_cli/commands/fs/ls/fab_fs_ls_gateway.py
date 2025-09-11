# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.client import fab_api_gateway as gateway_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspace
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vws: VirtualWorkspace, args, show_details):
    _base_cols = ["name", "id"]
    _details_cols = ["type", "capacityId", "numberOfMemberGateways", "version"]
    gateways = utils_mem_store.get_gateways(vws.tenant)
    sorted_gateways = utils_ls.sort_elements(
        [{"name": g.name, "id": g.id, "displayName": g.short_name} for g in gateways]
    )

    if show_details:
        fab_response = gateway_api.list_gateways(args)
        if fab_response.status_code in {200, 201}:
            _gateways: list = json.loads(fab_response.text)["value"]
            for gateway in sorted_gateways:
                gateway_details: dict[str, str] = next(
                    (c for c in _gateways if c["id"] == gateway["id"]), {}
                )
                for col in _details_cols:
                    gateway[col] = gateway_details.get(col, "Unknown")

    columns = _base_cols + _details_cols if show_details else ["name"]

    utils_ls.format_and_print_output(
        data=sorted_gateways,
        columns=columns,
        args=args,
        show_details=show_details
    )
