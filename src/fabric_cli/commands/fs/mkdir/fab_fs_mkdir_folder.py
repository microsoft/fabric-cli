# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_folders as folder_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(folder: Folder, args: Namespace) -> str | None:
    if folder.id is not None:
        raise FabricCLIError(
            ErrorMessages.Mkdir.folder_name_exists(), fab_constant.ERROR_ALREADY_EXISTS
        )

    args.ws_id = folder.workspace.id
    parent_folder_id = folder.parent.id if folder.parent != folder.workspace else None
    foldername = folder.short_name

    utils_ui.print_grey(f"Creating a new Folder...")

    payload = {
        "description": "Created by fab",
        "displayName": foldername,
    }
    if parent_folder_id:
        payload["parentFolderId"] = parent_folder_id

    json_payload = json.dumps(payload)

    response = folder_api.create_folder(args, json_payload)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        utils_ui.print_output_format(args, message=f"'{folder.name}' created", data=data, show_headers=True)
        if data is not None and data.get("id"):
            _folder_id = data["id"]
            folder._id = _folder_id
            # Update the cache with the new item
            utils_mem_store.upsert_folder_to_cache(folder)
            return _folder_id
        else:
            # If the response does not contain an id, invalidate the cache
            utils_mem_store.invalidate_folder_cache(folder.workspace)
            return None
    return None
