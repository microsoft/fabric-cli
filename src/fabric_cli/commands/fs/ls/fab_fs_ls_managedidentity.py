# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItemContainer
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vic: VirtualItemContainer, args, show_details):
    managed_identities = utils_mem_store.get_managed_identities(vic)

    if managed_identities:
        sorted_managed_identities = utils_ls.sort_elements(
            [{"name": mi.name, "id": mi.id} for mi in managed_identities]
        )
        base_cols = ["name"]
        if show_details:
            mi_detail_cols = ["servicePrincipalId", "applicationId"]

            args.ws_id = vic.workspace.id
            response = workspace_api.get_workspace(args)
            if response.status_code in {200, 201}:
                _managed_identities: list = [
                    json.loads(response.text)["workspaceIdentity"]
                ]
                for managed_identity in sorted_managed_identities:
                    mi_details: dict[str, str] = next(
                        (
                            c
                            for c in _managed_identities
                            if c["servicePrincipalId"] == managed_identity["id"]
                        ),
                        {},
                    )
                    for col in mi_detail_cols:
                        managed_identity[col] = mi_details.get(col, "Unknown")

        columns = base_cols + mi_detail_cols if show_details else base_cols

        utils_ls.format_and_print_output(
            data=sorted_managed_identities,
            columns=columns,
            args=args,
            show_details=show_details
        )
