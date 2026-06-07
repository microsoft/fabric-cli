# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from argparse import Namespace
from unittest.mock import patch

import pytest

from fabric_cli.commands.tables import fab_tables_opt


def test_exec_command_cleans_up_temp_file():
    """Verify the temporary config file is removed after job execution."""
    args = Namespace(
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

    created_temp_files = []

    def mock_run_command(a):
        # Capture the temp file path before it gets cleaned up
        created_temp_files.append(a.input)
        assert os.path.exists(a.input), "Temp file should exist during job execution"

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.jobs.run_command",
        side_effect=mock_run_command,
    ):
        fab_tables_opt.exec_command(args)

    assert len(created_temp_files) == 1
    assert not os.path.exists(
        created_temp_files[0]
    ), "Temp file should be cleaned up after job execution"


def test_exec_command_cleans_up_temp_file_on_error():
    """Verify the temporary config file is removed even if the job fails."""
    args = Namespace(
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

    created_temp_files = []

    def mock_run_command(a):
        created_temp_files.append(a.input)
        raise RuntimeError("Job failed")

    with patch(
        "fabric_cli.commands.tables.fab_tables_opt.jobs.run_command",
        side_effect=mock_run_command,
    ):
        with pytest.raises(RuntimeError, match="Job failed"):
            fab_tables_opt.exec_command(args)

    assert len(created_temp_files) == 1
    assert not os.path.exists(
        created_temp_files[0]
    ), "Temp file should be cleaned up even when job fails"


def test_exec_command_writes_correct_config_to_temp_file():
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
