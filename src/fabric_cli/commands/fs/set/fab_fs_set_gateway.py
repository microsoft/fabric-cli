# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_gateway as gateways_api
from fabric_cli.commands.fs.get import fab_fs_get_gateway as get_gateway
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui

INVALID_QUERIES = ["publicKey", "version", "virtualNetworkAzureResource"]
SUPPORTED_GATEWAY_TYPES = ["OnPremises", "VirtualNetwork"]


def exec(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    query = args.query

    utils_set.validate_query_not_in_blocklist(query, INVALID_QUERIES)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        vwsi_gateway_def = get_gateway.exec(gateway, args, verbose=False)

        gatewat_type = vwsi_gateway_def.get("type", "")

        validate_query_by_gateway_type(gatewat_type, query)

        updated_def = utils_set.update_fabric_element(
            vwsi_gateway_def, query, args.input
        )

        def _prep_for_updated_def(data, gatewat_type: str) -> str:
            data["type"] = gatewat_type

            # Casting to int if the value is a string and present
            if isinstance(data.get("inactivityMinutesBeforeSleep", 0), str):
                data["inactivityMinutesBeforeSleep"] = int(
                    data["inactivityMinutesBeforeSleep"]
                )
            if isinstance(data.get("numberOfMemberGateways", 0), str):
                data["numberOfMemberGateways"] = int(data["numberOfMemberGateways"])

            return json.dumps(data)

        gateway_update_def = _prep_for_updated_def(updated_def, gatewat_type)

        args.id = gateway.id
        utils_ui.print_grey(f"Setting new property for '{gateway.name}'...")
        response = gateways_api.update_gateway(args, gateway_update_def)

        if response.status_code == 200:
            utils_set.update_cache(
                updated_def, gateway, utils_mem_store.upsert_gateway_to_cache
            )
            utils_ui.print_output_format(args, message="Gateway updated")


def validate_query_by_gateway_type(gateway_type: str, query: str) -> None:
    if gateway_type not in SUPPORTED_GATEWAY_TYPES:
        raise FabricCLIError(
            ErrorMessages.Common.gateway_type_not_supported(gateway_type),
            fab_constant.ERROR_NOT_SUPPORTED,
        )
    elif gateway_type == "OnPremises" and query.startswith(
        ("numberOfMemberGateways", "capacityId", "inactivityMinutesBeforeSleep")
    ):
        raise FabricCLIError(
            ErrorMessages.Common.gateway_property_not_supported_for_type(
                query, "OnPremises"
            ),
            fab_constant.ERROR_NOT_SUPPORTED,
        )
    elif gateway_type == "VirtualNetwork" and query.startswith(
        ("allowCloudConnectionRefresh", "allowCustomConnectors")
    ):
        raise FabricCLIError(
            ErrorMessages.Common.gateway_property_not_supported_for_type(
                query, "VirtualNetwork"
            ),
            fab_constant.ERROR_NOT_SUPPORTED,
        )
