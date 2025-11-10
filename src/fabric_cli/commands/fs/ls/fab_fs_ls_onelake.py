# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import Item, OneLakeItem
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_util as utils


def list_item_folders(item: Item, args):
    show_details = bool(args.long)

    args.directory = item.path_id.strip("/")
    response = onelake_api.list_tables_files(args)

    if response.status_code in (200, 201):
        response_data = json.loads(response.text)
        paths = response_data.get("paths", [])

        for entry in paths:
            entry["name"] = (
                entry["name"].split("/")[1] if "/" in entry["name"] else entry["name"]
            )

        columns = ["permissions", "lastModified", "name"] if show_details else ["name"]

        utils_ls.format_and_print_output(
            data=paths,
            columns=columns,
            args=args,
            text_style=TextFormatStyle.UNIX
        )
    return None

def list_onelake(onelake: OneLakeItem, args):
    show_details = bool(args.long)

    local_path = utils.remove_dot_suffix(onelake.local_path)
    workspace_id = onelake.workspace.id
    item_id = onelake.item.id

    args.directory = f"{workspace_id}/?recursive=false&resource=filesystem&directory={item_id}/{local_path}&getShortcutMetadata=true"
    response = onelake_api.list_tables_files_recursive(args)

    if response.status_code in {200, 201}:
        if response.text:
            response_data = json.loads(response.text)
            paths = response_data.get("paths", [])

            output_data = []
            columns = []
            if paths:
                for entry in paths:
                    utils_ls.update_entry_name_and_type(entry, local_path)

                columns = (
                    ["permissions", "lastModified", "name", "type"]
                    if show_details
                    else ["name"]
                )
                
                output_data = paths
                
            utils_ls.format_and_print_output(
                data=output_data,
                columns=columns,
                args=args,
                text_style=TextFormatStyle.UNIX
            )
