# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import os
from unittest.mock import patch
import tempfile

import pytest

import fabric_cli.commands.labels.fab_labels_list_local as fab_labels_list_local
import fabric_cli.core.fab_constant as constant
from fabric_cli.core import fab_state_config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.errors import ErrorMessages
from tests.test_commands.data.static_test_data import StaticTestData

LABELS_ABS_PATH = None
MISSING_LABELS_ABS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "missing_labels.json"
)
INVALID_ENTRIES_LABELS_ABS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "invalid_labels_entries.json"
)
INVALID_JSON_LABELS_ABS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "invalid_json_labels.json"
)


class TestLabels:
    @pytest.fixture(scope="class", autouse=True)
    def setup_config_fab_definition_labels(
        self, cli_executor, test_data: StaticTestData
    ):

        old_value = fab_state_config.get_config(constant.FAB_LOCAL_DEFINITION_LABELS)
        labels = test_data.labels
        if not labels or len(labels) < 2:
            raise Exception("Unexpected error: labels were not defined correctly")

        # Create a temporary JSON file with the labels under a 'labels' property
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w", encoding="utf-8"
        )

        # Convert label objects to dicts for JSON serialization
        serializable_labels = [
            {
                "name": label.name,
                "id": label.id,
            }
            for label in labels
        ]
        json.dump({"labels": serializable_labels}, tmp_file)
        tmp_file.close()
        LABELS_ABS_PATH = tmp_file.name

        command_str = (
            f"config set {constant.FAB_LOCAL_DEFINITION_LABELS} {LABELS_ABS_PATH}"
        )
        cli_executor.exec_command(command_str)
        yield

        command_str = f"config set {constant.FAB_LOCAL_DEFINITION_LABELS} {old_value}"
        cli_executor.exec_command(command_str)

        # Clean up the temp file after all tests in the class
        os.remove(LABELS_ABS_PATH)

    # region labels SET

    # IMPORTANT!!!
    # test_labels_set tests are relay on the labels file which contain the label's ids for the test user.
    # When trying to create new vcr, if the tests are failing, please check:
    # 1. Values defined in labels json file are align with the sensativity lables.
    # 2. The Information Protection settings in the Admin portal are enabled.

    def test_labels_set_lakehouse_with_force_success(
        self, item_factory, cli_executor, mock_print_done, test_data: StaticTestData
    ):
        # If lables values were changed or new labels were added, new recordings are required, please check the comment under region labels SET

        # Setup
        notebook = item_factory(ItemType.LAKEHOUSE)
        valid_label_name = test_data.labels[1].name
        # Reset mock
        mock_print_done.reset_mock()
        # Execute command
        command_str = f"label set {notebook.full_path} -n {valid_label_name} -f"
        cli_executor.exec_command(command_str)
        # Assert
        mock_print_done.assert_called()
        assert mock_print_done.call_args[0][0] == "Label set\n"

    def test_labels_set_without_force_success(
        self, item_factory, cli_executor, mock_print_done, test_data: StaticTestData
    ):
        # If lables values were changed or new labels were added, new recordings are required, please check the comment under region labels SET

        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        valid_label_name = test_data.labels[0].name
        # Reset mock
        mock_print_done.reset_mock()
        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            # Execute command
            command_str = f"label set {notebook.full_path} -n {valid_label_name}"
            cli_executor.exec_command(command_str)
        # Assert
        mock_print_done.assert_called()
        assert mock_print_done.call_args[0][0] == "Label set\n"

    def test_labels_set_invalid_label_name_failure(
        self,
        item_factory,
        mock_fab_ui_print_error,
        cli_executor,
        test_data: StaticTestData,
    ):
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        invalid_label_name = test_data.labels[0].name + "?"
        mock_fab_ui_print_error.reset_mock()

        # Execute command
        command_str = f"label set {lakehouse.full_path} -n {invalid_label_name} -f"
        cli_executor.exec_command(command_str)

        # Assert
        mock_fab_ui_print_error.assert_called()
        error_call = mock_fab_ui_print_error.mock_calls[0]
        assert isinstance(error_call.args[0], FabricCLIError)
        assert (
            error_call.args[0].message
            == f"Id not found for label '{invalid_label_name}'"
        )
        assert error_call.args[0].status_code == constant.ERROR_INVALID_INPUT
        assert error_call.args[1] == "label set"

    # endregion

    # region labels RM
    def test_labels_rm_lakehouse_success(
        self, item_factory, mock_print_done, cli_executor
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        command_str = f"label rm {lakehouse.full_path} -f"
        cli_executor.exec_command(command_str)

        # Assert
        mock_print_done.assert_called_once()

    # endregion

    # region labels LIST-LOCAL
    def test_labels_list_local_success(
        self, mock_questionary_print, cli_executor, test_data: StaticTestData
    ):
        # Execute command
        cli_executor.exec_command("label list-local")

        for label in test_data.labels:
            assert any(
                label.id in call.args[0] for call in mock_questionary_print.mock_calls
            )
            assert any(
                label.name in call.args[0] for call in mock_questionary_print.mock_calls
            )

    def test_labels_list_local_invalid_path_failure(self):
        # Execute command
        with pytest.raises(FabricCLIError) as excinfo:
            exec_labels_list_local(MISSING_LABELS_ABS_PATH)

        # Assert
        assert (
            excinfo.value.message == ErrorMessages.Common.file_or_directory_not_exists()
        )
        assert excinfo.value.status_code == constant.ERROR_INVALID_PATH

    def test_labels_list_local_invalid_entries_failure(self):
        # Execute command
        with pytest.raises(FabricCLIError) as excinfo:
            exec_labels_list_local(INVALID_ENTRIES_LABELS_ABS_PATH)

        # Assert
        assert excinfo.value.message == ErrorMessages.Labels.invalid_entries_format()
        assert excinfo.value.status_code == constant.ERROR_INVALID_ENTRIES_FORMAT

    def test_labels_list_local_invalid_json_failure(self):
        # Execute command
        with pytest.raises(FabricCLIError) as excinfo:
            exec_labels_list_local(INVALID_JSON_LABELS_ABS_PATH)

        # Assert
        assert excinfo.value.message == ErrorMessages.Common.invalid_json_format()
        assert excinfo.value.status_code == constant.ERROR_INVALID_JSON

    # endregion


# region Helper Methods

# running using exec_command and not through parser since it will fail before execution.
# An exaxmple for runing this test - 'label list-local' while the configured yaml was deleted


def exec_labels_list_local(labels_path=LABELS_ABS_PATH):
    args = _build_labels_list_local(labels_path)
    fab_labels_list_local.exec_command(args)


def _build_labels_list_local(labels_path):
    return argparse.Namespace(
        command="labels",
        labels_command="list-local",
        command_path="labels list-local",
        input=labels_path,
    )
