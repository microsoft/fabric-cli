# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

#!/usr/bin/env python3
"""
Test script for verifying multiple session isolation with different PPIDs.
This script is executed as a subprocess to test context file isolation between sessions.
"""
import os
import sys
import tempfile

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
    # Get the config directory from command line argument or create a secure temporary one
    if len(sys.argv) > 1:
        config_dir = sys.argv[1]
    else:
        # Create a secure temporary directory if no argument provided
        config_dir = tempfile.mkdtemp(prefix="test_fab_sessions_")

    fab_state_config.config_location = lambda: config_dir

    # Create contexts from two different "sessions" (processes)
    context = Context()
    session_id = context._get_context_session_id()
    expected_file = f"context-{session_id}.json"

    print(f"Session ID: {session_id}")
    print(f"Context file: {os.path.basename(context._context_file)}")
    print(f"Expected: {expected_file}")
    assert expected_file in context._context_file
    print("SUCCESS")


if __name__ == "__main__":
    main()
