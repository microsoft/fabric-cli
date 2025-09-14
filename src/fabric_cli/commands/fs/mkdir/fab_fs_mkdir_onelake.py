# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemOnelakeWritableFoldersMap, ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import OneLakeItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def create_directory(onelake: OneLakeItem, args: Namespace) -> None:
    # Params
    if mkdir_utils.show_params_desc(args.params, onelake.type):
        return

    # Supported folders
    item_type: ItemType = onelake.item.item_type
    root_folder = onelake.root_folder
    supported_folders = ItemOnelakeWritableFoldersMap[item_type]

    if root_folder not in supported_folders:
        raise FabricCLIError(
            f"Cannot create folders under '{root_folder}' for {item_type}. Only {supported_folders} folders are supported",
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    path_name = utils.process_nargs(args.path)  # onelake.get_path().strip("/")
    path_id = onelake.path_id.strip("/")

    utils_ui.print_grey(f"Creating a new Directory...")
    args.directory = path_id

    response = onelake_api.create_dir(args)
    if response.status_code in (200, 201):
        utils_ui.print_output_format(args, message=f"'{path_name}' created")
