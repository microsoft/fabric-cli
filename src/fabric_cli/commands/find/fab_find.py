# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Find command for searching the Fabric catalog."""

import json
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_catalog as catalog_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_ui as utils_ui


# All Fabric item types (from API spec, alphabetically sorted)
ALL_ITEM_TYPES = [
    "AnomalyDetector",
    "ApacheAirflowJob",
    "CopyJob",
    "CosmosDBDatabase",
    "Dashboard",
    "Dataflow",
    "Datamart",
    "DataPipeline",
    "DigitalTwinBuilder",
    "DigitalTwinBuilderFlow",
    "Environment",
    "Eventhouse",
    "EventSchemaSet",
    "Eventstream",
    "GraphModel",
    "GraphQLApi",
    "GraphQuerySet",
    "KQLDashboard",
    "KQLDatabase",
    "KQLQueryset",
    "Lakehouse",
    "Map",
    "MirroredAzureDatabricksCatalog",
    "MirroredDatabase",
    "MirroredWarehouse",
    "MLExperiment",
    "MLModel",
    "MountedDataFactory",
    "Notebook",
    "Ontology",
    "OperationsAgent",
    "PaginatedReport",
    "Reflex",
    "Report",
    "SemanticModel",
    "SnowflakeDatabase",
    "SparkJobDefinition",
    "SQLDatabase",
    "SQLEndpoint",
    "UserDataFunction",
    "VariableLibrary",
    "Warehouse",
    "WarehouseSnapshot",
]

# Types that exist in Fabric but are NOT searchable via the Catalog Search API
UNSUPPORTED_ITEM_TYPES = [
    "Dashboard",
    "Dataflow",
    "Scorecard",
]

# Types that ARE searchable (for validation)
SEARCHABLE_ITEM_TYPES = [t for t in ALL_ITEM_TYPES if t not in UNSUPPORTED_ITEM_TYPES]


def complete_item_types(prefix: str, **kwargs) -> list[str]:
    """Completer for --type flag. Returns matching searchable item types."""
    prefix_lower = prefix.lower()
    # Only complete searchable types to avoid user frustration
    return [t for t in SEARCHABLE_ITEM_TYPES if t.lower().startswith(prefix_lower)]


@handle_exceptions()
@set_command_context()
def find_command(args: Namespace) -> None:
    """Search the Fabric catalog for items."""
    # Validate: either query or --continue must be provided
    has_query = hasattr(args, "query") and args.query
    has_continue = hasattr(args, "continue_token") and args.continue_token

    if not has_query and not has_continue:
        raise FabricCLIError(
            "Either a search query or --continue token is required.",
            fab_constant.ERROR_INVALID_INPUT,
        )

    payload = _build_search_payload(args)

    if has_continue:
        utils_ui.print_grey("Fetching next page of results...")
    else:
        utils_ui.print_grey(f"Searching catalog for '{args.query}'...")

    response = catalog_api.catalog_search(args, payload)

    _handle_response(args, response)


def _build_search_payload(args: Namespace) -> dict[str, Any]:
    """Build the search request payload from command arguments."""
    request: dict[str, Any] = {}

    # If continuation token is provided, only send that (search/filter are encoded in token)
    if hasattr(args, "continue_token") and args.continue_token:
        request["continuationToken"] = args.continue_token
        # Add page size if specified (allowed with continuation token)
        if hasattr(args, "limit") and args.limit:
            request["pageSize"] = args.limit
        return request

    # Normal search request
    request["search"] = args.query

    # Add page size if specified
    if hasattr(args, "limit") and args.limit:
        request["pageSize"] = args.limit

    # Build type filter if specified
    if hasattr(args, "type") and args.type:
        types = args.type  # Already a list from argparse nargs="+"
        # Validate types
        for t in types:
            if t in UNSUPPORTED_ITEM_TYPES:
                raise FabricCLIError(
                    f"Item type '{t}' is not searchable via catalog search API. "
                    f"Unsupported types: {', '.join(UNSUPPORTED_ITEM_TYPES)}",
                    fab_constant.ERROR_UNSUPPORTED_ITEM_TYPE,
                )
            if t not in SEARCHABLE_ITEM_TYPES:
                raise FabricCLIError(
                    f"Unknown item type: '{t}'. Use tab completion to see valid types.",
                    fab_constant.ERROR_INVALID_ITEM_TYPE,
                )

        filter_parts = [f"Type eq '{t}'" for t in types]
        request["filter"] = " or ".join(filter_parts)

    return request


def _handle_response(args: Namespace, response) -> None:
    """Handle the API response, including error cases."""
    # Check for error responses
    if response.status_code != 200:
        try:
            error_data = json.loads(response.text)
            error_code = error_data.get("errorCode", "UnknownError")
            error_message = error_data.get("message", response.text)
        except json.JSONDecodeError:
            error_code = "UnknownError"
            error_message = response.text

        raise FabricCLIError(
            f"Catalog search failed: {error_message}",
            error_code,
        )

    _display_results(args, response)


def _display_results(args: Namespace, response) -> None:
    """Format and display search results."""
    results = json.loads(response.text)
    items = results.get("value", [])
    continuation_token = results.get("continuationToken")

    if not items:
        utils_ui.print_grey("No items found.")
        return

    # Add result count info
    count = len(items)
    has_more = continuation_token is not None
    count_msg = f"{count} item(s) found" + (" (more available)" if has_more else "")
    utils_ui.print_grey("")  # Blank line after "Searching..."
    utils_ui.print_grey(count_msg)
    utils_ui.print_grey("")  # Blank line separator

    # Check if detailed output is requested
    detailed = getattr(args, "long", False)

    if detailed:
        # Detailed output: vertical key-value list with all fields
        # Use snake_case keys for proper Title Case formatting by fab_ui
        # Only include keys with non-empty values
        display_items = []
        for item in items:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "id": item.get("id"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
                "workspace_id": item.get("workspaceId"),
            }
            # Only add description if it has a value
            if item.get("description"):
                entry["description"] = item.get("description")
            display_items.append(entry)
        utils_ui.print_output_format(args, data=display_items, show_key_value_list=True)
    else:
        # Default output: compact table view
        display_items = [
            {
                "name": item.get("displayName") or item.get("name"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
                "description": item.get("description"),
            }
            for item in items
        ]
        utils_ui.print_output_format(args, data=display_items, show_headers=True)

    # Output continuation token if more results available
    if continuation_token:
        utils_ui.print_grey("")
        utils_ui.print_grey(f"To get more results, use: --continue \"{continuation_token}\"")
