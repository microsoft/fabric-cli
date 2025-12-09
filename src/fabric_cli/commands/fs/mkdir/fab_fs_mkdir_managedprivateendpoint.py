# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import time
from argparse import Namespace

from fabric_cli.client import (
    fab_api_managedprivateendpoint as managed_private_endpoint_api,
)
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(managed_private_endpoint: VirtualItem, args: Namespace) -> None:
    # Params
    params = args.params
    required_params = ["targetPrivateLinkResourceId", "targetSubresourceType"]
    optional_params = ["autoApproveEnabled"]
    if mkdir_utils.show_params_desc(
        params,
        managed_private_endpoint.item_type,
        required_params=required_params,
        optional_params=optional_params,
    ):
        return

    # Check required
    mkdir_utils.check_required_params(params, required_params)
    utils_ui.print_grey(
        f"Creating a new Managed Private Endpoint. It may take same time (waiting until provisioned)..."
    )

    managed_private_endpoint_name = managed_private_endpoint.short_name

    payload = {
        "name": managed_private_endpoint_name,
        "targetPrivateLinkResourceId": params.get("targetprivatelinkresourceid"),
        "targetSubresourceType": params.get("targetsubresourcetype"),
        "requestMessage": "Created by fab",
    }

    args.ws_id = managed_private_endpoint.workspace.id

    response = managed_private_endpoint_api.create_managed_private_endpoint(
        args, payload= json.dumps(payload)
    )
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        managed_private_endpoint._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_managed_private_endpoint_to_cache(
            managed_private_endpoint
        )

        # First check the state of the private endpoint
        s_args = Namespace()
        s_args.ws_id = managed_private_endpoint.workspace.id
        s_args.id = managed_private_endpoint.id
        state = "Unknown"
        iteration = 0
        result_message = ""
        while True:
            try:
                response = managed_private_endpoint_api.get_managed_private_endpoint(
                    s_args
                )
                if response.status_code == 200:
                    state = json.loads(response.text)["provisioningState"]
                    # If the state is not Provisioning, stop the loop
                    if state != "Provisioning":
                        break
                    connection = mkdir_utils.find_mpe_connection(
                        managed_private_endpoint,
                        params.get("targetprivatelinkresourceid"),
                    )
                    if connection:
                        # If it is ready from the Azure side, we can consider it
                        state = "Succeeded"
                        break
                    # Wait exponentially
                    time.sleep(2**iteration)
                    iteration += 1
            except Exception:
                state = "Failed"
                break

        if state != "Succeeded":
            raise FabricCLIError(
                f"Managed Private Endpoint was created on Fabric but encountered an issue on Azure provisioning. State: {state}",
                fab_constant.ERROR_OPERATION_FAILED,
            )
        result_message = f"'{managed_private_endpoint.name}' created"

        if params.get("autoapproveenabled", "false").lower() == "true":

            utils_ui.print_grey(f"Approving the Managed Private Endpoint...")

            # Try to approve it
            try:
                connection = mkdir_utils.find_mpe_connection(
                    managed_private_endpoint, params.get("targetprivatelinkresourceid")
                )
                if (
                    connection
                    and connection["properties"]["privateLinkServiceConnectionState"][
                        "status"
                    ]
                    == "Pending"
                ):
                    _args = Namespace()
                    _args.resource_uri = connection["id"]
                    response = managed_private_endpoint_api.approve_private_endpoint_connection(
                        _args
                    )
                    if response.status_code == 200:
                        result_message=f"'{managed_private_endpoint.name}' approved"
                    else:
                        raise Exception("Approval failed")
            except Exception:
                raise FabricCLIError(
                    f"Approval for Managed Private Endpoint failed",
                    fab_constant.ERROR_OPERATION_FAILED,
                )

    utils_ui.print_output_format(args, message=result_message, data=data, show_headers=True)
