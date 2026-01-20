# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import os
import platform
import time
from unittest.mock import ANY, patch

import pytest

import fabric_cli.commands.fs.fab_fs_export as fab_export
from fabric_cli.client import fab_api_item
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.utils import cli_path_join

new_name_index = 1


class TestImport:
    # Update existing tests
    def test_import_update_existing_notebook_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.NOTEBOOK,
            cli_executor,
        )

    def test_import_update_existing_sjd_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.SPARK_JOB_DEFINITION,
            cli_executor,
        )

    def test_import_update_existing_data_pipeline_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.DATA_PIPELINE,
            cli_executor,
        )

    def test_import_update_existing_report_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.REPORT,
            cli_executor,
        )

    def test_import_update_existing_semantic_model_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.SEMANTIC_MODEL,
            cli_executor,
        )

    def test_import_update_existing_kql_db_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.KQL_DATABASE,
            cli_executor,
        )

    def test_import_update_existing_kql_qs_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.KQL_QUERYSET,
            cli_executor,
        )

    def test_import_update_existing_eventhouse_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.EVENTHOUSE,
            cli_executor,
        )

    def test_import_update_existing_mirrored_db_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.MIRRORED_DATABASE,
            cli_executor,
        )

    def test_import_update_existing_reflex_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.REFLEX,
            cli_executor,
        )

    def test_import_update_existing_kql_dashboard_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        spy_update_item_definition,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
    ):
        _import_update_existing_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            mock_print_warning,
            spy_update_item_definition,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.KQL_DASHBOARD,
            cli_executor,
        )

    # Create new tests
    def test_import_home_directory_path_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        monkeypatch,
    ):
        # Setup mock home directory
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        home_dir_env = "USERPROFILE" if platform.system() == "Windows" else "HOME"
        monkeypatch.setenv(home_dir_env, str(home_dir))

        # Create test directory under mock home
        input_dir = home_dir / "test_import"
        input_dir.mkdir()

        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            f"~/test_import",
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.NOTEBOOK,
            cli_executor,
        )

    def test_import_create_new_sqldb_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.SQL_DATABASE,
            cli_executor,
        )

    def test_import_create_new_notebook_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.NOTEBOOK,
            cli_executor,
        )

    def test_import_create_new_sjd_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.SPARK_JOB_DEFINITION,
            cli_executor,
        )

    def test_import_create_new_data_pipeline_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.DATA_PIPELINE,
            cli_executor,
        )

    def test_import_create_new_report_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.REPORT,
            cli_executor,
        )

    def test_import_create_new_semantic_model_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.SEMANTIC_MODEL,
            cli_executor,
        )

    def test_import_create_new_kql_db_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.KQL_DATABASE,
            cli_executor,
        )

    def test_import_create_new_kql_qs_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.KQL_QUERYSET,
            cli_executor,
        )

    def test_import_create_new_eventhouse_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.EVENTHOUSE,
            cli_executor,
        )

    def test_import_create_new_mirrored_db_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.MIRRORED_DATABASE,
            cli_executor,
        )

    def test_import_create_new_reflex_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.REFLEX,
            cli_executor,
        )

    def test_import_create_new_kql_dashboard_item_success(
        self,
        item_factory,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
    ):
        _import_create_new_item_success(
            item_factory,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.KQL_DASHBOARD,
            cli_executor,
        )

    # Non Supported items tests
    def test_import_create_new_dashboard_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.DASHBOARD,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_datamart_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.DATAMART,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_lakehouse_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.LAKEHOUSE,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_mirrored_warehouse_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.MIRRORED_WAREHOUSE,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_ml_experiment_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.ML_EXPERIMENT,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_ml_model_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.ML_MODEL,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_paginated_report_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.PAGINATED_REPORT,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_sql_endpoint_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.SQL_ENDPOINT,
            cli_executor,
            assert_fabric_cli_error,
        )

    def test_import_create_new_warehouse_item_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor,
        assert_fabric_cli_error,
    ):
        _import_create_new_item_fail(
            workspace,
            mock_print_done,
            tmp_path,
            spy_create_item,
            mock_print_grey,
            upsert_item_to_cache,
            ItemType.WAREHOUSE,
            cli_executor,
            assert_fabric_cli_error,
        )

    # Test with lakehouse path
    def test_import_lakehouse_path_fail(
        self,
        workspace,
        item_factory,
        mock_print_done,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
        item_type=ItemType.NOTEBOOK,
    ):
        # Setup
        lh_item = item_factory(ItemType.LAKEHOUSE)
        item_name = f"newName.{str(item_type)}"
        new_item_path = cli_path_join(workspace.full_path, item_name)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_grey.reset_mock()
        upsert_item_to_cache.reset_mock()
        spy_create_item.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"import {new_item_path} --input {lh_item.full_path}/Files --force"
        )

        # Assert
        assert_fabric_cli_error(fab_constant.ERROR_NOT_SUPPORTED)
        mock_print_grey.assert_not_called()
        spy_create_item.assert_not_called()
        mock_print_done.assert_not_called()
        upsert_item_to_cache.assert_not_called()

    def test_import_item_wrong_format_fail(
        self,
        workspace,
        mock_print_done,
        tmp_path,
        spy_create_item,
        mock_print_grey,
        upsert_item_to_cache,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
    ):
        # Setup
        item_name = f"newName.{str(ItemType.NOTEBOOK)}"
        new_item_path = cli_path_join(workspace.full_path, item_name)

        # Execute command
        cli_executor.exec_command(
            f"import {new_item_path} --input {str(tmp_path)} --format pyt"
        )

        # Assert
        assert_fabric_cli_error(
            fab_constant.ERROR_INVALID_INPUT,
            "Invalid format. Only '.py' and '.ipynb' are supported",
        )
        mock_print_grey.assert_not_called()
        spy_create_item.assert_not_called()
        mock_print_done.assert_not_called()
        upsert_item_to_cache.assert_not_called()


