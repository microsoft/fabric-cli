# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_folders as folder_api
from fabric_cli.core.hiearchy.fab_hiearchy import Folder
from fabric_cli.utils import fab_cmd_get_utils as utils_get


def exec(folder: Folder, args: Namespace, verbose: bool = True) -> dict:
    args.ws_id = folder.workspace.id
    args.folder_id = folder.id

    folder_def = {}
    response = folder_api.get_folder(args)
    if response.status_code == 200:
        folder_def = json.loads(response.text)
        utils_get.query_and_export(folder_def, args, folder.name, verbose)

    return folder_def
