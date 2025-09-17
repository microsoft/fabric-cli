# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from unittest.mock import patch

from fabric_cli.core import fab_constant
from fabric_cli.core.completers import fab_config_completers


def test_complete_config_keys_returns_all_keys_when_no_prefix_should_return_all_keys():
    with patch(
        "fabric_cli.core.completers.fab_config_completers.sorted"
    ) as mock_sorted:
        mock_sorted.side_effect = lambda x: x

        result = fab_config_completers.complete_config_keys("")

        mock_sorted.assert_called_once()

        expected_keys = list(fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES.keys())
        assert set(result) == set(expected_keys)


def test_complete_config_keys_filters_by_prefix_should_return_matching_keys():
    result = fab_config_completers.complete_config_keys("mode")
    assert "mode" in result

    result = fab_config_completers.complete_config_keys("default")
    assert len(result) > 0
    for key in result:
        assert key.startswith("default")


def test_complete_config_keys_case_insensitive_should_return_same_results():
    result_lower = fab_config_completers.complete_config_keys("mode")
    result_upper = fab_config_completers.complete_config_keys("MODE")

    assert result_lower == result_upper


def test_complete_config_values_enum_keys_should_return_expected_values():
    args = Namespace()
    args.key = "mode"

    result = fab_config_completers.complete_config_values("", args)
    assert result == ["command_line", "interactive"]

    result = fab_config_completers.complete_config_values("inter", args)
    assert result == ["interactive"]


def test_complete_config_values_invalid_key_should_return_empty():
    args = Namespace()
    args.key = "invalid_key_that_does_not_exist"

    result = fab_config_completers.complete_config_values("", args)
    assert result == []


def test_complete_config_values_empty_key_should_return_empty():
    args = Namespace()
    args.key = ""

    result = fab_config_completers.complete_config_values("", args)
    assert result == []


def test_complete_config_values_valid_key_no_values_should_return_empty():
    args = Namespace()
    args.key = "default_capacity"

    result = fab_config_completers.complete_config_values("", args)

    assert result == []
