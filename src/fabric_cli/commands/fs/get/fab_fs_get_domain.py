# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_get_utils as utils_get


def exec(
    virtual_ws_item: VirtualWorkspaceItem, args: Namespace, verbose: bool = True
) -> dict:
    fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMIN_ROLE)
    args.name = virtual_ws_item.short_name
    args.id = virtual_ws_item.id

    virtual_ws_item_def = {}
    response = domain_api.get_domain(args)
    if response.status_code == 200:
        virtual_ws_item_def = json.loads(response.text)

        # Add workspaces
        try:
            response = domain_api.list_domain_workspaces(args)
            if response.status_code == 200:
                _assigned_workspaces: list = json.loads(response.text)["value"]
                virtual_ws_item_def["domainWorkspaces"] = _assigned_workspaces
        except Exception:
            pass

        utils_get.query_and_export(
            virtual_ws_item_def, args, virtual_ws_item.name, verbose
        )

    return virtual_ws_item_def
