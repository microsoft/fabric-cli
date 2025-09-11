# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def create_managed_private_endpoint(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/managed-private-endpoints/create-workspace-managed-private-endpoint?tabs=HTTP"""
    args.item_uri = "managedPrivateEndpoints"
    return item_api.create_item(args, payload, item_uri=True)


def get_managed_private_endpoint(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/managed-private-endpoints/get-workspace-managed-private-endpoint?tabs=HTTP"""
    args.item_uri = "managedPrivateEndpoints"
    return item_api.get_item(args, item_uri=True)


def delete_managed_private_endpoint(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/managed-private-endpoints/delete-workspace-managed-private-endpoint?tabs=HTTP"""
    args.item_uri = "managedPrivateEndpoints"
    return item_api.delete_item(
        args, bypass_confirmation=bypass_confirmation, item_uri=True, verbose=verbose
    )


# Azure API


def list_private_endpoints_by_azure_resource(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storagerp/private-endpoint-connections/list?view=rest-storagerp-2024-01-01&viewFallbackFrom=rest-storagerp-2023-05-01&tabs=HTTP"""
    args.audience = "azure"
    api_version = api_utils.get_api_version(args.resource_uri)
    args.uri = (
        f"{args.resource_uri}/privateEndpointConnections?api-version={api_version}"
    )
    args.uri = args.uri.lstrip("/")
    args.method = "get"

    return fabric_api.do_request(args)


def approve_private_endpoint_connection(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/appservice/app-service-environments/approve-or-reject-private-endpoint-connection?view=rest-appservice-2024-04-01&tabs=HTTP"""
    args.audience = "azure"
    api_version = api_utils.get_api_version(args.resource_uri)
    args.uri = f"{args.resource_uri}?api-version={api_version}"
    args.uri = args.uri.lstrip("/")
    args.method = "put"

    payload = json.dumps(
        {
            "properties": {
                "privateLinkServiceConnectionState": {
                    "status": "Approved",
                    "description": "Approved by fab",
                }
            }
        }
    )

    return fabric_api.do_request(args, data=payload)


def get_managed_private_endpoint_azure(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storagerp/private-endpoint-connections/get?view=rest-storagerp-2024-01-01&tabs=HTTP"""
    args.audience = "azure"
    api_version = api_utils.get_api_version(args.resource_uri)
    args.uri = f"{args.resource_uri}?api-version={api_version}"
    args.uri = args.uri.lstrip("/")
    args.method = "get"

    return fabric_api.do_request(args)
