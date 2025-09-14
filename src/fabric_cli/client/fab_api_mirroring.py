# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def get_mirroring_status(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/mirroreddatabase/mirroring/get-mirroring-status?tabs=HTTP"""
    _prepare_args(args, "getMirroringStatus")
    return fabric_api.do_request(args)


def get_table_mirroring_status(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/mirroreddatabase/mirroring/get-tables-mirroring-status?tabs=HTTP"""
    _prepare_args(args, "getTablesMirroringStatus")
    return fabric_api.do_request(args)


def start_mirroring(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/mirroreddatabase/mirroring/start-mirroring?tabs=HTTP"""
    _prepare_args(args, "startMirroring")
    return api_utils.start_resource(args, bypass_confirmation, verbose)


def stop_mirroring(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/mirroreddatabase/mirroring/stop-mirroring?tabs=HTTP"""
    _prepare_args(args, "stopMirroring")
    return api_utils.stop_resource(args, bypass_confirmation, verbose)


def _prepare_args(args: Namespace, endpoint: str) -> None:
    ws_id = args.ws_id
    db_id = args.id
    args.uri = f"workspaces/{ws_id}/mirroredDatabases/{db_id}/{endpoint}"
    args.method = "post"
