# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import tempfile

import pytest

from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils.fab_files import load_json_from_path


def test_load_good_json_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "tmp_test.json")
        with open(tmp_file, "w") as file:
            file.write('{"key": "value"}')
            file.flush()
        with open(tmp_file, "r") as file:
            data = load_json_from_path(file.name)
            assert data == {"key": "value"}


def test_load_bad_json_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "tmp_test.json")
        with open(tmp_file, "w") as file:
            file.write('{"key": "value"')
            file.flush()
        with open(tmp_file, "r") as file:
            with pytest.raises(FabricCLIError) as e:
                load_json_from_path(file.name)
            assert (
                e.value.message == f"The file at {file.name} is not a valid JSON file"
            )


def test_load_missing_json_file():
    with pytest.raises(FabricCLIError) as e:
        load_json_from_path("tests/data/missing.json")
    assert e.value.message == "The file at tests/data/missing.json was not found"
