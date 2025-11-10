# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.fab_types import VirtualWorkspaceType
from fabric_cli.core.hiearchy.fab_hiearchy import Tenant
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(tenant: Tenant, args):
    show_details = bool(args.long)
    show_all = bool(args.all)
    workspaces = utils_mem_store.get_workspaces(tenant)
    sorted_workspaces = []
    columns = []
    if workspaces:
        sorted_workspaces = utils_ls.sort_elements(
            [{"name": ws.name, "id": ws.id} for ws in workspaces]
        )

        if show_details:
            capacities, workspaces_details = utils_ls.get_capacities_and_workspaces(
                args
            )
            sorted_workspaces = utils_ls.enrich_workspaces_with_details(
                sorted_workspaces, workspaces_details, capacities
            )

        columns = (
            ["name", "id", "capacityName", "capacityId", "capacityRegion"]
            if show_details
            else ["name"]
        )

    show_hidden = (
        show_all or fab_state_config.get_config(fab_constant.FAB_SHOW_HIDDEN) == "true"
    )

    utils_ls.format_and_print_output(
        data=sorted_workspaces,
        columns=columns,
        args=args,
        text_style=TextFormatStyle.UNIX,
        hidden_data=VirtualWorkspaceType if show_hidden else None
    )
