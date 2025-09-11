# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse

# Azure API versions
API_VERSION_PROVIDER = "2021-04-01"
API_VERSION_SUBSCRIPTIONS = "2022-12-01"
API_VERSION_VNETS = "2024-05-01"

def get_provider_azure(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/resources/providers/get?view=rest-resources-2021-04-01&tabs=HTTP"""
    subscription_id = args.subscription_id
    provider_namespace = args.provider_namespace
    args.audience = "azure"
    args.uri = f"subscriptions/{subscription_id}/providers/{provider_namespace}?api-version={API_VERSION_PROVIDER}"
    args.method = "get"

    return fabric_api.do_request(args)

def list_subscriptions_azure(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/resources/subscriptions/list?view=rest-resources-2022-12-01&tabs=HTTP"""
    args.audience = "azure"
    args.uri = f"subscriptions?api-version={API_VERSION_SUBSCRIPTIONS}"
    args.method = "get"

    return fabric_api.do_request(args)

def list_vnets_azure(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/virtualnetwork/virtual-networks/list-all?view=rest-virtualnetwork-2024-05-01&tabs=HTTP"""
    subscription_id = args.subscription_id
    args.audience = "azure"
    args.uri = f"subscriptions/{subscription_id}/providers/Microsoft.Network/virtualNetworks?api-version={API_VERSION_VNETS}"
    args.method = "get"

    return fabric_api.do_request(args)
