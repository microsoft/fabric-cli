# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.client import fab_api_shortcuts as shortcut_api
from fabric_cli.core.fab_types import OneLakeItemType
from fabric_cli.core.hiearchy.fab_hiearchy import OneLakeItem
from fabric_cli.utils import fab_util as utils


def shortcut_file_or_folder(
    onelake: OneLakeItem,
    args: Namespace,
    force_delete: bool,
    verbose: bool = True,
) -> None:
    # Remove shortcut
    if onelake.nested_type == OneLakeItemType.SHORTCUT:
        args.ws_id = onelake.workspace.id
        args.id = onelake.item.id
        args.path, args.sc_name = os.path.split(onelake.local_path.rstrip("/"))
        args.name = onelake.full_name  # the name that is displayed in the UI

        shortcut_api.delete_shortcut(args, force_delete, verbose)
        return

    # Remove file or folder
    path_name = utils.process_nargs(args.path)
    path_id = onelake.path_id.strip("/")

    args.directory = path_id
    args.name = path_name

    onelake_api.delete_dir(args, force_delete, verbose)
