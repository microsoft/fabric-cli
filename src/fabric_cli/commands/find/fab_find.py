# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Find command for searching the Fabric catalog."""

import json
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_catalog as catalog_api
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.utils import fab_ui as utils_ui


# Supported item types for the catalog search API
SUPPORTED_ITEM_TYPES = [
    "Report",
    "SemanticModel",
    "PaginatedReport",
    "Datamart",
    "Lakehouse",
    "Eventhouse",
    "Environment",
    "KQLDatabase",
    "KQLQueryset",
    "KQLDashboard",
    "DataPipeline",
    "Notebook",
    "SparkJobDefinition",
    "MLExperiment",
    "MLModel",
    "Warehouse",
    "Eventstream",
    "SQLEndpoint",
    "MirroredWarehouse",
    "MirroredDatabase",
    "Reflex",
    "GraphQLApi",
    "MountedDataFactory",
    "SQLDatabase",
    "CopyJob",
    "VariableLibrary",
    "ApacheAirflowJob",
    "WarehouseSnapshot",
    "DigitalTwinBuilder",
    "DigitalTwinBuilderFlow",
    "MirroredAzureDatabricksCatalog",
    "Map",
    "AnomalyDetector",
    "UserDataFunction",
    "GraphModel",
    "GraphQuerySet",
    "SnowflakeDatabase",
    "OperationsAgent",
    "CosmosDBDatabase",
    "Ontology",
    "EventSchemaSet",
]

# Types NOT supported by the catalog search API
UNSUPPORTED_ITEM_TYPES = [
    "Dashboard",
    "Dataflow",  # Gen1 and Gen2
    "Scorecard",
]


@handle_exceptions()
@set_command_context()
def find_command(args: Namespace) -> None:
    """Search the Fabric catalog for items."""
    payload = _build_search_payload(args)

    utils_ui.print_grey(f"Searching catalog for '{args.query}'...")
    response = catalog_api.catalog_search(args, payload)

    _display_results(args, response)


def _build_search_payload(args: Namespace) -> str:
    """Build the search request payload from command arguments."""
    request: dict[str, Any] = {"search": args.query}

    # Add page size if specified
    if hasattr(args, "limit") and args.limit:
        request["pageSize"] = args.limit

    # Build type filter if specified
    if hasattr(args, "type") and args.type:
        types = [t.strip() for t in args.type.split(",")]
        # Validate types
        for t in types:
            if t not in SUPPORTED_ITEM_TYPES:
                if t in UNSUPPORTED_ITEM_TYPES:
                    utils_ui.print_warning(
                        f"Type '{t}' is not supported by catalog search API"
                    )
                else:
                    utils_ui.print_warning(f"Unknown item type: '{t}'")

        filter_parts = [f"Type eq '{t}'" for t in types]
        request["filter"] = " or ".join(filter_parts)

    return json.dumps(request)


def _display_results(args: Namespace, response) -> None:
    """Format and display search results."""
    results = json.loads(response.text)
    items = results.get("value", [])

    if not items:
        utils_ui.print_grey("No items found.")
        return

    # Add result count info
    count = len(items)
    has_more = results.get("continuationToken") is not None
    count_msg = f"{count} item(s) found" + (" (more available)" if has_more else "")
    utils_ui.print_grey(count_msg)

    # Check if detailed output is requested
    detailed = getattr(args, "detailed", False)

    if detailed:
        # Detailed output: show all fields including IDs
        display_items = [
            {
                "id": item.get("id"),
                "name": item.get("displayName"),
                "type": item.get("type"),
                "workspaceId": item.get("workspaceId"),
                "workspace": item.get("workspaceName"),
                "description": item.get("description"),
            }
            for item in items
        ]
    else:
        # Default output: compact view aligned with CLI path format
        display_items = [
            {
                "name": item.get("displayName"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
                "description": item.get("description"),
            }
            for item in items
        ]

    # Format output based on output_format setting
    utils_ui.print_output_format(args, display_items)
