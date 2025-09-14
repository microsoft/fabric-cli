# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_jmespath as jmespath


def test_search(mock_fab_set_state_config):

    mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "text")
    _data = [{"key": "value"}, {"key": "value2"}]
    _expression = None
    _result = jmespath.search(_data, _expression)
    assert _result == ["[0].key", "[1].key"]

    _expression = "[*].key"
    _result = jmespath.search(_data, _expression)
    assert _result == ["value", "value2"]

    _data = {"key": "value"}
    _expression = "key"
    _result = jmespath.search(_data, _expression)
    assert _result == "value"

    _data = {"key": "value", "list": [1, 2, 3]}
    _expression = None
    _result = jmespath.search(_data, _expression)
    assert _result == ["key", "list[0]", "list[1]", "list[2]"]

    _expression = "list[1]"
    _result = jmespath.search(_data, _expression)
    assert _result == "2"

    _data = {"key": {"subkey": "value"}}
    _expression = "key.subkey"
    _result = jmespath.search(_data, _expression)
    assert _result == "value"

    _expression = "key"
    _result = jmespath.search(_data, _expression)

    assert _result == {"subkey": "value"}

    _data = {"key": {"subkey": "value", "subkey2": "value2"}}
    _expression = "key.*"
    _result = jmespath.search(_data, _expression)
    assert _result == ["value", "value2"]

    _data = {"key": "value"}
    _expression = "."
    _result = jmespath.search(_data, _expression)
    assert _result == {"key": "value"}

    _expression = "*"
    _result = jmespath.search(_data, _expression)
    assert _result == ["value"]

    # Wildcard expression in a list
    _data = {"list": [{"key": 1}, {"key": 2}, {"key": 3}]}
    _expression = "list[*].key"
    _result = jmespath.search(_data, _expression)
    assert _result == [1, 2, 3]

    # Invalid expression
    _expression = ".nonexistent"
    with pytest.raises(FabricCLIError) as e:
        jmespath.search(_data, _expression)
    assert e.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert e.value.message == "Invalid jmespath query (https://jmespath.org)"

    # ------------------------------------------------------------------
    # Binary-content scenarios
    _data = {
        "key": "value",
        "binary": b"\x00\xff",
        "list": [b"\x01\x02", 1]
    }

    # No expression → path discovery
    _expression = None
    _result = jmespath.search(_data, _expression)
    assert _result == ['key', 'binary', 'list[0]', 'list[1]']

    # Directly selecting the bytes field
    _expression = "binary"
    _result = jmespath.search(_data, _expression)
    # bytes are not JSON-serialisable; search() falls back to str(result)
    assert _result == "b'\\x00\\xff'"

    # Selecting the list that contains a bytes element
    _expression = "list"
    _result = jmespath.search(_data, _expression)
    # dumps() redacts bytes inside collections
    assert _result == [b"\x01\x02", 1]

    # Selecting the entire data
    _expression = "."
    _result = jmespath.search(_data, _expression)
    assert _result == {'binary': b'\x00\xff', 'key': 'value', 'list': [b'\x01\x02', 1]}


def test_replace():

    _data = [{"key": "value"}, {"key": "value2"}]
    _expression = "[0].key"
    _new_value = "new_value"
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == [{"key": "new_value"}, {"key": "value2"}]

    _expression = "[1]"
    _new_value = {"key": "new_value"}
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == [{"key": "new_value"}, {"key": "new_value"}]

    _data = {"key": "value"}
    _expression = "key"
    _new_value = "new_value"
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": "new_value"}

    _data = {"key": "value", "list": [1, 2, 3]}
    _expression = "list[1]"
    _new_value = 99
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": "value", "list": [1, 99, 3]}

    _data = {"key": "value", "list": [1, 2, 3]}
    _expression = "list"
    _new_value = [99, 100]
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": "value", "list": [99, 100]}

    _data = {"key": "value", "list": [1, 2, 3]}
    _expression = "list[1]"
    _new_value = [99, 100]
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": "value", "list": [1, [99, 100], 3]}

    _data = {"key": "value", "list": [1, 2, 3]}
    _expression = "key"
    _new_value = {"subkey": "value"}
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": {"subkey": "value"}, "list": [1, 2, 3]}

    # Nested key with array index
    _data = {"key": {"value": [1, 2, 3]}}
    _expression = "key.value[1]"
    _new_value = 99
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": {"value": [1, 99, 3]}}

    # Nested array index
    _data = {"key": {"value": [{"key.value"}, {"list": [1, 2, 3]}, {}]}}
    _expression = "key.value[1].list[1]"
    _new_value = 99
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": {"value": [{"key.value"}, {"list": [1, 99, 3]}, {}]}}

    # Invalid expression
    _data = {"key": "value", "list": [1, 2, 3]}
    _expression = ".nonexistent"
    _new_value = "new_value"
    _result = jmespath.replace(_data, _expression, _new_value)
    assert _result == {"key": "value", "list": [1, 2, 3], "nonexistent": "new_value"}

    # Modify all second elements in a list of dictionaries => Unsupported
    _data = {"list": [{"key": 1}, {"key": 2}, {"key": 3}]}
    _expression = "list[*].key"
    _new_value = 99
    with pytest.raises(ValueError) as e:
        jmespath.replace(_data, _expression, _new_value)
    assert str(e.value) == "Wildcards are not supported in array indexing"

    # Wildcard expression in a parent
    _data = {
        "key": {"subkey": "value", "subkey2": "value2"},
        "key2": {"subkey": "value", "subkey2": "value2"},
    }
    _expression = "key.*"
    _new_value = "new_value"
    with pytest.raises(ValueError) as e:
        jmespath.replace(_data, _expression, _new_value)
    assert str(e.value) == "Wildcards are not supported"

    _expression = "*.key"
    _new_value = "new_value"
    with pytest.raises(ValueError) as e:
        jmespath.replace(_data, _expression, _new_value)
    assert str(e.value) == "Wildcards are not supported in parent expressions"

    # Empty expression
    _expression = ""
    _new_value = "new_value"
    with pytest.raises(ValueError) as e:
        jmespath.replace(_data, _expression, _new_value)
    assert str(e.value) == "The JMESPath expression cannot be empty"
