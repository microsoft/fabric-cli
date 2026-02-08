# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys
from unittest.mock import patch

import pytest


class TestMainModule:
    """Test suite for main module functionality."""

    def test_main_no_args_starts_interactive_mode_success(self):
        """Test that running 'fab' without arguments automatically enters interactive mode."""
        with patch("fabric_cli.main.start_interactive_mode") as mock_start_interactive:
            from fabric_cli.main import main

            with patch.object(sys, 'argv', ['fab']):
                with patch("fabric_cli.core.fab_parser_setup.get_global_parser_and_subparsers") as mock_get_parsers:
                    mock_parser = type('MockParser', (), {
                        'parse_args': lambda: type('Args', (), {
                            'command': None,
                            'version': False
                        })(),
                        'set_mode': lambda mode: None
                    })()
                    mock_subparsers = object()
                    mock_get_parsers.return_value = (mock_parser, mock_subparsers)
                    
                    with patch("fabric_cli.core.fab_state_config.init_defaults"):
                        main()
                    
                    mock_start_interactive.assert_called_once()

    def test_start_interactive_mode_directly_success(self):
        """Test that start_interactive_mode can be called directly without infinite loops."""
        # Mock the InteractiveCLI to prevent actual interactive session
        with patch("fabric_cli.core.fab_interactive.InteractiveCLI") as mock_interactive_cli:
            from unittest.mock import Mock
            
            mock_cli_instance = Mock()
            mock_cli_instance._is_running = False
            mock_cli_instance.start_interactive = Mock()  # Mock the start_interactive method
            mock_interactive_cli.return_value = mock_cli_instance
            
            from fabric_cli.core.fab_interactive import start_interactive_mode
            start_interactive_mode()
            
            mock_interactive_cli.assert_called_once()
            mock_cli_instance.start_interactive.assert_called_once()