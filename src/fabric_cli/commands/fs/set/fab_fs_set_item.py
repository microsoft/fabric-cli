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

    utils_set.validate_item_query(query_value)

    utils_set.print_set_warning()
    if force or utils_ui.prompt_confirm():
        args.output = None
        args.deep_traversal = True
        args.ws_id = item.workspace.id
        args.id = item.id
        args.item_uri = format_mapping.get(item.item_type, "items")

        if query_value == fab_constant.ITEM_QUERY_DEFINITION or query_value.startswith(
            f"{fab_constant.ITEM_QUERY_DEFINITION}."
        ):
            if not item.check_command_support(Command.FS_EXPORT):
                raise FabricCLIError(
                    CommonErrors.definition_update_not_supported_for_item_type(
                        str(item.item_type)
                    ),
                    fab_constant.ERROR_UNSUPPORTED_COMMAND,
                )

            args.format = definition_format_mapping.get(item.item_type, "")
            def_response = item_api.get_item_definition(args)
            definition = json.loads(def_response.text)

            json_payload, updated_def = _update_element(
                definition, query_value, args.input, decode_encode=True
            )

            definition_base64_to_update, _ = utils_set.extract_json_schema(updated_def)
            update_item_definition_payload = json.dumps(definition_base64_to_update)

            utils_ui.print_grey(f"Setting new property for '{item.name}'...")
            item_api.update_item_definition(args, update_item_definition_payload)
        else:
            item_metadata = json.loads(item_api.get_item(args, item_uri=True).text)

            json_payload, updated_metadata = _update_element(
                item_metadata, query_value, args.input, decode_encode=False
            )

            update_payload_dict = utils_set.extract_updated_properties(
                updated_metadata, query_value
            )
            item_update_payload = json.dumps(update_payload_dict)

            utils_ui.print_grey(f"Setting new property for '{item.name}'...")

            item_api.update_item(args, item_update_payload, item_uri=True)

            if fab_constant.ITEM_QUERY_DISPLAY_NAME in updated_metadata:
                new_item_name = updated_metadata[fab_constant.ITEM_QUERY_DISPLAY_NAME]
                item._name = new_item_name
                utils_mem_store.upsert_item_to_cache(item)

        utils_ui.print_output_format(args, message="Item updated")


def _update_element(
    resource_def: dict,
    query_value: str,
    input_value: str,
    decode_encode: bool,
) -> tuple[str, dict]:
    try:
        return utils_set.update_fabric_element(
            resource_def,
            query_value,
            input_value,
            decode_encode=decode_encode,
        )
    except (ValueError, KeyError, IndexError):
        raise FabricCLIError(
            CommonErrors.invalid_set_item_query(query_value),
            fab_constant.ERROR_INVALID_QUERY,
        )
