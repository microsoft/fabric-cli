# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_import_utils as utils_import
from fabric_cli.utils import fab_item_util
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_storage as utils_storage
from fabric_cli.utils import fab_ui as utils_ui


def import_single_item(item: Item, args: Namespace) -> None:
    _input_format = fab_item_util.resolve_definition_format(
        item_type=item.item_type, format_param=getattr(args, "format", None)
    )

    args.ws_id = item.workspace.id
    input_path = utils_storage.get_import_path(args.input)

    if input_path["type"] != "local":
        raise FabricCLIError(
            f"Import only supports local paths. Unsupported input path type: '{input_path['type']}'.",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    if args.force or utils_ui.prompt_confirm():

        # Check first if an item exists
        item_exists = item.id is not None
        _input_path = input_path["path"]

        # Get the payload
        payload = utils_import.get_payload_for_item_type(
            _input_path, item, input_format=_input_format
        )

        if item_exists:
            utils_ui.print_warning("An item with the same name exists")

            # Update
            if args.force or utils_ui.prompt_confirm("Overwrite?"):
                args.id = item.id

                utils_ui.print_grey(
                    f"Importing (update) '{_input_path}' → '{item.path}'..."
                )

                _import_update_item(args, payload, item)

                utils_ui.print_output_format(
                    args, message=f"'{item.name}' imported")
        else:
            # Create
            utils_ui.print_grey(
                f"Importing '{_input_path}' → '{item.path}'...")

            response = _import_create_item(args, payload, item)

            if response.status_code in (200, 201):
                utils_ui.print_output_format(
                    args, message=f"'{item.name}' imported")
                data = json.loads(response.text)
                item._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_item_to_cache(item)


# Utils
def _import_update_item(
    args: Namespace, payload: dict, item: Item
) -> None:
    """Update an existing item's definition.

    For Environment items, implements the two-phase approach:
    1. Check that no publish is currently in progress
    2. Import the definition via the Items Definition API
    3. Trigger publish automatically after import
    4. Wait for publish to complete
    """
    is_environment = item.item_type == ItemType.ENVIRONMENT

    # Phase 1: For environments, check publish state before import
    if is_environment:
        utils_import.check_environment_publish_ready(args)

    # Phase 2: Import definition via Items Definition API
    definition_payload = json.dumps(
        {
            "definition": payload["definition"],
        }
    )
    item_api.update_item_definition(args, payload=definition_payload)

    # Phase 3 & 4: For environments, trigger publish and wait for completion
    if is_environment:
        utils_import.trigger_environment_publish(args)
        utils_import.wait_for_environment_publish(args)


def _import_create_item(
    args: Namespace, payload: dict, item: Item
) -> ApiResponse:
    """Create a new item with definition.

    For Environment items, implements the two-phase approach:
    1. Create the item via the Items Definition API
    2. Trigger publish automatically after creation
    3. Wait for publish to complete
    """

    _payload = json.dumps(payload)
    response = item_api.create_item(args, payload=_payload)

    # For environments, trigger publish and wait for completion
    if item.item_type == ItemType.ENVIRONMENT:
        data = json.loads(response.text)
        args.id = data["id"]
        utils_import.trigger_environment_publish(args)
        utils_import.wait_for_environment_publish(args)

    return response
