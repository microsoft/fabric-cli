# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import format_mapping
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def exec(item: Item, args: Namespace) -> str | None:
    # Determine if this is part of a batch operation
    is_root_operation = not hasattr(args, 'output_batch')

    # Params
    params = args.params
    required_params, optional_params = mkdir_utils.get_params_per_item_type(item)

    if mkdir_utils.show_params_desc(
        params,
        item.item_type,
        required_params=required_params,
        optional_params=optional_params,
    ):
        return None

    if item.id is not None:
        raise FabricCLIError(
            "An item with the same name exists", fab_constant.ERROR_ALREADY_EXISTS
        )

    # Check required params
    mkdir_utils.check_required_params(params, required_params)

    args.ws_id = item.workspace.id
    item_name = item.short_name
    item_type = item.item_type

    utils_ui.print_grey(f"Creating a new {item_type}...")
    args.item_type = str(item_type).lower()

    # Remove all unwanted keys from the params
    utils.remove_keys_from_dict(params, ["displayname", "type"])

    payload = {
        "description": "Created by fab",
        "displayName": item_name,
        "type": str(item_type),
        "folderId": item.folder_id,
    }
    payload = mkdir_utils.add_type_specific_payload(item, args, payload)
    json_payload = json.dumps(payload)
    args.item_uri = format_mapping.get(item.item_type, "items")

    response = item_api.create_item(args, json_payload, item_uri=True)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        
        if not is_root_operation:
            # Collect operation data for batch output
            args.output_batch['items'].append(data)
            args.output_batch['names'].append(item.name)
            
            # Only print consolidated output at the end of root operation
            if is_root_operation:
                names = args.output_batch['names']
                names_list = f"'{names[0]}' and '{names[1]}'" if len(names) == 2 else "'" + "', '".join(names[:-1]) + f"' and '{names[-1]}'"
                
                utils_ui.print_output_format(
                    args,
                    message=f"{names_list} created",
                    data=args.output_batch['items'],
                    show_headers=True
                )
                # Clean up
                delattr(args, 'output_batch')
        else:
            # Standard single item output for non-batched scenarios
            utils_ui.print_output_format(args, message=f"'{item.name}' created", data=data, show_headers=True)
            
        if data is not None and data.get("id"):
            _item_id = data["id"]
            item._id = _item_id
            # Update the cache with the new item
            utils_mem_store.upsert_item_to_cache(item)
            return _item_id
        else:
            # If the response does not contain an id, invalidate the cache
            utils_mem_store.invalidate_item_cache(item.workspace)
            return None
    return None
