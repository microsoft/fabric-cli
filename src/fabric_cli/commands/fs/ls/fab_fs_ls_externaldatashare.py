# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualItemContainer
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_item_util as item_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_util as utils


def exec(vic: VirtualItemContainer, args, show_details):
    external_data_shares = utils_mem_store.get_external_data_shares(vic.parent)

    if external_data_shares:
        sorted_external_data_shares = utils_ls.sort_elements(
            [
                {
                    "name": eds.name,
                    "id": eds.id,
                    "status": eds.status,
                    "itemId": eds.item_id,
                }
                for eds in external_data_shares
            ]
        )

        base_cols = ["name"]

        should_filter_out_revoked_eds = not show_details
        if show_details:
            eds_detail_cols = [
                "id",
                "status",
                "itemId",
                # "creatorPrincipal",
                # "expirationTimeUtc",
                # "invitationUrl",
                # "paths",
                # "recipient",
                # "workspaceId",
            ]
            eds_detail_col_enrich = "itemName"

            for external_data_share in sorted_external_data_shares:
                item_name = item_utils.get_item_name_from_eds_name(
                    external_data_share.get("name")
                )
                external_data_share[eds_detail_col_enrich] = item_name

        if should_filter_out_revoked_eds:
            sorted_external_data_shares = [
                eds
                for eds in sorted_external_data_shares
                if not eds["status"] == "Revoked"
            ]

        columns = (
            base_cols + eds_detail_cols + [eds_detail_col_enrich]
            if show_details
            else base_cols
        )

        utils_ls.format_and_print_output(
            data=sorted_external_data_shares,
            columns=columns,
            args=args,
            text_style=TextFormatStyle.UNIX
        )
