# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import definition_format_mapping, format_mapping
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.errors.common import CommonErrors
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(item: Item, args: Namespace) -> None:
    force = args.force
    query = args.query

    query_value = item.extract_friendly_name_path_or_default(query)

    utils_set.validate_item_query(query_value, item)

    utils_set.print_set_warning()
    if force or utils_ui.prompt_confirm():
        args.output = None
        args.deep_traversal = True
        args.ws_id = item.workspace.id
        args.id = item.id
        args.item_uri = format_mapping.get(item.item_type, "items")

        if query_value.startswith(fab_constant.ITEM_QUERY_DEFINITION):
            formats = definition_format_mapping.get(item.item_type, {"default": ""})
            args.format = formats["default"]
            def_response = item_api.get_item_definition(args)
            definition = json.loads(def_response.text)

            updated_def = _update_item_definition(definition, query_value, args.input)

            update_item_definition_payload = json.dumps(updated_def)

            utils_ui.print_grey(f"Setting new property for '{item.name}'...")
            item_api.update_item_definition(args, update_item_definition_payload)
        else:
            item_metadata = json.loads(item_api.get_item(args, item_uri=True).text)

            update_payload_dict = _update_item_metadata(
                item_metadata, query_value, args.input
            )
            item_update_payload = json.dumps(update_payload_dict)

            utils_ui.print_grey(f"Setting new property for '{item.name}'...")

            item_api.update_item(args, item_update_payload, item_uri=True)

            if fab_constant.ITEM_QUERY_DISPLAY_NAME in update_payload_dict:
                new_item_name = update_payload_dict[fab_constant.ITEM_QUERY_DISPLAY_NAME]
                item._name = new_item_name
                utils_mem_store.upsert_item_to_cache(item)

        utils_ui.print_output_format(args, message="Item updated")


def _update_item_definition(
    item_def: dict,
    query_value: str,
    input_value: str,
) -> dict:
    """Update item definition with base64 decode/encode."""
    try:
        updated_def = utils_set.update_item_definition(
            item_def,
            query_value,
            input_value,
        )
        return updated_def
    except (ValueError, KeyError, IndexError):
        raise FabricCLIError(
            CommonErrors.invalid_set_item_query(query_value),
            fab_constant.ERROR_INVALID_QUERY,
        )


def _update_item_metadata(
    item_metadata: dict,
    query_value: str,
    input_value: str,
) -> dict:
    """Update item metadata without base64 encoding."""
    try:
        return utils_set.update_fabric_element(
            item_metadata,
            query_value,
            input_value,
        )
    except (ValueError, KeyError, IndexError):
        raise FabricCLIError(
            CommonErrors.invalid_set_item_query(query_value),
            fab_constant.ERROR_INVALID_QUERY,
        )