# region Helper Methods
def _import_create_new_item_success(
    item_factory,
    mock_print_done,
    tmp_path,
    spy_create_item,
    mock_print_grey,
    upsert_item_to_cache,
    item_type: ItemType,
    cli_executor: CLIExecutor,
):
    # Setup
    item = item_factory(item_type)
    
    # TODO: delete this line after mirrored db fix the API GAP for Create
    if item_type == ItemType.MIRRORED_DATABASE:
        time.sleep(60)
    
    export(item.full_path, output=os.path.expanduser(str(tmp_path)))

    # Reset mock
    mock_print_done.reset_mock()
    mock_print_grey.reset_mock()
    upsert_item_to_cache.reset_mock()
    spy_create_item.reset_mock()

    # Execute command
    item_path = item.full_path
    global new_name_index
    new_item_path = item_path.replace(
        item.display_name, item.display_name + "_new_" + str(new_name_index)
    )
    new_name_index += 1
    new_item_path = item_path.replace(
        item.display_name, item.display_name + "_new_" + str(new_name_index)
    )
    with patch("fabric_cli.utils.fab_ui.prompt_confirm", return_value=True):
        cli_executor.exec_command(
            f"import {new_item_path} --input {str(tmp_path)}/{item.name} --force"
        )

    # Assert
    mock_print_grey.assert_called_once()
    assert "Importing " in mock_print_grey.call_args[0][0]
    spy_create_item.assert_called_once()
    mock_print_done.assert_called_once()
    upsert_item_to_cache.assert_called_once()


def _import_update_existing_item_success(
    item_factory,
    mock_print_done,
    tmp_path,
    mock_print_warning,
    spy_update_item_definition,
    mock_print_grey,
    upsert_item_to_cache,
    item_type: ItemType,
    cli_executor: CLIExecutor,
):
    # Setup
    item = item_factory(item_type)
    
    # TODO: delete this line after mirrored db fix the API GAP for Create
    if item_type == ItemType.MIRRORED_DATABASE:
        time.sleep(60)
    
    export(item.full_path, output=str(tmp_path))

    # Reset mock
    mock_print_done.reset_mock()
    mock_print_warning.reset_mock()
    mock_print_grey.reset_mock()
    upsert_item_to_cache.reset_mock()

    # Execute command
    cli_executor.exec_command(
        f"import {item.full_path} --input {str(tmp_path)}/{item.name} --force"
    )

    # Assert
    mock_print_warning.assert_called_once()
    mock_print_grey.assert_called_once()
    assert "Importing (update) " in mock_print_grey.call_args[0][0]
    spy_update_item_definition.assert_called_once()
    mock_print_done.assert_called_once()
    upsert_item_to_cache.assert_called_once()


def _import_create_new_item_fail(
    workspace,
    mock_print_done,
    tmp_path,
    spy_create_item,
    mock_print_grey,
    upsert_item_to_cache,
    item_type: ItemType,
    cli_executor: CLIExecutor,
    assert_fabric_cli_error,
):
    # Setup
    item_name = f"newName.{str(item_type)}"
    new_item_path = cli_path_join(workspace.full_path, item_name)

    # Execute command
    cli_executor.exec_command(f"import {new_item_path} --input {str(tmp_path)} --force")

    # Assert
    assert_fabric_cli_error(fab_constant.ERROR_UNSUPPORTED_COMMAND)
    mock_print_grey.assert_not_called()
    spy_create_item.assert_not_called()
    mock_print_done.assert_not_called()
    upsert_item_to_cache.assert_not_called()


def export(path, output, force=True):
    args = _build_export_args(path, output, force)
    context = handle_context.get_command_context(args.path)
    fab_export.exec_command(args, context)


def _build_export_args(path, output, force=True):
    return argparse.Namespace(
        command="export",
        acl_subcommand="export",
        command_path="export",
        path=path,
        output=output,
        force=force,
    )


@pytest.fixture()
def spy_update_item_definition():
    with patch(
        "fabric_cli.client.fab_api_item.update_item_definition",
        side_effect=fab_api_item.update_item_definition,
    ) as mock:
        yield mock


@pytest.fixture()
def spy_create_item():
    with patch(
        "fabric_cli.client.fab_api_item.create_item",
        side_effect=fab_api_item.create_item,
    ) as mock:
        yield mock


@pytest.fixture()
def upsert_item_to_cache():
    with patch("fabric_cli.utils.fab_mem_store.upsert_item_to_cache") as mock:
        yield mock


# On windows default writing to file is \r\n while in linux is \n. Keeping it as \n for all
@pytest.fixture(autouse=True, scope="module")
def mock_open():
    def custom_open(file_path, mode, *args, **kwargs):
        if mode == "w" and kwargs["encoding"] == "utf-8":
            return open(file_path, mode, encoding="utf-8", newline="\n")
        else:
            return open(file_path, mode)

    with patch("fabric_cli.utils.fab_storage.open", side_effect=custom_open):
        yield


# endregion
