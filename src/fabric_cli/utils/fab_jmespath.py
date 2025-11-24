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


def is_simple_path_expression(expr: str) -> bool:
    """Check if a JMESPath expression is a simple explicit path.

    Simple explicit paths are direct field access or numeric index only,
    without filters, wildcards, slices, or functions.

    Args:
        expr: The JMESPath expression to check.

    Returns:
        True if the expression is a simple explicit path, False otherwise.

    Examples:
        >>> is_simple_path_expression("displayName")
        True
        >>> is_simple_path_expression("a.b[0].c")
        True
        >>> is_simple_path_expression("foo['bar-baz']")
        True
        >>> is_simple_path_expression("items[*].id")
        False
        >>> is_simple_path_expression("a.b[?name > 3]")
        False
        >>> is_simple_path_expression("length(items)")
        False
        >>> is_simple_path_expression("a.b[:2]")
        False
        >>> is_simple_path_expression("[foo, bar]")
        False
    """
    try:
        compiled = jmespath.compile(expr)
        parsed = compiled.parsed
        return _is_simple_path_ast_tree(parsed)
    except Exception:
        return False


def _is_simple_path_ast_tree(node: Any) -> bool:
    """Recursively check if a parsed JMESPath AST tree represents a simple path.

    This function traverses the entire AST tree starting from the given node,
    checking that all nodes in the tree represent simple path operations only.

    Args:
        node: Root node of the JMESPath AST tree to validate.

    Returns:
        True if the entire tree represents simple field/index access only.
    """
    node_type = node.get("type")

    if node_type == "field":
        # Simple field access like "displayName"
        return True

    elif node_type == "index":
        # Numeric array index like [0]
        # Check that index is a literal number, not an expression
        index_value = node.get("value")
        return isinstance(index_value, int)

    elif node_type == "index_expression":
        # Array indexing like parts[0] which creates an index_expression node
        # with children: [field_node, index_node]
        children = node.get("children", [])
        return all(_is_simple_path_ast_tree(child) for child in children)

    elif node_type == "subexpression":
        # Nested path like "a.b.c"
        # Both children must be simple
        children = node.get("children", [])
        return all(_is_simple_path_ast_tree(child) for child in children)

    return False
