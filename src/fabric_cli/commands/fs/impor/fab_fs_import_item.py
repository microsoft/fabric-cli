# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_import_utils as utils_import
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_storage as utils_storage
from fabric_cli.utils import fab_ui as utils_ui


def import_single_item(item: Item, args: Namespace) -> None:
    _input_format = None
    if args.format:
        _input_format = args.format
        if _input_format not in (".py", ".ipynb"):
            raise FabricCLIError(
                "Invalid format. Only '.py' and '.ipynb' are supported.",
                fab_constant.ERROR_INVALID_INPUT,
            )

    args.ws_id = item.workspace.id
    input_path = utils_storage.get_import_path(args.input)

    # Input path only support from local directories
    if input_path["type"] == "lakehouse":
        raise FabricCLIError(
            "Import from Lakehouse/Files not supported",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    if args.force or utils_ui.prompt_confirm():

        # Check first if an item exists
        item_exists = item.id is not None
        _input_path = input_path["path"]

        # Get the payload
        payload = utils_import.get_payload_for_item_type(
            _input_path, item, _input_format
        )

        if item_exists:
            fab_logger.log_warning("An item with the same name exists")

            # Update
            if args.force or utils_ui.prompt_confirm("Overwrite?"):
                args.id = item.id

                utils_ui.print_grey(
                    f"Importing (update) '{_input_path}' → '{item.path}'..."
                )

                # Environment item type, not supporting definition yet
                if item.item_type == ItemType.ENVIRONMENT:
                    _import_update_environment_item(args, payload)
                else:
                    _import_update_item(args, payload)

                utils_ui.print_output_format(args, message=f"'{item.name}' imported"
                )
        else:
            # Create
            utils_ui.print_grey(f"Importing '{_input_path}' → '{item.path}'...")

            # Environment item type, not supporting definition yet
            if item.item_type == ItemType.ENVIRONMENT:
                response = _import_create_environment_item(item, args, payload)
            else:
                response = _import_create_item(args, payload)

            if response.status_code in (200, 201):
                utils_ui.print_output_format(args, message=f"'{item.name}' imported"
                )
                data = json.loads(response.text)
                item._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_item_to_cache(item)


# Utils
def _import_update_environment_item(args: Namespace, payload: dict) -> None:
    utils_import.publish_environment_item(args, payload)


def _import_update_item(args: Namespace, payload: dict) -> None:
    definition_payload = json.dumps(
        {
            "definition": payload["definition"],
        }
    )
    item_api.update_item_definition(args, payload=definition_payload)


def _import_create_environment_item(
    item: Item, args: Namespace, payload: dict
) -> ApiResponse:

    item_payload: dict = {
        "type": str(item.item_type),
        "description": "Imported from fab",
        "displayName": item.short_name,
        "folderId": item.folder_id,
    }
    item_payload_str = json.dumps(item_payload)

    # Create the item
    response = item_api.create_item(args, payload=item_payload_str)
    data = json.loads(response.text)
    args.id = data["id"]

    utils_import.publish_environment_item(args, payload)
    return response


def _import_create_item(args: Namespace, payload: dict) -> ApiResponse:
    _payload = json.dumps(payload)
    return item_api.create_item(args, payload=_payload)
