# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for the global parameters parser module."""

import argparse

import pytest

from fabric_cli.parsers import fab_global_params


def test_add_global_flags():
    """Test adding global flags to a parser."""
    # Setup
    parser = argparse.ArgumentParser()

    # Execute
    fab_global_params.add_global_flags(parser)

    # Verify
    # Get all flags
    all_flags = [action for action in parser._actions if action.option_strings]

    # Check help flag
    help_flag = next(a for a in all_flags if "-help" in a.option_strings)
    assert help_flag.dest == "help"
    assert help_flag.option_strings == ["-help"]

    # Check output format flag
    format_flag = next(a for a in all_flags if "--output_format" in a.option_strings)
    assert format_flag.dest == "output_format"
    assert format_flag.option_strings == ["--output_format"]

    assert format_flag.choices == ["json", "text"]
    assert not format_flag.required
    assert "Override output format type" in format_flag.help


def test_add_global_flags_parser_integration():
    """Test that global flags work correctly in parser."""
    # Setup
    parser = argparse.ArgumentParser()
    fab_global_params.add_global_flags(parser)

    # Test help flag (should raise SystemExit)
    with pytest.raises(SystemExit):
        parser.parse_args(["-help"])

    # Test output format flag with valid choices
    args = parser.parse_args(["--output_format", "json"])
    assert args.output_format == "json"

    args = parser.parse_args(["--output_format", "text"])
    assert args.output_format == "text"

    # Test invalid output format (should raise SystemExit)
    with pytest.raises(SystemExit):
        parser.parse_args(["--output_format", "invalid"])
