# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.client import fab_api_gateway as gateway_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(connection: VirtualWorkspaceItem, args: Namespace) -> None:
    # Params
    required_params = [
        "connectionDetails.type",
        "connectionDetails.parameters.*",
        "credentialDetails.type",
        "credentialDetails.*",
    ]
    optional_params = [
        "gateway|gatewayId",
        "privacyLevel",
        "description",
        "connectionDetails.creationMethod",
        "credentialDetails.singleSignOnType",
        "credentialDetails.connectionEncryption",
        "credentialDetails.skipTestConnection",
    ]

    if mkdir_utils.show_params_desc(
        args.params,
        connection.item_type,
        required_params=required_params,
        optional_params=optional_params,
    ):
        return

    # Lowercase params
    params = args.params

    if params.get("gateway"):
        # Get the gateway id from the gateway name
        gateway_name = params.get("gateway")
        if not gateway_name.endswith(".Gateway"):
            gateway_name = f"{gateway_name}.Gateway"
        gateway = handle_context.get_command_context(f"/.gateways/{gateway_name}")
        params["gatewayid"] = gateway.id

    if params.get("gatewayid"):
        gateway_id = params.get("gatewayid")
        args.id = gateway_id
        response = gateway_api.get_gateway(args)
        if response.status_code != 200:
            raise FabricCLIError(
                f"Gateway with id {gateway_id} not found",
                fab_constant.ERROR_NOT_FOUND,
            )
        body = json.loads(response.text)
        match body.get("type"):
            case "OnPremises" | "OnPremisesPersonal":
                connectivityType = "OnPremisesGateway"
            case "VirtualNetwork":
                connectivityType = "VirtualNetworkGateway"
            case _ as x:
                raise FabricCLIError(
                    f"Gateway type {x} not supported", fab_constant.ERROR_NOT_SUPPORTED
                )
    else:
        gateway_id = None
        connectivityType = "ShareableCloud"

    if gateway_id:
        # Modify params to obtain the gatewayId
        args.request_params = {"gatewayId": gateway_id}

    response = connection_api.list_supported_connection_types(args)
    if response.status_code != 200:
        raise FabricCLIError(
            "Failed to list supported connection types",
            fab_constant.ERROR_NOT_SUPPORTED,
        )
    args.request_params = {}

    supp_con_types = json.loads(response.text)["value"]
    con_type = params.get("connectiondetails", {}).get("type")
    if con_type is None:
        supp_con_types_str = ", ".join([x["type"] for x in supp_con_types])
        raise FabricCLIError(
            f"Connection type is required. Available connection types are: {supp_con_types_str}",
            fab_constant.ERROR_INVALID_INPUT,
        )

    con_type_def = next(
        (item for item in supp_con_types if item["type"].lower() == con_type.lower()),
        None,
    )

    if con_type_def is None:
        raise FabricCLIError(
            f"Connection type '{con_type}' not found", fab_constant.ERROR_INVALID_INPUT
        )

    utils_ui.print_grey(f"Creating a new Connection...")

    # Base payload
    payload = {
        "description": "Created by fab",
        "displayName": connection.short_name,
        "connectivityType": connectivityType,
    }
    if gateway_id:
        payload["gatewayId"] = gateway_id

    payload = mkdir_utils.get_connection_config_from_params(
        payload, con_type, con_type_def, args.params
    )

    json_payload = json.dumps(payload)

    response = connection_api.create_connection(args, payload=json_payload)
    if response.status_code in (200, 201):
        utils_ui.print_output_format(args, message=f"'{connection.name}' created")

        data = json.loads(response.text)
        connection._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_connection_to_cache(connection)
