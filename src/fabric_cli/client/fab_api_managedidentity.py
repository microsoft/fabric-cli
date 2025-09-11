# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client.fab_api_types import ApiResponse


def provision_managed_identity(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/provision-identity?tabs=HTTP"""
    args.item_uri = "provisionIdentity"
    return item_api.create_item(args, item_uri=True)


def deprovision_managed_identity(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/deprovision-identity?tabs=HTTP"""
    # Using Overrides since Deprovision API is a POST api without object id in the URI.
    override_method = "post"
    args.uri = f"workspaces/{args.ws_id}/deprovisionIdentity"

    return item_api.delete_item(
        args,
        bypass_confirmation=bypass_confirmation,
        verbose=verbose,
        override_method=override_method,
    )
