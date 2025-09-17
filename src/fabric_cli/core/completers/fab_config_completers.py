# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import List

from fabric_cli.core import fab_constant


def complete_config_keys(prefix: str, **kwargs) -> List[str]:
    keys = list(fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES.keys())
    matching_keys = [key for key in keys if key.lower().startswith(prefix.lower())]

    return sorted(matching_keys)


def complete_config_values(prefix: str, parsed_args: Namespace, **kwargs) -> List[str]:
    if not hasattr(parsed_args, "key") or not parsed_args.key:
        return []

    key = parsed_args.key.lower()

    if key not in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
        return []

    valid_values = fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES[key]

    if not valid_values:
        return []

    matching_values = [
        value for value in valid_values if value.lower().startswith(prefix.lower())
    ]

    return sorted(matching_values)
