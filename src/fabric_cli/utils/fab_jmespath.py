# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Any, Optional

import jmespath

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui

# Redis and others built some custom functions
# https://redis.io/docs/latest/integrate/redis-data-integration/reference/jmespath-custom-functions/


def search(
    data: Any, expression: str, deep_traversal: Optional[bool] = False
) -> str | list | dict:
    if not expression:
        max_depth = float("inf") if deep_traversal else 4
        return _get_json_paths(data, max_depth=max_depth)
    else:
        try:
            if "." == expression:
                return data
            result = jmespath.search(expression, data, options=None)
            if isinstance(result, (dict, list)):
                return result
            return str(result)
        except Exception as e:
            raise FabricCLIError(
                ErrorMessages.Common.invalid_jmespath_query(),
                fab_constant.ERROR_INVALID_INPUT,
            )


def replace(data: Any, expression: Any, new_value: Any) -> Any:
    """
    Replace the value of a property or subtree in a JSON structure using JMESPath.

    :param data: The JSON object (as a dictionary).
    :param expression: A JMESPath expression for the property to replace.
    :param new_value: The new value to set.
    :return: Updated JSON object.
    """
    if not expression:
        raise ValueError("The JMESPath expression cannot be empty")

    # Split the expression to identify parent and key
    parts = expression.strip(".").split(".")

    # Handle array indices in the path
    for i, part in enumerate(parts):
        if "[" in part and "]" in part:
            key, index = part.split("[")
            if "*" in index:
                raise ValueError("Wildcards are not supported in array indexing")
            index = int(index.rstrip("]"))
            parts[i] = f"{key}[{index}]"

    if len(parts) == 1:  # No parent, top-level key
        key = parts[0]
        parent = data
    else:
        # Identify parent container and target key
        parent_expr = ".".join(parts[:-1])
        key = parts[-1]

        if "*" in parent_expr:
            raise ValueError("Wildcards are not supported in parent expressions")

        # Locate parent container
        parent = jmespath.search(parent_expr, data)
        if parent is None:
            raise ValueError(f"Cannot locate parent for expression '{expression}'")

    if "*" in key:
        raise ValueError("Wildcards are not supported")

    # Update the target key or array index
    if key.startswith("[") and key.endswith("]"):  # Handle array index
        index = int(key.strip("[]"))
        if not isinstance(parent, list) or index >= len(parent):
            raise IndexError(f"Index out of range for '{key}'")
        parent[index] = new_value
    elif "[" in key and "]" in key:
        key, index = key.split("[")
        index = int(index.rstrip("]"))
        if not isinstance(parent, dict) or key not in parent:
            raise KeyError(f"Key '{key}' not found in parent")
        parent[key][index] = new_value
    else:  # Handle regular keys
        if not isinstance(parent, dict):
            raise ValueError(f"Parent for '{key}' is not a dictionary")
        parent[key] = new_value

    return data


# Utils
def _get_json_paths(json_obj, current_path="", depth=0, max_depth=4):
    paths = []

    if isinstance(json_obj, dict):
        # If the current object is a dictionary, traverse its keys
        for key, value in json_obj.items():
            new_path = f"{current_path}.{key}" if current_path else key
            if depth < max_depth:
                paths.extend(_get_json_paths(value, new_path, depth + 1, max_depth))
            else:
                # If we've reached max depth, only add the path
                paths.append(new_path)

    elif isinstance(json_obj, list):
        if not json_obj:  # Explicitly handle empty lists
            paths.append(current_path)
        # If the current object is a list, traverse its items
        for idx, value in enumerate(json_obj):
            new_path = f"{current_path}[{idx}]"
            if depth < max_depth:
                paths.extend(_get_json_paths(value, new_path, depth + 1, max_depth))
            else:
                # If we've reached max depth, only add the path
                paths.append(new_path)

    else:
        paths.append(current_path)

    return paths
