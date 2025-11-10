# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Any

from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.core.fab_output import TextFormatStyle
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspace
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vws: VirtualWorkspace, args, show_details):
    _base_cols = ["name", "id"]
    _details_cols = {
        # "connectionDetails",
        "connectionDetails.type": "type",
        "connectivityType": "connectivityType",
        # "credentialDetails",
        "gatewayName": "gatewayName",
        "gatewayId": "gatewayId",
        "privacyLevel": "privacyLevel",
    }
    connections = utils_mem_store.get_connections(vws.tenant)
    sorted_connections = utils_ls.sort_elements(
        [{"name": c.name, "id": c.id, "displayName": c.short_name} for c in connections]
    )

    if show_details:
        fab_response = connection_api.list_connections(args)
        if fab_response.status_code in {200, 201}:
            _connections: list = json.loads(fab_response.text)["value"]
            for connection in sorted_connections:
                connection_details: dict[str, Any] = next(
                    (c for c in _connections if c["id"] == connection["id"]), {}
                )
                for col, alias in _details_cols.items():
                    cols = col.split(".")
                    # Loop through cols minus the last one
                    if len(cols) > 1:
                        _value: dict[str, Any] = connection_details
                        for i in range(len(cols) - 1):
                            _value = _value.get(cols[i], {})
                        connection[alias] = _value.get(cols[-1], "Unknown")
                    else:
                        connection[alias] = connection_details.get(col, "Unknown")

        _gateways = utils_mem_store.get_gateways(vws.tenant)
        for connection in sorted_connections:
            gateway_id = connection.get("gatewayId")
            gateway_name = next(
                (g.name for g in _gateways if g.id == gateway_id), "Unknown"
            )
            connection["gatewayName"] = gateway_name

    columns = _base_cols + list(_details_cols.values()) if show_details else ["name"]

    utils_ls.format_and_print_output(
        data=sorted_connections,
        columns=columns,
        args=args,
        text_style=TextFormatStyle.UNIX
    )
