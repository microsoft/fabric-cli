# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Any, Optional

from fabric_cli.client import fab_api_azure as azure_api
from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui


def delete_resource(
    args: Namespace,
    bypass_confirmation: bool | None,
    verbose: bool = True,
    operation: Optional[str] = "delete",
) -> bool:
    if not bypass_confirmation:
        if utils_ui.prompt_confirm():
            return _do_delete_resource(args, operation=operation)
        else:
            if verbose:
                utils_ui.print_warning(f"Resource {operation} cancelled")
            return False
    else:
        if verbose:
            utils_ui.print_warning(f"Executing force {operation}...")
        return _do_delete_resource(args, verbose=verbose, operation=operation)


def start_resource(
    args: Namespace, bypass_confirmation: bool | None, verbose: bool = True
) -> bool:
    if not bypass_confirmation:
        if utils_ui.prompt_confirm():
            return _do_start_resource(args, verbose)
        else:
            if verbose:
                utils_ui.print_warning("Resource start cancelled")
            return False
    else:
        if verbose:
            utils_ui.print_warning("Executing force start...")
        return _do_start_resource(args, verbose)


def stop_resource(
    args: Namespace, bypass_confirmation: bool | None, verbose: bool = True
) -> bool:
    if not bypass_confirmation:
        if utils_ui.prompt_confirm():
            return _do_stop_resource(args, verbose)
        else:
            if verbose:
                utils_ui.print_warning("Resource stop cancelled")
            return False
    else:
        if verbose:
            utils_ui.print_warning("Executing force stop...")
        return _do_stop_resource(args, verbose)


def assign_resource(
    args: Namespace,
    payload: str,
    bypass_confirmation: bool | None,
    verbose: bool = True,
) -> bool:
    if not bypass_confirmation:
        if utils_ui.prompt_confirm():
            return _do_assign_resource(args, payload, verbose)
        else:
            if verbose:
                utils_ui.print_warning("Resource assignment cancelled")
            return False
    else:
        if verbose:
            utils_ui.print_warning("Executing force assignment...")
        return _do_assign_resource(args, payload, verbose)


def unassign_resource(
    args: Namespace,
    bypass_confirmation: bool | None,
    payload: Optional[str] = None,
    verbose: bool = True,
) -> bool:
    if not bypass_confirmation:
        if utils_ui.prompt_confirm():
            return _do_unassign_resource(args, payload, verbose)
        else:
            if verbose:
                utils_ui.print_warning("Resource unassignment cancelled")
            return False
    else:
        if verbose:
            utils_ui.print_warning("Executing force unassignment...")
        return _do_unassign_resource(args, payload, verbose)


def get_api_version(resource_uri: str) -> Any:
    # Resource URI format Option A: /subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/{namespace}/{resource_type}/{resource_name}
    # Resource URI format Option B: /subscriptions/{subscription_id}/providers/{namespace}/{resource_type}
    ru_parts = resource_uri.lstrip("/").split("/")
    subscription_id = ru_parts[1]
    namespace = ru_parts[3] if ru_parts[2] == "providers" else ru_parts[5]
    resource_type = ru_parts[4] if ru_parts[2] == "providers" else ru_parts[6]
    # Hardcoded api version for capacities for performance reasons
    if namespace == "Microsoft.Fabric" and resource_type == "capacities":
        return "2023-11-01"

    args = Namespace()
    args.subscription_id = subscription_id
    args.provider_namespace = namespace

    response = azure_api.get_provider_azure(args)
    if response.status_code == 200:
        json_response = json.loads(response.text)
        for rt in json_response["resourceTypes"]:
            if rt["resourceType"].lower() == resource_type.lower():
                return rt["apiVersions"][0]

    raise FabricCLIError(
        ErrorMessages.Client.resource_type_not_found_in_provider(args.resource_type, args.provider_namespace),
        status_code=constant.ERROR_NOT_SUPPORTED,
    )


# Utils
def _do_delete_resource(
    args: Namespace, verbose: bool = True, operation: Optional[str] = "delete"
) -> bool:
    if verbose:
        if operation is not None:
            utils_ui.print_grey(f"{_to_gerund_capitalized(operation)} '{args.name}'...")
    response = fabric_api.do_request(args)

    return _validate_success_and_print_on_verbose(
        args, f"{operation}d", response.status_code, verbose
    )


def _do_start_resource(args: Namespace, verbose: bool = True) -> bool:
    if verbose:
        utils_ui.print_grey(f"Starting '{args.name}'...")
    response = fabric_api.do_request(args)

    return _validate_success_and_print_on_verbose(
        args, "started", response.status_code, verbose
    )


def _do_stop_resource(args: Namespace, verbose: bool = True) -> bool:
    if verbose:
        utils_ui.print_grey(f"Stopping '{args.name}'...")
    response = fabric_api.do_request(args)

    return _validate_success_and_print_on_verbose(
        args, "stopped", response.status_code, verbose
    )


def _do_assign_resource(
    args: Namespace, payload: str, verbose: bool = True
) -> bool:
    if verbose:
        utils_ui.print_grey(f"Assigning '{args.name}'...")
    response = fabric_api.do_request(args, data=payload)

    return _validate_success_and_print_on_verbose(
        args, "assigned", response.status_code, verbose
    )


def _do_unassign_resource(
    args: Namespace, payload: Optional[str] = None, verbose: bool = True
) -> bool:
    if verbose:
        utils_ui.print_grey(f"Unassigning '{args.name}'...")
    response = fabric_api.do_request(args, data=payload)

    return _validate_success_and_print_on_verbose(
        args, "unassigned", response.status_code, verbose
    )

def _to_gerund_capitalized(operation: str) -> str:
    if operation.endswith("e") and not operation.endswith("ee"):
        result = f"{operation[:-1]}ing"
    else:
        result = f"{operation}ing"
    return result.capitalize()


def _validate_success_and_print_on_verbose(
    args: Namespace, action: str, status_code: int, verbose: bool = True
) -> bool:
    if status_code in [200, 201]:
        if verbose:
            utils_ui.print_output_format(args, message=f"'{args.name}' {action}")
        return True
    if status_code == 202:
        if verbose:
            utils_ui.print_output_format(
                args, message=f"'{args.name}' is being {action}"
            )
        return True
    return False
