# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def create_shortcut(args: Namespace, payload: dict) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-shortcuts/create-shortcut?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.id}/shortcuts?shortcutConflictPolicy={args.shortcutConflictPolicy}"
    args.method = "post"

    return fabric_api.do_request(args, json=payload)


def get_shortcut(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-shortcuts/get-shortcut?tabs=HTTP"""
    args.uri = (
        f"workspaces/{args.ws_id}/items/{args.id}/shortcuts/{args.path}/{args.name}"
    )
    args.method = "get"

    return fabric_api.do_request(args)


def delete_shortcut(
    args: Namespace, bypass_confirmation: bool, verbose: bool = True
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-shortcuts/delete-shortcut?tabs=HTTP"""
    args.uri = (
        f"workspaces/{args.ws_id}/items/{args.id}/shortcuts/{args.path}/{args.sc_name}"
    )
    args.method = "delete"

    return api_utils.delete_resource(args, bypass_confirmation, verbose)
