# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Find command for searching the Fabric catalog."""

import json
import shutil
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_catalog as catalog_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_jmespath as utils_jmespath
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


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
]

# Types that ARE searchable (for validation)
SEARCHABLE_ITEM_TYPES = [t for t in ALL_ITEM_TYPES if t not in UNSUPPORTED_ITEM_TYPES]


@handle_exceptions()
@set_command_context()
def find_command(args: Namespace) -> None:
    """Search the Fabric catalog for items."""
    if args.query:
        args.query = utils.process_nargs(args.query)

    is_interactive = getattr(args, "fab_mode", None) == fab_constant.FAB_MODE_INTERACTIVE
    payload = _build_search_payload(args, is_interactive)

    utils_ui.print_grey(f"Searching catalog for '{args.search_text}'...")

    if is_interactive:
        _find_interactive(args, payload)
    else:
        _find_commandline(args, payload)


def _find_interactive(args: Namespace, payload: dict[str, Any]) -> None:
    """Fetch and display results page by page, prompting between pages."""
    total_count = 0

    while True:
        response = catalog_api.catalog_search(args, payload)
        _raise_on_error(response)

        results = json.loads(response.text)
        items = results.get("value", [])
        continuation_token = results.get("continuationToken", "") or None

        if not items and total_count == 0:
            utils_ui.print_grey("No items found.")
            return

        total_count += len(items)
        has_more = continuation_token is not None

        count_msg = f"{len(items)} item(s) found" + (" (more available)" if has_more else "")
        utils_ui.print_grey("")
        utils_ui.print_grey(count_msg)
        utils_ui.print_grey("")

        _display_items(args, items)

        if not has_more:
            break

        try:
            utils_ui.print_grey("")
            input("Press any key to continue... (Ctrl+C to stop)")
        except (KeyboardInterrupt, EOFError):
            utils_ui.print_grey("")
            break

        payload = {"continuationToken": continuation_token}

    if total_count > 0:
        utils_ui.print_grey("")
        utils_ui.print_grey(f"{total_count} total item(s)")


def _find_commandline(args: Namespace, payload: dict[str, Any]) -> None:
    """Fetch all results across pages and display."""
    all_items: list[dict] = []

    while True:
        response = catalog_api.catalog_search(args, payload)
        _raise_on_error(response)

        results = json.loads(response.text)
        all_items.extend(results.get("value", []))

        continuation_token = results.get("continuationToken", "") or None
        if not continuation_token:
            break

        payload = {"continuationToken": continuation_token}

    if not all_items:
        utils_ui.print_grey("No items found.")
        return

    utils_ui.print_grey("")
    utils_ui.print_grey(f"{len(all_items)} item(s) found")
    utils_ui.print_grey("")

    _display_items(args, all_items)


def _build_search_payload(args: Namespace, is_interactive: bool) -> dict[str, Any]:
    """Build the search request payload from command arguments."""
    request: dict[str, Any] = {"search": args.search_text}

    # Interactive pages through 50 at a time; command-line fetches up to 1000
    request["pageSize"] = 50 if is_interactive else 1000

    # Build type filter from -P params
    type_filter = _parse_type_param(args)
    if type_filter:
        op = type_filter["operator"]
        types = type_filter["values"]

        if op == "eq":
            if len(types) == 1:
                request["filter"] = f"Type eq '{types[0]}'"
            else:
                or_clause = " or ".join(f"Type eq '{t}'" for t in types)
                request["filter"] = f"({or_clause})"
        elif op == "ne":
            if len(types) == 1:
                request["filter"] = f"Type ne '{types[0]}'"
            else:
                ne_clause = " and ".join(f"Type ne '{t}'" for t in types)
                request["filter"] = f"({ne_clause})"

    return request


