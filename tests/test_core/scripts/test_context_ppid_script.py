# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

#!/usr/bin/env python3
"""
Test script for verifying parent process ID context file naming.
This script is executed as a subprocess to test PPID-based context file isolation.
"""
import os
import sys

# Add the src directory to the path so we can import fabric_cli modules
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "src",
    ),
)

from fabric_cli.core import fab_state_config
from fabric_cli.core.fab_context import Context


def main():
    # Get the config directory from command line argument
    config_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_fab_config"

    fab_state_config.config_location = lambda: config_dir

    # Create a context and check the file path
    context = Context()
    session_id = context._get_context_session_id()
    expected_filename = f"context-{session_id}.json"
    actual_filename = os.path.basename(context._context_file)

    print(f"Expected: {expected_filename}")
    print(f"Actual: {actual_filename}")

    assert (
        expected_filename in context._context_file
    ), f"Expected {expected_filename} to be in {context._context_file}"
    print("SUCCESS")


if __name__ == "__main__":
    main()
