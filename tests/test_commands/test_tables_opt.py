# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from argparse import Namespace
from unittest.mock import patch

import pytest

from fabric_cli.commands.tables import fab_tables_opt


@pytest.fixture
def table_maintenance_args():
    """Provide a default Namespace for table maintenance tests."""
    return Namespace(
        jobType=None,
        lakehouse_path="/workspace/lakehouse",
        jobs_command=None,
        configuration='{"optimize": true}',
        table_name="my_table",
        schema=None,
        input=None,
        params=None,
        path=None,
    )


def test_exec_command_cleans_up_temp_file_success(table_maintenance_args):
    """Verify the temporary config file is removed after job execution."""
    created_temp_files = []

    def mock_run_command(a):
        created_temp_files.append(a.input)
        assert os.path.exists(a.input), "Temp file should exist during job execution"

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.jobs.run_command",
        side_effect=mock_run_command,
    ):
        fab_tables_opt.exec_command(table_maintenance_args)

    assert len(created_temp_files) == 1
    assert not os.path.exists(
        created_temp_files[0]
    ), "Temp file should be cleaned up after job execution"


def test_exec_command_cleans_up_temp_file_on_job_failure(table_maintenance_args):
    """Verify the temporary config file is removed even if the job fails."""
    created_temp_files = []

    def mock_run_command(a):
        created_temp_files.append(a.input)
        raise RuntimeError("Job failed")

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.jobs.run_command",
        side_effect=mock_run_command,
    ):
        with pytest.raises(RuntimeError, match="Job failed"):
            fab_tables_opt.exec_command(table_maintenance_args)

    assert len(created_temp_files) == 1
    assert not os.path.exists(
        created_temp_files[0]
    ), "Temp file should be cleaned up even when job fails"


def test_exec_command_cleans_up_temp_file_on_open_failure(table_maintenance_args):
    """Verify the temp file is removed when open() raises a PermissionError."""
    import tempfile

    created_temp_paths = []
    original_ntf = tempfile.NamedTemporaryFile
    original_open = open

    def capturing_ntf(*a, **kw):
        tf = original_ntf(*a, **kw)
        created_temp_paths.append(tf.name)
        return tf

    def mock_open(path, *args, **kwargs):
        # Raise PermissionError only for the write to the captured temp file
        mode = args[0] if args else kwargs.get("mode", "r")
        if created_temp_paths and path == created_temp_paths[0] and mode == "w":
            raise PermissionError("Permission denied")
        return original_open(path, *args, **kwargs)

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.tempfile.NamedTemporaryFile",
        side_effect=capturing_ntf,
    ):
        with patch("builtins.open", side_effect=mock_open):
            with pytest.raises(PermissionError, match="Permission denied"):
                fab_tables_opt.exec_command(table_maintenance_args)

    assert len(created_temp_paths) == 1
    assert not os.path.exists(
        created_temp_paths[0]
    ), "Temp file should be cleaned up when open() fails"


def test_exec_command_cleans_up_temp_file_on_serialization_failure(
    table_maintenance_args,
):
    """Verify the temp file is removed when json.dump raises due to non-serializable config."""
    import tempfile

    created_temp_paths = []
    original_ntf = tempfile.NamedTemporaryFile

    def capturing_ntf(*a, **kw):
        tf = original_ntf(*a, **kw)
        created_temp_paths.append(tf.name)
        return tf

    def mock_json_dump(*args, **kwargs):
        raise TypeError("Object of type set is not JSON serializable")

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.tempfile.NamedTemporaryFile",
        side_effect=capturing_ntf,
    ):
        with patch(
            "fabric_cli.commands.tables.fab_tables_opt.json.dump",
            side_effect=mock_json_dump,
        ):
            with pytest.raises(TypeError, match="not JSON serializable"):
                fab_tables_opt.exec_command(table_maintenance_args)

    assert len(created_temp_paths) == 1
    assert not os.path.exists(
        created_temp_paths[0]
    ), "Temp file should be cleaned up when serialization fails"


def test_exec_command_writes_correct_config_success():
    """Verify the temp file contains the expected job configuration."""
    args = Namespace(
        jobType=None,
        lakehouse_path="/workspace/lakehouse",
        jobs_command=None,
        configuration='{"optimize": true}',
        table_name="sales",
        schema="dbo",
        input=None,
        params=None,
        path=None,
    )

    def mock_run_command(a):
        with open(a.input, "r") as f:
            config = json.load(f)
        assert config["tableName"] == "sales"
        assert config["schemaName"] == "dbo"
        assert config["optimize"] is True

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.jobs.run_command",
        side_effect=mock_run_command,
    ):
        fab_tables_opt.exec_command(args)
