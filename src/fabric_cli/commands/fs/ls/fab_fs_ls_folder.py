# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Union

from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.utils import fab_cmd_fs_utils as utils_fs
from fabric_cli.utils import fab_ui as utils_ui


def exec(folder: Folder, args):
    show_details = bool(args.long)

    ws_elements: list[Union[Item, Folder]] = utils_fs.get_ws_elements(folder)
    sort_elements = utils_fs.sort_ws_elements(ws_elements, show_details)

    utils_ui.print_output_format(args, data=sort_elements, show_headers=show_details)
