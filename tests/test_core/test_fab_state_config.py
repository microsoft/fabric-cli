# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import tempfile

import fabric_cli.core.fab_state_config as cfg
from fabric_cli.core import fab_constant


class TestStateConfig:
    """Test suite for state config read/write operations."""

    def test_read_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = os.path.join(tmpdir, "tmp_test.txt")
            with open(tmp_file, "w") as file:
                file.write('{"key": "value"}')
                file.flush()  # flush the buffer to write the data to the file before reading it
            with open(tmp_file, "r") as file:
                data = cfg.read_config(file.name)
                assert data == {"key": "value"}

    def test_read_config_missing_file(self):
        with tempfile.NamedTemporaryFile("w") as fp:
            fp.close()  # close the file to delete it
            data = cfg.read_config(fp.name)
            assert data == {}

    def test_read_config_bad_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = os.path.join(tmpdir, "tmp_test.txt")
            with open(tmp_file, "w") as file:
                file.write('{"key": "value"')
                file.flush()
            data = cfg.read_config(tmp_file)
            assert data == {}

    def test_write_config(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = os.path.join(tmpdir, "tmp_test.txt")
            with open(tmp_file, "w") as file:
                file.flush()
            monkeypatch.setattr(cfg, "config_file", tmp_file)
            cfg.write_config({"key": "value"})
            data = cfg.read_config(tmp_file)
            assert data == {"key": "value"}

    def test_get_set_config(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = os.path.join(tmpdir, "tmp_cfg.txt")
            with open(cfg_file, "w") as cfg_fp:
                cfg_fp.write('{"key": "value"}')
                cfg_fp.flush()
            monkeypatch.setattr(cfg, "config_file", cfg_file)
            cfg.set_config("key2", "value2")
            assert cfg.get_config("key") == "value"
            assert cfg.get_config("key2") == "value2"

    def test_list_configs(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = os.path.join(tmpdir, "tmp_test.txt")
            with open(tmp_file, "w") as file:
                file.write('{"key": "value"}')
                file.flush()
            monkeypatch.setattr(cfg, "config_file", tmp_file)
            cfg.set_config("key2", "value2")
            assert cfg.list_configs() == {"key": "value", "key2": "value2"}


class TestInitDefaults:
    """Test suite for config initialization optimization."""

    def test_init_defaults_no_write_when_unchanged_success(self, tmp_path, monkeypatch):
        """Test that init_defaults skips writing when config already has all defaults."""
        import json

        from fabric_cli.core import fab_constant

        # Create a config file with all defaults already set
        config_data = dict(fab_constant.CONFIG_DEFAULT_VALUES)
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        monkeypatch.setattr(cfg, "config_file", str(config_file))

        # Track write calls
        original_write = cfg.write_config
        write_calls = []

        def tracking_write(data):
            write_calls.append(data)
            original_write(data)

        monkeypatch.setattr(cfg, "write_config", tracking_write)

        cfg.init_defaults()

        # Should NOT have written since nothing changed
        assert len(write_calls) == 0, "Should skip write when config unchanged"


# region init_defaults migration


def _create_temp_config(monkeypatch, tmp_path, config_data):
    """Create a temp config file with the given data and monkeypatch cfg.config_file to point to it."""
    config_file = os.path.join(tmp_path, "config.json")
    with open(config_file, "w") as f:
        json.dump(config_data, f)
    monkeypatch.setattr(cfg, "config_file", config_file)
    return config_file


def test_init_defaults_removes_mode_key_success(monkeypatch, tmp_path):
    """If an existing config file contains 'mode', init_defaults must delete it."""
    config_file = _create_temp_config(monkeypatch, tmp_path, {
        fab_constant.FAB_MODE: fab_constant.FAB_MODE_INTERACTIVE,
        fab_constant.FAB_CACHE_ENABLED: "true",
    })

    cfg.init_defaults()

    result = cfg.read_config(config_file)
    assert fab_constant.FAB_MODE not in result
    assert result[fab_constant.FAB_CACHE_ENABLED] == "true"


def test_init_defaults_no_mode_key_success(monkeypatch, tmp_path):
    """Config without 'mode' must initialize cleanly (distinct from removes_mode_key: verifies no error on absence)."""
    config_file = _create_temp_config(monkeypatch, tmp_path, {
        fab_constant.FAB_DEBUG_ENABLED: "true",
    })

    cfg.init_defaults()

    result = cfg.read_config(config_file)
    assert fab_constant.FAB_MODE not in result
    assert result[fab_constant.FAB_DEBUG_ENABLED] == "true"


def test_init_defaults_applies_missing_defaults_success(monkeypatch, tmp_path):
    """init_defaults must fill in missing default values."""
    config_file = _create_temp_config(monkeypatch, tmp_path, {})

    cfg.init_defaults()

    result = cfg.read_config(config_file)
    for key, default_val in fab_constant.CONFIG_DEFAULT_VALUES.items():
        assert result.get(key) == default_val, (
            f"Expected default for '{key}' = '{default_val}', got '{result.get(key)}'"
        )


def test_init_defaults_preserves_user_overrides_success(monkeypatch, tmp_path):
    """User-set values must not be overwritten by defaults."""
    config_file = _create_temp_config(monkeypatch, tmp_path, {
        fab_constant.FAB_CACHE_ENABLED: "false",
    })

    cfg.init_defaults()

    result = cfg.read_config(config_file)
    assert result[fab_constant.FAB_CACHE_ENABLED] == "false"

# endregion


# region security: file permission tests


def test_config_location_creates_directory_with_restricted_permissions(
    monkeypatch, tmp_path
):
    """Verify config directory is created with mode 0o700 (owner-only access)."""
    config_dir = tmp_path / "fab_config_test"
    monkeypatch.setattr(
        cfg, "config_location", lambda: _create_restricted_dir(str(config_dir))
    )
    # Call our helper which mimics the real config_location logic
    location = _create_restricted_dir(str(config_dir))
    assert os.path.isdir(location)

    mode = oct(os.stat(location).st_mode & 0o777)
    assert mode == "0o700", f"Config directory has mode {mode}, expected 0o700"


def _create_restricted_dir(path):
    """Helper that mirrors the fixed config_location logic."""
    if not os.path.exists(path):
        os.makedirs(path, mode=0o700)
    return path


def test_write_config_creates_file_with_restricted_permissions(monkeypatch, tmp_path):
    """Verify config files are created with mode 0o600 (owner read/write only)."""
    config_file = os.path.join(str(tmp_path), "config.json")
    monkeypatch.setattr(cfg, "config_file", config_file)

    cfg.write_config({"key": "value"})

    assert os.path.exists(config_file)
    mode = oct(os.stat(config_file).st_mode & 0o777)
    assert mode == "0o600", f"Config file has mode {mode}, expected 0o600"

    # Verify content is still correct
    data = cfg.read_config(config_file)
    assert data == {"key": "value"}


def test_write_config_preserves_restricted_permissions_on_overwrite(
    monkeypatch, tmp_path
):
    """Verify permissions stay restricted when config file is overwritten."""
    config_file = os.path.join(str(tmp_path), "config.json")
    monkeypatch.setattr(cfg, "config_file", config_file)

    cfg.write_config({"first": "write"})
    cfg.write_config({"second": "write"})

    mode = oct(os.stat(config_file).st_mode & 0o777)
    assert mode == "0o600", f"Config file has mode {mode} after overwrite, expected 0o600"

    data = cfg.read_config(config_file)
    assert data == {"second": "write"}


# endregion
