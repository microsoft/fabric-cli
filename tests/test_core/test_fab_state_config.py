# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import tempfile

import fabric_cli.core.fab_state_config as cfg


def test_read_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "tmp_test.txt")
        with open(tmp_file, "w") as file:
            file.write('{"key": "value"}')
            file.flush()  # flush the buffer to write the data to the file before reading it
        with open(tmp_file, "r") as file:
            data = cfg.read_config(file.name)
            assert data == {"key": "value"}


def test_read_config_missing_file():
    with tempfile.NamedTemporaryFile("w") as fp:
        fp.close()  # close the file to delete it
        data = cfg.read_config(fp.name)
        assert data == {}


def test_read_config_bad_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "tmp_test.txt")
        with open(tmp_file, "w") as file:
            file.write('{"key": "value"')
            file.flush()
        data = cfg.read_config(tmp_file)
        assert data == {}


def test_write_config(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "tmp_test.txt")
        with open(tmp_file, "w") as file:
            file.flush()
        monkeypatch.setattr(cfg, "config_file", tmp_file)
        cfg.write_config({"key": "value"})
        data = cfg.read_config(tmp_file)
        assert data == {"key": "value"}


def test_get_set_config(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "tmp_cfg.txt")
        with open(cfg_file, "w") as cfg_fp:
            cfg_fp.write('{"key": "value"}')
            cfg_fp.flush()
        monkeypatch.setattr(cfg, "config_file", cfg_file)
        cfg.set_config("key2", "value2")
        assert cfg.get_config("key") == "value"
        assert cfg.get_config("key2") == "value2"


def test_list_configs(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "tmp_test.txt")
        with open(tmp_file, "w") as file:
            file.write('{"key": "value"}')
            file.flush()
        monkeypatch.setattr(cfg, "config_file", tmp_file)
        cfg.set_config("key2", "value2")
        assert cfg.list_configs() == {"key": "value", "key2": "value2"}
