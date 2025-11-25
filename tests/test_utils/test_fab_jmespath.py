# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import jmespath
import pytest

from fabric_cli.utils.fab_jmespath import is_simple_path_expression

# Tests for is_simple_path_expression()


@pytest.mark.parametrize(
    "expr,expected",
    [
        # Simple explicit paths - True
        ("displayName", True),
        ("a.b.c", True),
        ("a.b[0].c", True),
        ('foo."bar-baz"', True),
        ("definition.parts[0].payload", True),
        ("sparkSettings.automaticLog.enabled", True),
        ("properties.VariableLibrary", True),
        ("parts[0]", True),
        (
            "definition.parts[0].payload.a.bcd.e",
            True,
        ),
        ("a.b[0].c[1].d", True),
        # Complex expressions - False
        ("items[*].id", False),
        ("a.b[*]", False),
        ("a.*.c", False),
        ("a.b[?name > 3]", False),
        ("items[?price > 100]", False),
        ("items[?price > `100`]", False),
        ("a.b[:2]", False),
        ("items[1:5]", False),
        ("items[::]", False),
        ("items[:2]", False),
        ("length(items)", False),
        ("contains(tags, 'blue')", False),
        ("items[].name", False),
        ("a.b[]", False),
        ("items[]", False),
        ("items[] | sort(@)", False),
        ("a.b | @", False),
        ("items[] | @", False),
        ("[foo, bar]", False),
        ("[displayName, description]", False),
        ("{name: foo.name, cost: foo.price}", False),
        ("{name: foo, price: bar}", False),
        ("`true`", False),
        ("`42`", False),
        ("@", False),
        ("&price", False),
        ("foo || bar", False),
    ],
)
def test_is_simple_path_expression_classifies_expressions_correctly(
    expr: str, expected: bool
):
    """Test that expressions are correctly classified as simple or complex."""
    result = is_simple_path_expression(expr)
    assert (
        result == expected
    ), f"Expression '{expr}' should return {expected}, but got {result}"


def test_is_simple_path_expression_empty_expression_should_return_false():
    """Test that empty expression returns False."""
    assert is_simple_path_expression("") is False


def test_is_simple_path_expression_invalid_expression_should_return_false():
    """Test that invalid JMESPath expression returns False."""
    assert is_simple_path_expression("a.[[[") is False
    assert is_simple_path_expression("???invalid???") is False
