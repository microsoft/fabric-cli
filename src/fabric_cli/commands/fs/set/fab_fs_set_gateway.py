# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_gateway as gateways_api
from fabric_cli.commands.fs.get import fab_fs_get_gateway as get_gateway
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_GATEWAYS = [
    "displayName",
    "allowCloudConnectionRefresh",
    "allowCustomConnectors",
    "capacityId",
    "inactivityMinutesBeforeSleep",
    "numberOfMemberGateways",
]


def exec(gateway: VirtualWorkspaceItem, args: Namespace) -> None:
    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_GATEWAYS)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        vwsi_gateway_def = get_gateway.exec(gateway, args, verbose=False)

        json_payload, updated_def = utils_set.update_fabric_element(
            vwsi_gateway_def, query, args.input, decode_encode=False
        )

        def _prep_for_updated_def(data):
            data.pop("id", None)
            # numberOfMemberGateways is supported only for VirtualNetwork type (reason for the whole match statement)
            match data.get("type"):
                case "OnPremises":
                    data.pop("numberOfMemberGateways", None)
                    data.pop("publicKey", None)
                    data.pop("version", None)
                case "VirtualNetwork":
                    data.pop("virtualNetworkAzureResource", None)
                case _:
                    raise FabricCLIError(
                        f"Set Operation on Gateway type '{data.get('type')}' not supported",
                        fab_constant.ERROR_NOT_SUPPORTED,
                    )
            # Casting to int if the value is a string and present
            if isinstance(data.get("inactivityMinutesBeforeSleep", 0), str):
                data["inactivityMinutesBeforeSleep"] = int(
                    data["inactivityMinutesBeforeSleep"]
                )
            if isinstance(data.get("numberOfMemberGateways", 0), str):
                data["numberOfMemberGateways"] = int(data["numberOfMemberGateways"])

            return json.dumps(data, indent=4)

        gateway_update_def = _prep_for_updated_def(updated_def)

        args.id = gateway.id
        utils_ui.print_grey(f"Setting new property for '{gateway.name}'...")
        response = gateways_api.update_gateway(args, gateway_update_def)

        if response.status_code == 200:
            # Update mem_store
            gateway._name = updated_def["displayName"]
            utils_mem_store.upsert_gateway_to_cache(gateway)
            utils_ui.print_output_format(args, message="Gateway updated")
