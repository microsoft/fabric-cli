# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Lazy loading utilities for fabric CLI.
This module provides lazy loading for external dependencies to avoid
importing them until they are actually needed.
The module will be loaded only when the function is called for the first time and cached afterwards.
"""


def questionary():
    import questionary

    return questionary
