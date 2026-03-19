# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Find command for searching the Fabric catalog."""

import json
import os
from argparse import Namespace
from typing import Any

import yaml

from fabric_cli.client import fab_api_catalog as catalog_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_jmespath as utils_jmespath
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def _load_type_config() -> dict[str, list[str]]:
    """Load item type definitions from type_supported.yaml."""
    yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "type_supported.yaml")
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


_TYPE_CONFIG = _load_type_config()
ALL_ITEM_TYPES = _TYPE_CONFIG["supported"] + _TYPE_CONFIG["unsupported"]
UNSUPPORTED_ITEM_TYPES = _TYPE_CONFIG["unsupported"]
SEARCHABLE_ITEM_TYPES = _TYPE_CONFIG["supported"]


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


def _fetch_results(args: Namespace, payload: dict[str, Any]) -> tuple[list[dict], str | None]:
    """Execute a catalog search request and return parsed results.

    Returns:
        Tuple of (items list, continuation_token or None).

    Raises:
        FabricCLIError: On API error or invalid response body.
    """
    # raw_response=True in catalog_api.search means we must check status ourselves
    response = catalog_api.search(args, payload)
    _raise_on_error(response)

    try:
        results = json.loads(response.text)
    except json.JSONDecodeError:
        raise FabricCLIError(
            ErrorMessages.Find.invalid_response(),
            fab_constant.ERROR_INVALID_JSON,
        )

    items = results.get("value", [])
    continuation_token = results.get("continuationToken", "") or None
    return items, continuation_token


def _print_search_summary(count: int, has_more: bool = False) -> None:
    """Print the search result summary line."""
    count_msg = f"{count} item(s) found" + (" (more available)" if has_more else "")
    utils_ui.print_grey("")
    utils_ui.print_grey(count_msg)
    utils_ui.print_grey("")


def _find_interactive(args: Namespace, payload: dict[str, Any]) -> None:
    """Fetch and display results page by page, prompting between pages."""
    total_count = 0
    has_more = True

    while has_more:
        items, continuation_token = _fetch_results(args, payload)

        if not items and total_count == 0:
            utils_ui.print_grey("No items found.")
            return

        total_count += len(items)
        has_more = continuation_token is not None
        _print_search_summary(len(items), has_more)

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
        utils_ui.print_grey(f"{total_count} item(s) shown")


def _find_commandline(args: Namespace, payload: dict[str, Any]) -> None:
    """Fetch all results across pages and display."""
    all_items: list[dict] = []
    has_more = True

    while has_more:
        items, continuation_token = _fetch_results(args, payload)
        all_items.extend(items)
        has_more = continuation_token is not None
        if has_more:
            payload = {"continuationToken": continuation_token}

    if not all_items:
        utils_ui.print_grey("No items found.")
        return

    _print_search_summary(len(all_items))

    _display_items(args, all_items)


def _build_search_payload(args: Namespace, is_interactive: bool) -> dict[str, Any]:
    """Build the search request payload from command arguments."""
    request: dict[str, Any] = {"search": args.search_text}
    request["pageSize"] = 50 if is_interactive else 1000

    type_filter = _parse_type_from_params(args)
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

    params_dict = utils.get_dict_from_params(params_str)

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
            close = [v for k, v in all_types_lower.items() if t_lower in k or k in t_lower]
            hint = f" Did you mean {', '.join(close)}?" if close else " Use tab completion to see valid types."
            raise FabricCLIError(
                ErrorMessages.Find.unrecognized_type(t, hint),
                fab_constant.ERROR_INVALID_ITEM_TYPE,
            )
        normalized.append(all_types_lower[t_lower])

    return {"operator": operator, "values": normalized}


def _raise_on_error(response) -> None:
    """Raise FabricCLIError if the API response indicates failure."""
    if response.status_code != 200:
        try:
            error_data = json.loads(response.text)
            error_code = error_data.get("errorCode", fab_constant.ERROR_UNEXPECTED_ERROR)
            error_message = error_data.get("message", response.text)
        except json.JSONDecodeError:
            error_code = fab_constant.ERROR_UNEXPECTED_ERROR
            error_message = response.text

        raise FabricCLIError(
            ErrorMessages.Find.search_failed(error_message),
            error_code,
        )


def _display_items(args: Namespace, items: list[dict]) -> None:
    """Format and display search result items."""
    show_details = getattr(args, "long", False)
    has_descriptions = any(item.get("description") for item in items)

    display_items = []
    for item in items:
        if show_details:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "id": item.get("id"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
                "workspace_id": item.get("workspaceId"),
            }
        else:
            entry = {
                "name": item.get("displayName") or item.get("name"),
                "type": item.get("type"),
                "workspace": item.get("workspaceName"),
            }
        if has_descriptions:
            entry["description"] = item.get("description") or ""
        display_items.append(entry)

    if has_descriptions and not show_details:
        utils.truncate_descriptions(display_items)

    if getattr(args, "query", None):
        display_items = utils_jmespath.search(display_items, args.query)

    utils_ui.print_output_format(args, data=display_items, show_headers=True)
