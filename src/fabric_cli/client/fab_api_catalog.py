# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Catalog API client for searching Fabric items across workspaces.

API Reference: POST https://api.fabric.microsoft.com/v1/catalog/search
Required Scope: Catalog.Read.All
"""

import os
from argparse import Namespace

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse

# Environment variable to override the catalog search endpoint (for internal/daily testing)
ENV_CATALOG_ENDPOINT = "FAB_CATALOG_ENDPOINT"

# Default: use standard Fabric API path
DEFAULT_CATALOG_URI = "catalog/search"


def catalog_search(args: Namespace, payload: str) -> ApiResponse:
    """Search the Fabric catalog for items.

    https://learn.microsoft.com/en-us/rest/api/fabric/core/catalog/search

    Args:
        args: Namespace with request configuration
        payload: JSON string with search request body:
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
        Dashboard, Dataflow (Gen1), Dataflow (Gen2), Scorecard

    Environment Variables:
        FAB_CATALOG_ENDPOINT: Override the catalog search endpoint URL for testing
                              (e.g., https://wabi-daily-us-east2-redirect.analysis.windows.net/v1/catalog/search)
    """
    # Check for custom endpoint override (for daily/internal testing)
    custom_endpoint = getattr(args, "endpoint", None) or os.environ.get(ENV_CATALOG_ENDPOINT)

    if custom_endpoint:
        # Use custom endpoint directly via raw request
        return _catalog_search_custom_endpoint(args, payload, custom_endpoint)

    # Standard Fabric API path
    args.uri = DEFAULT_CATALOG_URI
    args.method = "post"
    return fabric_api.do_request(args, data=payload)


def _catalog_search_custom_endpoint(args: Namespace, payload: str, endpoint: str) -> ApiResponse:
    """Make catalog search request to a custom endpoint (e.g., daily environment)."""
    import requests
    import json
    import platform

    from fabric_cli.core import fab_constant
    from fabric_cli.core.fab_auth import FabAuth
    from fabric_cli.core.fab_context import Context as FabContext
    from fabric_cli.client.fab_api_types import ApiResponse

    # Get token using Fabric scope
    token = FabAuth().get_access_token(fab_constant.SCOPE_FABRIC_DEFAULT)

    # Build headers
    ctxt_cmd = FabContext().command
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": f"{fab_constant.API_USER_AGENT}/{fab_constant.FAB_VERSION} ({ctxt_cmd}; {platform.system()}; {platform.machine()}; {platform.release()})",
    }

    response = requests.post(endpoint, headers=headers, data=payload, timeout=240)

    return ApiResponse(
        status_code=response.status_code,
        text=response.text,
        content=response.content,
        headers=response.headers,
    )

