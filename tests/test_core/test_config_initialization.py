# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import tempfile
from unittest.mock import patch

import fabric_cli.core.fab_constant as constants
import fabric_cli.core.fab_state_config as config


def test_config_init_defaults_idempotent():
    """Test that init_defaults can be called multiple times safely"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "config.json")
        with patch.object(config, "config_file", tmp_file):
            # Call init_defaults multiple times
            config.init_defaults()
            config.init_defaults()
            config.init_defaults()

            cfg = config.read_config(tmp_file)
            # Should have all the default values
            for key, default_value in constants.CONFIG_DEFAULT_VALUES.items():
                assert cfg.get(key) == default_value


def test_config_init_preserves_existing_values():
    """Test that init_defaults preserves existing user configurations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "config.json")
        with patch.object(config, "config_file", tmp_file):
            # Set some custom values first
            config.set_config("debug_enabled", "true")
            config.set_config("custom_setting", "user_value")

            # Call init_defaults
            config.init_defaults()

            cfg = config.read_config(tmp_file)
            # Custom values should be preserved
            assert cfg.get("debug_enabled") == "true"
            assert cfg.get("custom_setting") == "user_value"
            # Defaults should be added for missing keys
            assert (
                cfg.get("cache_enabled")
                == constants.CONFIG_DEFAULT_VALUES["cache_enabled"]
            )


def test_config_init_adds_new_keys():
    """Test that init_defaults adds new configuration keys from upgrades"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "config.json")
        with patch.object(config, "config_file", tmp_file):
            # Start with empty config
            config.write_config({})

            # Call init_defaults
            config.init_defaults()

            cfg = config.read_config(tmp_file)
            # Should have all default keys
            for key in constants.FAB_CONFIG_KEYS_TO_VALID_VALUES:
                if key in constants.CONFIG_DEFAULT_VALUES:
                    assert key in cfg, f"Missing default key: {key}"


def test_legacy_config_key_migration():
    """Test that init_defaults handles migration of legacy config keys"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "config.json")
        with patch.object(config, "config_file", tmp_file):
            # Set up a config with legacy keys
            legacy_config = {
                "fab_cache_enabled": "false",  # Legacy key
                "debug_enabled": "true",  # Current key
            }
            config.write_config(legacy_config)

            # Call init_defaults to trigger migration
            config.init_defaults()

            cfg = config.read_config(tmp_file)
            # Legacy key should be migrated to new key
            assert cfg.get("cache_enabled") == "false"  # Migrated value
            assert "fab_cache_enabled" not in cfg  # Legacy key removed
            assert cfg.get("debug_enabled") == "true"  # Existing key preserved
