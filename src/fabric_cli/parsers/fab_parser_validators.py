# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse


def validate_positive_int(value):
    """Validate that the value is a positive integer."""
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"'{value}' must be a positive integer")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer")