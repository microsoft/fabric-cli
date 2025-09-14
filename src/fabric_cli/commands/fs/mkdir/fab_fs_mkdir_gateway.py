# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_gateway as gateway_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    # Params
    required_params = [
        "capacity|capacityId",
        "virtualNetworkName",
        "subnetName",
    ]
    optional_params = [
        "inactivityMinutesBeforeSleep",  # Default: 30
        "numberOfMemberGateways",  # Default: 1
        "subscriptionId",
        "resourceGroupName",
    ]

    if mkdir_utils.show_params_desc(
        args.params,
        gateway.item_type,
        required_params=required_params,
        optional_params=optional_params,
    ):
        return

    utils_ui.print_grey(f"Creating a new Gateway...")

    # Lowercase params
    params = args.params

    if params.get("capacity"):
        # Get the capacity id from the capacity name
        capacity_name = params.get("capacity")
        if not capacity_name.endswith(".Capacity"):
            capacity_name = f"{capacity_name}.Capacity"
        capacity = handle_context.get_command_context(f"/.capacities/{capacity_name}")
        params["capacityid"] = capacity.id

    if not params.get("capacityid"):
        raise FabricCLIError(
            "Capacity Name or ID is required", fab_constant.ERROR_INVALID_INPUT
        )

    if not params.get("virtualnetworkname") or not params.get("subnetname"):
        raise FabricCLIError(
            "Virtual Network and Subnet Name is required",
            fab_constant.ERROR_INVALID_INPUT,
        )

    if not params.get("subscriptionid"):
        vnet = params.get("virtualnetworkname")
        subnet = params.get("subnetname")
        sub_id, rg_name = mkdir_utils.find_vnet_subnet(vnet, subnet)
        utils_ui.print_grey(
            f"Found Subnet '{vnet}/{subnet}' in Subscription '{sub_id}' and Resource Group '{rg_name}'"
        )
        params["subscriptionid"] = sub_id
        params["resourcegroupname"] = rg_name

    if not params.get("subscriptionid") or not params.get("resourcegroupname"):
        raise FabricCLIError(
            "Subscription ID and Resource Group Name is required",
            fab_constant.ERROR_INVALID_INPUT,
        )

    vnet_res = {
        "subscriptionId": params.get("subscriptionid"),
        "resourceGroupName": params.get("resourcegroupname"),
        "virtualNetworkName": params.get("virtualnetworkname"),
        "subnetName": params.get("subnetname"),
    }

    payload = {
        # "description": "Created by fab",
        "displayName": gateway.short_name,
        "capacityId": params.get("capacityid"),
        "inactivityMinutesBeforeSleep": params.get("inactivityminutesbeforesleep", 30),
        "numberOfMemberGateways": args.params.get("numberofmembergateways", 1),
        "type": "VirtualNetwork",
        "virtualNetworkAzureResource": vnet_res,
    }

    response = gateway_api.create_gateway(args, payload=json.dumps(payload))
    if response.status_code in (200, 201):
        utils_ui.print_output_format(args, message=f"'{gateway.name}' created")

        data = json.loads(response.text)
        gateway._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_gateway_to_cache(gateway)
