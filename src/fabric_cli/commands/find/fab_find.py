# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Find command for searching the Fabric catalog."""

import json
import os
from argparse import Namespace
from typing import Any

import yaml

from fabric_cli.client import fab_api_catalog as catalog_api
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_jmespath as utils_jmespath
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def _load_type_config() -> dict[str, list[str]]:
    """Load item type definitions from type_supported.yaml."""
    yaml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "type_supported.yaml"
    )
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_TYPE_CONFIG = _load_type_config()
ALL_ITEM_TYPES = _TYPE_CONFIG["supported"] + _TYPE_CONFIG["unsupported"]
UNSUPPORTED_ITEM_TYPES = _TYPE_CONFIG["unsupported"]


@handle_exceptions()
@set_command_context()
def find_command(args: Namespace) -> None:
    """Search the Fabric catalog for items."""
    if args.query:
        args.query = utils.process_nargs(args.query)

    is_interactive = (
        getattr(args, "fab_mode", None) == fab_constant.FAB_MODE_INTERACTIVE
    )
    payload = _build_search_payload(args, is_interactive)

    utils_ui.print_grey("Searching...")

    if is_interactive:
        _find_interactive(args, payload)
    else:
        _find_commandline(args, payload)


def _fetch_results(
    args: Namespace, payload: dict[str, Any]
) -> tuple[list[dict], str | None]:
    """Execute a catalog search request and return parsed results.

    Returns:
        Tuple of (items list, continuation_token or None).

    Raises:
        FabricCLIError: On API error or invalid response body.
    """
    response = catalog_api.search(args, payload)
    results = _parse_response(response)

    items = results.get("value", [])
    continuation_token = results.get("continuationToken", "") or None
    return items, continuation_token


def _next_page_payload(token: str, current: dict[str, Any]) -> dict[str, Any]:
    """Build a continuation payload for the next page."""
    return {"continuationToken": token, "pageSize": current.get("pageSize", 50)}


def _print_search_summary(count: int, has_more_pages: bool = False) -> None:
    """Print the search result summary line."""
    label = "item" if count == 1 else "items"
    count_msg = f"{count} {label} found" + (" (more available)" if has_more_pages else "")
    utils_ui.print_grey("")
    utils_ui.print_grey(count_msg)
    utils_ui.print_grey("")


def _display_page(
    args: Namespace,
    display_items: list[dict],
    truncate_cols: list[str] | None,
    has_more_pages: bool,
    total_count: int,
) -> int:
    """Display a page of results, returning the updated total count."""
    if display_items:
        total_count += len(display_items)
        _print_search_summary(total_count, has_more_pages)
        _display_items(args, display_items, truncate_cols)
    return total_count


def _find_interactive(args: Namespace, payload: dict[str, Any]) -> None:
    """Fetch and display results page by page, prompting between pages."""
    total_count = 0
    items, continuation_token = _fetch_results(args, payload)
    display_items, truncate_cols = _prepare_display_items(args, items)
    total_count = _display_page(
        args, display_items, truncate_cols, continuation_token is not None, total_count
    )

    while continuation_token is not None:
        if display_items:
            try:
                utils_ui.print_grey("")
                input("Press Enter to continue... (Ctrl+C to stop)")
            except (KeyboardInterrupt, EOFError):
                utils_ui.print_grey("")
                break

        payload = _next_page_payload(continuation_token, payload)
        items, continuation_token = _fetch_results(args, payload)
        display_items, truncate_cols = _prepare_display_items(args, items)
        total_count = _display_page(
            args, display_items, truncate_cols, continuation_token is not None, total_count
        )

    if total_count == 0:
        utils_ui.print_grey("No items found.")


def _find_commandline(args: Namespace, payload: dict[str, Any]) -> None:
    """Fetch all results across pages and display."""
    all_items: list[dict] = []
    items, continuation_token = _fetch_results(args, payload)
    all_items.extend(items)

    while continuation_token is not None:
        payload = _next_page_payload(continuation_token, payload)
        items, continuation_token = _fetch_results(args, payload)
        all_items.extend(items)

    if not all_items:
        utils_ui.print_grey("No items found.")
        return

    display_items, truncate_cols = _prepare_display_items(args, all_items)
    if not display_items:
        utils_ui.print_grey("No items found.")
        return
    _print_search_summary(len(display_items))
    _display_items(args, display_items, truncate_cols)


def _build_search_payload(args: Namespace, is_interactive: bool) -> dict[str, Any]:
    """Build the search request payload from command arguments."""
    request: dict[str, Any] = {"search": args.search_text}
    request["pageSize"] = 50 if is_interactive else 1000

    type_filter = _parse_type_from_params(args)
    if type_filter:
        op = type_filter["operator"]
        types = type_filter["values"]
        joiner = " or " if op == "eq" else " and "
        clauses = [f"Type {op} '{t}'" for t in types]
        request["filter"] = (
            f"({joiner.join(clauses)})" if len(clauses) > 1 else clauses[0]
        )

    return request


