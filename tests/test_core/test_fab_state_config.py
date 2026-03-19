# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import tempfile

import fabric_cli.core.fab_state_config as cfg


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

    def test_init_defaults__no_write_when_unchanged(self, tmp_path, monkeypatch):
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
