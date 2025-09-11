# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse


def set_sensi_labels(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/labels/bulk-set-labels?tabs=HTTP"""
    args.uri = f"admin/items/bulkSetLabels"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def remove_sensi_labels(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/admin/labels/bulk-remove-labels?tabs=HTTP"""
    args.uri = f"admin/items/bulkRemoveLabels"
    args.method = "post"

    return fabric_api.do_request(args, data=payload)
