# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItem
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils
from fabric_cli.utils import fab_item_util as item_utils


def exec(external_data_share: VirtualItem, args: Namespace) -> None:
    # Params
    params = args.params
    required_params = [
        "paths",
        "recipient.userPrincipalName",
        "recipient.tenantId",
        "item",
    ]
    if mkdir_utils.show_params_desc(
        params,
        external_data_share.item_type,
        required_params=required_params,
    ):
        return

    # Check required
    mkdir_utils.check_required_params(params, required_params)

    utils_ui.print_warning(
        "External Data Share will use the Item name and the ExternalDataShare id - provided name is ignored"
    )

    utils_ui.print_grey(f"Creating a new External Data Share...")
    item = handle_context.get_command_context(params.get("item"))
    try:
        assert isinstance(item, Item)
    except Exception:
        raise FabricCLIError(
            f"The provided item does not match the expected type: {item.type} ",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    raw_paths = params.get("paths")
    cleaned_paths = raw_paths.strip("[]")
    paths = cleaned_paths.split(",")

    payload = {
        "paths": paths,
        "recipient": params.get("recipient"),
    }

    json_payload = json.dumps(payload)
    args.ws_id = external_data_share.workspace.id
    args.item_id = item.id

    response = item_api.create_item_external_data_share(args, payload=json_payload)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        external_data_share._id = data["id"]
        external_data_share._name = item_utils.get_external_data_share_name(
            item.name, external_data_share.id
        )

        utils_ui.print_output_format(args, message=f"'{external_data_share.name}' created", data=data, show_headers=True)

        # Add to mem_store
        utils_mem_store.upsert_external_data_share_to_cache(external_data_share, item)
