# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_azure as azure_api
from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspace
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vws: VirtualWorkspace, args, show_details):
    capacities = utils_mem_store.get_capacities(vws.tenant)
    sorted_capacities = utils_ls.sort_elements(
        [{"name": c.name, "id": c.id, "displayName": c.short_name} for c in capacities]
    )

    if show_details:
        fab_response = capacity_api.list_capacities(args)
        if fab_response.status_code in {200, 201}:
            _capacities: list = json.loads(fab_response.text)["value"]
            for cap in sorted_capacities:
                capacity_details: dict[str, str] = next(
                    (c for c in _capacities if c["id"] == cap["id"]), {}
                )
                cap["sku"] = capacity_details.get("sku", "Unknown")
                cap["region"] = capacity_details.get("region", "Unknown")
                cap["state"] = capacity_details.get("state", "Unknown")

        # Azure details
        _az_capacities: list = get_all_az_capacities()
        unknown_capacity = {
            "id": "/subscriptions/Unknown/resourceGroups/Unknown/providers/Microsoft.Fabric/capacities/Unknown",
            "properties": {"administration": {"members": []}},
            "tags": "",
        }
        for cap in sorted_capacities:
            az_cap_details: dict = next(
                (c for c in _az_capacities if c["name"] == cap["displayName"]),
                unknown_capacity,
            )
            # id is in the format /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-name/providers/Microsoft.Fabric/capacities/capacity-name
            cap["subscriptionId"] = az_cap_details["id"].split("/")[2]
            cap["resourceGroup"] = az_cap_details["id"].split("/")[4]
            cap["admins"] = az_cap_details["properties"]["administration"]["members"]
            cap["tags"] = str(az_cap_details["tags"])

    columns = (
        [
            "name",
            "id",
            "sku",
            "region",
            "state",
            "subscriptionId",
            "resourceGroup",
            "admins",
            "tags",
        ]
        if show_details
        else ["name"]
    )

    utils_ls.format_and_print_output(
        data=sorted_capacities, columns=columns, args=args, text_style=TextFormatStyle.UNIX
    )


# Utils
def get_all_az_capacities() -> Any:
    args = Namespace()
    api_response = azure_api.list_subscriptions_azure(args)
    if api_response.status_code != 200:
        raise FabricCLIError(
            "Failed to list subscriptions", fab_constant.ERROR_NOT_FOUND
        )
    subscriptions = json.loads(api_response.text)["value"]
    capacities = []

    for sub in subscriptions:
        sub_id = sub["id"].split("/")[-1]
        _args = Namespace()
        _args.subscription_id = sub_id
        capacities_req = capacity_api.list_capacities_azure(_args)
        capacities += json.loads(capacities_req.text)["value"]

    return capacities
