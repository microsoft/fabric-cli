# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import re
from argparse import Namespace
from collections.abc import MutableMapping

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def exec(capacity: VirtualWorkspaceItem, args: Namespace) -> None:
    # Params
    optional_params = ["subscriptionId", "resourceGroup", "location", "admin", "sku"]
    if mkdir_utils.show_params_desc(
        args.params, capacity.item_type, optional_params=optional_params
    ):
        return

    (
        az_default_admin,
        az_default_location,
        az_subscription_id,
        az_resource_group,
        _sku,
    ) = utils.get_capacity_settings(args.params)

    utils_ui.print_grey(f"Creating a new Capacity...")

    payload: MutableMapping = {
        "properties": {
            "administration": {
                "members": [
                    f"{az_default_admin}",
                ]
            }
        },
        "sku": {"name": "F2", "tier": "Fabric"},
        "location": f"{az_default_location}",
    }

    args.subscription_id = az_subscription_id
    args.resource_group_name = az_resource_group
    args.name = capacity.short_name
    payload["sku"]["name"] = _sku

    if not (3 <= len(args.name) <= 63):
        raise FabricCLIError(
            "Name must be between 3 and 63 characters in length",
            fab_constant.ERROR_INVALID_INPUT,
        )

    pattern = r"^[a-z][a-z0-9]*$"
    if not re.match(pattern, args.name):
        raise FabricCLIError(
            "Name must start with a lowercase letter and contain only lowercase letters or digits",
            fab_constant.ERROR_INVALID_INPUT,
        )

    # Remove all unwanted keys from the params
    utils.remove_keys_from_dict(args.params, ["properties", "run"])

    json_payload = json.dumps(payload)

    response = capacity_api.create_capacity(args, payload=json_payload)
    if response.status_code in (200, 201):
        utils_ui.print_output_format(args, message=f"'{capacity.name}' created", data=json.loads(response.text), show_headers=True)

        # In here we use a different approach since the id responded by the API is not the same as the id we use in the code
        # The id in the response is the fully qualified azure resource ID for the resource
        # The id in Fabric is the giud of the resource
        # Calling the mem_store method to get the capacity id from the name invalids the cache and performs and API call to the Fabric endpoint to get the GIUD
        try:
            capacity._id = utils_mem_store.get_capacity_id(
                capacity.tenant, capacity.name
            )
            utils_mem_store.upsert_capacity_to_cache(capacity)
        except FabricCLIError as e:
            # If the capacity is not found, it means the user is not an admin of the capacity
            if e.status_code == "NotFound":
                utils_ui.print_warning(
                    "You are not listed as and administrator of the capacity. You won't be able to see or manage it."
                )
            else:
                raise e
