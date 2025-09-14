# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.commands.fs.get import fab_fs_get_item as get_item
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(item: Item, args: Namespace) -> None:
    force = args.force
    query = args.query

    utils_set.validate_expression(query, item.get_mutable_properties())

    # Get item
    args.output = None
    args.deep_traversal = True
    item_def = get_item.exec(item, args, verbose=False, decode=False)

    utils_set.print_set_warning()
    if force or utils_ui.prompt_confirm():

        query_value = item.get_property_value(query)

        # Update item
        json_payload, updated_def = utils_set.update_fabric_element(
            item_def, query_value, args.input, decode_encode=True
        )

        definition_base64_to_update, name_description_properties = (
            utils_set.extract_json_schema(updated_def)
        )

        args.ws_id = item.workspace.id
        args.id = item.id
        update_item_definition_payload = json.dumps(definition_base64_to_update)
        update_item_payload = json.dumps(name_description_properties)

        utils_ui.print_grey(f"Setting new property for '{item.name}'...")
        item_api.update_item(args, update_item_payload)

        try:
            if query_value.startswith("definition") and item.check_command_support(
                Command.FS_EXPORT
            ):
                item_api.update_item_definition(args, update_item_definition_payload)
        except Exception:
            utils_ui.print_grey(
                "Item supports only updating displayName or description, not definition",
            )

        # Update mem_store
        new_item_name = name_description_properties["displayName"]
        item._name = new_item_name
        utils_mem_store.upsert_item_to_cache(item)

        utils_ui.print_output_format(args, message="Item updated")