def _parse_type_from_params(args: Namespace) -> dict[str, Any] | None:
    """Extract and validate item types from -P params.

    Supports:
        -P type=Report              → eq single
        -P type=[Report,Lakehouse]  → eq multiple (or)
        -P type!=Dashboard          → ne single
        -P type!=[Dashboard,Report] → ne multiple (and)

    Returns dict with 'operator' ('eq' or 'ne') and 'values' list, or None.
    """
    params_str = getattr(args, "params", None)
    if not params_str:
        return None

    # nargs="?" gives a string; nargs="*" gives a list (backward compat)
    if isinstance(params_str, list):
        params_str = ",".join(params_str)

    params_dict = utils.get_dict_from_params(params_str, max_depth=1)

    # Check for type key (with or without ! for ne operator)
    type_value = None
    operator = "eq"
    for key, value in params_dict.items():
        # get_dict_from_params splits on first "=", so "type!=X" becomes key="type!", value="X"
        clean_key = key.rstrip("!")
        is_ne = key.endswith("!")

        if clean_key.lower() == "type":
            type_value = value
            operator = "ne" if is_ne else "eq"
        else:
            raise FabricCLIError(
                ErrorMessages.Common.unsupported_parameter(clean_key),
                fab_constant.ERROR_INVALID_INPUT,
            )

    if not type_value:
        return None

    # Parse bracket syntax: [val1,val2] or plain: val1
    if type_value.startswith("[") and type_value.endswith("]"):
        inner = type_value[1:-1]
        types = [t.strip() for t in inner.split(",") if t.strip()]
        if not types:
            raise FabricCLIError(
                ErrorMessages.Find.unrecognized_type(
                    "[]", " Specify at least one item type."
                ),
                fab_constant.ERROR_INVALID_INPUT,
            )
    else:
        types = [type_value.strip()]

    all_types_lower = {t.lower(): t for t in ALL_ITEM_TYPES}
    unsupported_lower = {t.lower() for t in UNSUPPORTED_ITEM_TYPES}
    normalized = []
    for t in types:
        t_lower = t.lower()
        if t_lower in unsupported_lower and operator == "eq":
            canonical = all_types_lower.get(t_lower, t)
            raise FabricCLIError(
                ErrorMessages.Common.type_not_supported(canonical),
                fab_constant.ERROR_UNSUPPORTED_ITEM_TYPE,
            )
        if t_lower not in all_types_lower:
            close = [
                v for k, v in all_types_lower.items() if t_lower in k or k in t_lower
            ]
            hint = (
                f" Did you mean {', '.join(close)}?"
                if close
                else " Run 'find --help' to see examples."
            )
            raise FabricCLIError(
                ErrorMessages.Find.unrecognized_type(t, hint),
                fab_constant.ERROR_INVALID_ITEM_TYPE,
            )
        normalized.append(all_types_lower[t_lower])

    return {"operator": operator, "values": normalized}


def _parse_response(response) -> dict:
    """Parse a successful API response or raise FabricCLIError on failure."""
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        if response.status_code == 200:
            raise FabricCLIError(
                ErrorMessages.Common.invalid_json_format(),
                fab_constant.ERROR_INVALID_JSON,
            )
        raise FabricCLIError(
            ErrorMessages.Find.search_failed(response.text),
            fab_constant.ERROR_INVALID_JSON,
        )

    if response.status_code == 200:
        return data

    fab_logger.log_debug(f"Catalog search error: {data}")
    raise FabricCLIError(
        ErrorMessages.Find.search_failed(data.get("message", response.text)),
        data.get("errorCode", fab_constant.ERROR_UNEXPECTED_ERROR),
    )


def _get_workspace_field(item: dict, field: str) -> str | None:
    """Extract workspace field, supporting both flat and hierarchy formats."""
    ws = item.get("hierarchy", {}).get("workspace", {})
    if field == "name":
        return ws.get("displayName") or item.get("workspaceName")
    if field == "id":
        return ws.get("id") or item.get("workspaceId")
    return None


def _prepare_display_items(
    args: Namespace, items: list[dict]
) -> tuple[list[dict], list[str] | None]:
    """Transform API items into display-ready dicts with optional filtering.

    Returns:
        Tuple of (display items, columns_to_truncate or None).
    """
    show_details = getattr(args, "long", False)
    has_descriptions = any(item.get("description") for item in items)

    display_items = []
    for item in items:
        if show_details:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "id": item.get("id"),
                "type": item.get("type"),
                "workspace": _get_workspace_field(item, "name"),
                "workspace_id": _get_workspace_field(item, "id"),
            }
        else:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "type": item.get("type"),
                "workspace": _get_workspace_field(item, "name"),
            }
        if has_descriptions:
            entry["description"] = item.get("description") or ""
        display_items.append(entry)

    if getattr(args, "query", None):
        query_result = utils_jmespath.search(display_items, args.query)
        if not isinstance(query_result, list):
            return [], None
        display_items = query_result

    truncate_cols = ["description", "workspace", "name"] if not show_details else None
    return display_items, truncate_cols


def _display_items(
    args: Namespace,
    display_items: list[dict],
    columns_to_truncate: list[str] | None = None,
) -> None:
    """Render prepared display items, truncating columns for text format."""
    utils_ui.print_output_format(
        args,
        data=display_items,
        show_headers=True,
        truncate_columns=columns_to_truncate,
    )
    utils_ui.print_grey("")
