# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse

# Fabric API


def list_capacities(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/capacities/list-capacities?tabs=HTTP"""
    args.uri = "capacities"
    args.method = "get"

    return fabric_api.do_request(args)


# Fabric ARM API


def list_capacities_azure(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/list-by-subscription?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    subscription_id = args.subscription_id
    args.audience = "azure"
    uri = f"subscriptions/{subscription_id}/providers/Microsoft.Fabric/capacities"
    api_version = api_utils.get_api_version(uri)
    args.uri = f"{uri}?api-version={api_version}"
    args.method = "get"

    return fabric_api.do_request(args)


def create_capacity(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/create-or-update?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    _prepare_args(args, "put")
    return fabric_api.do_request(args, data=payload)


def delete_capacity(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/delete?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    _prepare_args(args, "delete")
    return api_utils.delete_resource(args, bypass_confirmation, verbose)


def get_capacity(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/get?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    _prepare_args(args, "get")
    return fabric_api.do_request(args)


def update_capacity(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/update?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    _prepare_args(args, "patch")
    return fabric_api.do_request(args, data=payload)


def resume_capacity(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/resume?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    _prepare_args(args, "post", "resume")
    return api_utils.start_resource(args, bypass_confirmation, verbose)


def suspend_capacity(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/suspend?view=rest-microsoftfabric-2023-11-01&tabs=HTTP"""
    _prepare_args(args, "post", "suspend")
    return api_utils.stop_resource(args, bypass_confirmation, verbose)


# Utils
def _get_capacity_uri(args: Namespace) -> str:
    subscription_id = args.subscription_id
    resource_group_name = args.resource_group_name
    # Remove the .capacity suffix if it exists
    name = args.name[:-9] if args.name.lower().endswith(".capacity") else args.name
    return f"subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Fabric/capacities/{name}"


def _prepare_args(args: Namespace, method: str, action: Optional[str] = None) -> None:
    args.audience = "azure"
    uri = _get_capacity_uri(args)
    api_version = api_utils.get_api_version(uri)
    if action:
        args.uri = f"{uri}/{action}?api-version={api_version}"
    else:
        args.uri = f"{uri}?api-version={api_version}"
    args.method = method
