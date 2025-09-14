# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client.fab_api_types import ApiResponse


def create_spark_pool(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/custom-pools/create-workspace-custom-pool?tabs=HTTP"""
    args.item_uri = "spark/pools"
    return item_api.create_item(args, payload, item_uri=True)


def get_spark_pool(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/custom-pools/get-workspace-custom-pool?tabs=HTTP"""
    args.item_uri = "spark/pools"
    return item_api.get_item(args, item_uri=True)


def update_spark_pool(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/custom-pools/update-workspace-custom-pool?tabs=HTTP"""
    args.item_uri = "spark/pools"
    return item_api.update_item(args, payload, item_uri=True)


def delete_spark_pool(
    args: Namespace,
    bypass_confirmation: Optional[bool] = False,
    verbose: bool = True,
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/spark/custom-pools/delete-workspace-custom-pool?tabs=HTTP"""
    args.item_uri = "spark/pools"
    return item_api.delete_item(
        args, bypass_confirmation=bypass_confirmation, item_uri=True, verbose=verbose
    )
