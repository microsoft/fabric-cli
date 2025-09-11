# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def list_domains(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/list-domains?tabs=HTTP"""
    args.uri = "admin/domains"
    args.method = "get"

    return fabric_api.do_request(args)


def create_domain(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/create-domain?tabs=HTTP"""
    args.uri = "admin/domains"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def get_domain(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/get-domain?tabs=HTTP"""
    args.uri = f"admin/domains/{args.id}"
    args.method = "get"

    return fabric_api.do_request(args)


def update_domain(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/update-domain?tabs=HTTP"""
    args.uri = f"admin/domains/{args.id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


def delete_domain(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/delete-domain?tabs=HTTP"""
    args.uri = f"admin/domains/{args.id}"
    args.method = "delete"

    return api_utils.delete_resource(args, bypass_confirmation, verbose)


def assign_to_workspaces(
    args: Namespace,
    payload: str,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/assign-domain-workspaces-by-ids?tabs=HTTP"""
    args.uri = f"admin/domains/{args.id}/assignWorkspaces"
    args.method = "post"

    return api_utils.assign_resource(args, payload, bypass_confirmation, verbose)


def unassign_from_workspaces(
    args: Namespace,
    payload: str,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/unassign-domain-workspaces-by-ids?tabs=HTTP"""
    args.uri = f"admin/domains/{args.id}/unassignWorkspaces"
    args.method = "post"

    return api_utils.unassign_resource(
        args, bypass_confirmation, payload=payload, verbose=verbose
    )


def list_domain_workspaces(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/domains/list-domain-workspaces?tabs=HTTP"""
    args.uri = f"admin/domains/{args.id}/workspaces"
    args.method = "get"

    return fabric_api.do_request(args)
