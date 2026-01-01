# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_folders as folder_api
from fabric_cli.commands.fs.get import fab_fs_get_folder as get_folder
from fabric_cli.core.hiearchy.fab_hiearchy import Folder
from fabric_cli.utils import fab_cmd_set_utils as utils_set
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui

JMESPATH_UPDATE_FOLDERS = ["displayName"]


def exec(folder: Folder, args: Namespace) -> None:
    query = args.query

    utils_set.validate_expression(query, JMESPATH_UPDATE_FOLDERS)

    utils_set.print_set_warning()
    if args.force or utils_ui.prompt_confirm():

        args.deep_traversal = True
        args.output = None
        folder_def = get_folder.exec(folder, args, verbose=False)

        updated_def = utils_set.update_fabric_element(folder_def, query, args.input)

        args.name = folder.short_name
        args.id = folder.id

        utils_ui.print_grey(f"Setting new property for '{folder.name}'...")
        response = folder_api.update_folder(args, json.dumps(updated_def, indent=4))

        if response.status_code == 200:
            utils_set.update_cache(
                updated_def, folder, utils_mem_store.upsert_folder_to_cache
            )
            utils_ui.print_output_format(args, message="Folder updated")
