# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Catalog API client for searching Fabric items across workspaces.

API Reference: POST https://api.fabric.microsoft.com/v1/catalog/search
Required Scope: Catalog.Read.All
"""

from argparse import Namespace

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse


def catalog_search(args: Namespace, payload: dict) -> ApiResponse:
    """Search the Fabric catalog for items.

    https://learn.microsoft.com/en-us/rest/api/fabric/core/catalog/search

    Args:
        args: Namespace with request configuration
        payload: Dict with search request body:
            - search (required): Text to search across displayName, description, workspaceName
            - pageSize: Number of results per page
            - continuationToken: Token for pagination
            - filter: OData filter string, e.g., "Type eq 'Report' or Type eq 'Lakehouse'"

    Returns:
        ApiResponse with search results containing:
            - value: List of ItemCatalogEntry objects
            - continuationToken: Token for next page (if more results exist)

    Note:
        The following item types are NOT searchable via this API:
        Dashboard

        Note: Dataflow Gen1 and Gen2 are currently not searchable; only Dataflow Gen2
        CI/CD items are returned (as type 'Dataflow').
        Scorecards are returned as type 'Report'.
    """
    args.uri = "catalog/search"
    args.method = "post"
    # Use raw_response to avoid auto-pagination (we handle pagination in display)
    args.raw_response = True
    return fabric_api.do_request(args, json=payload)

