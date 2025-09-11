# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse

import pytest

from fabric_cli.parsers import fab_parser_validators


def test_validate_positive_int_with_valid_positive_integers():
    # Test various valid positive integers
    test_cases = [
        ("1", 1),
        ("10", 10),
        ("100", 100),
        ("999999", 999999),
    ]
    
    for input_value, expected in test_cases:
        result = fab_parser_validators.validate_positive_int(input_value)
        assert result == expected
        assert isinstance(result, int)


def test_validate_positive_int_with_zero_raises_error():
    with pytest.raises(argparse.ArgumentTypeError) as exc_info:
        fab_parser_validators.validate_positive_int("0")
    
    assert "'0' must be a positive integer" in str(exc_info.value)


def test_validate_positive_int_with_negative_integers_raises_error():
    with pytest.raises(argparse.ArgumentTypeError) as exc_info:
        fab_parser_validators.validate_positive_int("-1")
    
    assert "'-1' must be a positive integer" in str(exc_info.value)


def test_validate_positive_int_with_non_numeric_strings_raises_error():
    invalid_values = ["abc", "12.5", "1.0", "text", "12abc", "", " "]
    
    for value in invalid_values:
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            fab_parser_validators.validate_positive_int(value)
        
        assert f"'{value}' is not a valid integer" in str(exc_info.value)


def test_validate_positive_int_with_none_raises_error():
    with pytest.raises(TypeError):
        fab_parser_validators.validate_positive_int(None)