def _parse_type_param(args: Namespace) -> dict[str, Any] | None:
    """Extract and validate item types from -P params.

    Supports:
        -P type=Report          → eq single
        -P type=[Report,Lakehouse]  → eq multiple (or)
        -P type!=Dashboard      → ne single
        -P type!=[Dashboard,Report] → ne multiple (and)
    Legacy comma syntax also supported: -P type=Report,Lakehouse

    Returns dict with 'operator' ('eq' or 'ne') and 'values' list, or None.
    """
    params = getattr(args, "params", None)
    if not params:
        return None

    # params is a list from argparse nargs="*", e.g. ["type=[Report,Lakehouse]"]
    type_value = None
    operator = "eq"
    for param in params:
        if "!=" in param:
            key, value = param.split("!=", 1)
            if key.lower() == "type":
                type_value = value
                operator = "ne"
            else:
                raise FabricCLIError(
                    f"'{key}' isn't a supported parameter. Supported: type",
                    fab_constant.ERROR_INVALID_INPUT,
                )
        elif "=" in param:
            key, value = param.split("=", 1)
            if key.lower() == "type":
                type_value = value
                operator = "eq"
            else:
                raise FabricCLIError(
                    f"'{key}' isn't a supported parameter. Supported: type",
                    fab_constant.ERROR_INVALID_INPUT,
                )
        else:
            raise FabricCLIError(
                f"Invalid parameter format: '{param}'. Use key=value or key!=value.",
                fab_constant.ERROR_INVALID_INPUT,
            )

    if not type_value:
        return None

    # Parse bracket syntax: [val1,val2] or plain: val1 or legacy: val1,val2
    if type_value.startswith("[") and type_value.endswith("]"):
        inner = type_value[1:-1]
        types = [t.strip() for t in inner.split(",") if t.strip()]
    else:
        types = [t.strip() for t in type_value.split(",") if t.strip()]

    # Validate and normalize types (case-insensitive matching)
    all_types_lower = {t.lower(): t for t in ALL_ITEM_TYPES}
    unsupported_lower = {t.lower() for t in UNSUPPORTED_ITEM_TYPES}
    normalized = []
    for t in types:
        t_lower = t.lower()
        if t_lower in unsupported_lower and operator == "eq":
            canonical = all_types_lower.get(t_lower, t)
            raise FabricCLIError(
                f"'{canonical}' isn't searchable via the catalog search API.",
                fab_constant.ERROR_UNSUPPORTED_ITEM_TYPE,
            )
        if t_lower not in all_types_lower:
            # Suggest close matches instead of dumping the full list
            close = [v for k, v in all_types_lower.items() if t_lower in k or k in t_lower]
            hint = f" Did you mean {', '.join(close)}?" if close else " Use tab completion to see valid types."
            raise FabricCLIError(
                f"'{t}' isn't a recognized item type.{hint}",
                fab_constant.ERROR_INVALID_ITEM_TYPE,
            )
        normalized.append(all_types_lower[t_lower])

    return {"operator": operator, "values": normalized}


def _raise_on_error(response) -> None:
    """Raise FabricCLIError if the API response indicates failure."""
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


def _display_items(args: Namespace, items: list[dict]) -> None:
    """Format and display search result items."""
    detailed = getattr(args, "long", False)

    if detailed:
        display_items = []
        for item in items:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "id": item.get("id"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
                "workspace_id": item.get("workspaceId"),
            }
            if item.get("description"):
                entry["description"] = item.get("description")
            display_items.append(entry)
    else:
        has_descriptions = any(item.get("description") for item in items)

        display_items = []
        for item in items:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
            }
            if has_descriptions:
                entry["description"] = item.get("description") or ""
            display_items.append(entry)

        # Truncate descriptions to avoid table wrapping beyond terminal width
        if has_descriptions:
            _truncate_descriptions(display_items)

    # Apply JMESPath client-side filtering if -q/--query specified
    if getattr(args, "query", None):
        display_items = utils_jmespath.search(display_items, args.query)

    if detailed:
        utils_ui.print_output_format(args, data=display_items, show_key_value_list=True)
    else:
        utils_ui.print_output_format(args, data=display_items, show_headers=True)


def _truncate_descriptions(items: list[dict]) -> None:
    """Truncate description column so the table fits within terminal width."""
    term_width = shutil.get_terminal_size((120, 24)).columns
    # Calculate width used by other columns (max value length + 2 padding + 1 gap each)
    other_fields = ["name", "type", "workspace"]
    used = sum(
        max((len(str(item.get(f, ""))) for item in items), default=0) + 3
        for f in other_fields
    )
    # Also account for "description" header length minimum
    max_desc = max(term_width - used - 3, 20)
    for item in items:
        desc = item.get("description", "")
        if len(desc) > max_desc:
            item["description"] = desc[: max_desc - 1] + "…"
