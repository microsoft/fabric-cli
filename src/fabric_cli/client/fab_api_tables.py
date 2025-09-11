# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse


def load_table(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/tables/load-table?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/lakehouses/{args.lakehouse_id}/tables/{args.table_name}/load"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)
