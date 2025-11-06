# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import os
import re
import time

import fabric_cli.commands.fs.fab_fs_set as fab_fs_set
import fabric_cli.commands.jobs.fab_jobs_run as fab_jobs_run
import fabric_cli.commands.jobs.fab_jobs_run_cancel as fab_jobs_run_cancel
import fabric_cli.commands.jobs.fab_jobs_run_list as fab_jobs_run_list
import fabric_cli.commands.jobs.fab_jobs_run_sch as fab_jobs_run_sch
import fabric_cli.commands.jobs.fab_jobs_run_status as fab_jobs_run_status
import fabric_cli.commands.jobs.fab_jobs_run_update as fab_jobs_run_update
import fabric_cli.commands.jobs.fab_jobs_run_rm as fab_jobs_run_rm
import fabric_cli.core.fab_state_config as state_config
import fabric_cli.utils.fab_cmd_job_utils as utils_job
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, VirtualItemContainerType
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.utils import fab_storage as utils_storage


class TestJobs:
    # region JOB RUN
    def test_run_job_notebook(self, item_factory, cli_executor, mock_questionary_print):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Execute command
        cli_executor.exec_command(f"job run {notebook.full_path}")

        # Extract the arguments passed to the mock
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()

        # Assert that the first call to the mock was to create the Notebook
        assert calls[0].args[0] == f"Importing '{nb_path}' → '{notebook.full_path}'..."

        # Assert that the second call to the mock was to run the Notebook
        regex = r"∟ Job instance '(.*)' created"
        matches = re.match(regex, calls[2].args[0])
        assert matches
        job_instance_id = matches.group(1)

        assert calls[3].args[0] == "∟ Timeout: no timeout specified"

        # All the calls in between are NotStarted or InProgress status

        # Assert that the last call to the mock was the completition message
        assert calls[-1].args[0].split()[4] == "Completed"

        job_run_status(notebook.full_path, job_instance_id)

        calls = mock_questionary_print.call_args_list

        # Assert that the last call to the mock was the completition message
        assert calls[-1].args[0].split()[2] == "RunNotebook"
        assert calls[-1].args[0].split()[3] == "Manual"
        assert calls[-1].args[0].split()[4] == "Completed"

    def test_run_job_notebook_timeout(
        self, item_factory, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example_wait.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Execute command
        cli_executor.exec_command(f"job run {notebook.full_path} --timeout 10")

        # Extract the arguments passed to the mock
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()

        # Assert that the first call to the mock was to create the Notebook
        assert calls[0].args[0] == f"Importing '{nb_path}' → '{notebook.full_path}'..."

        # Assert that the second call to the mock was to run the Notebook
        regex = r"∟ Job instance '(.*)' created"
        matches = re.match(regex, calls[2].args[0])
        assert matches
        job_instance_id = matches.group(1)

        assert calls[3].args[0] == "∟ Timeout: 10 seconds"

        # All the calls in between are NotStarted or Running status

        # Assert that the a single call to the warning mock was the timeout message
        mock_print_warning.assert_called_once()
        w_calls = mock_print_warning.call_args_list
        regex = r"Job instance '(.*)' timed out after (.*) seconds"
        match = re.match(regex, w_calls[-1].args[0])
        assert match
        instance_id = match.group(1)
        assert job_instance_id == instance_id
        timeout_sec = int(match.group(2))
        assert timeout_sec >= 1

        job_run_status(notebook.full_path, job_instance_id)

        calls = mock_questionary_print.call_args_list

        # Assert that the last call to the mock was the completition message
        assert calls[-1].args[0].split()[2] == "RunNotebook"
        assert calls[-1].args[0].split()[3] == "Manual"
        assert calls[-1].args[0].split()[4] == "Cancelled"

    def test_run_job_notebook_timeout_zero_sec(
        self, item_factory, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Execute command
        cli_executor.exec_command(f"job run {notebook.full_path} --timeout 0")

        # Extract the arguments passed to the mock
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()

        # Assert that the first call to the mock was to create the Notebook
        assert calls[0].args[0] == f"Importing '{nb_path}' → '{notebook.full_path}'..."

        # Assert that the second call to the mock was to run the Notebook
        regex = r"∟ Job instance '(.*)' created"
        matches = re.match(regex, calls[2].args[0])
        assert matches
        job_instance_id = matches.group(1)

        assert calls[3].args[0] == "∟ Timeout: 0 seconds"

        # All the calls in between are NotStarted or InProgress status

        # Assert that the a single call to the warning mock was the timeout message
        mock_print_warning.assert_called_once()
        w_calls = mock_print_warning.call_args_list
        regex = r"Job instance '(.*)' timed out after (.*) seconds"
        match = re.match(regex, w_calls[-1].args[0])
        assert match
        instance_id = match.group(1)
        assert job_instance_id == instance_id
        timeout_sec = int(match.group(2))
        assert timeout_sec == 0

        time.sleep(1)
        job_run_status(notebook.full_path, job_instance_id)

        calls = mock_questionary_print.call_args_list

        # Assert that the last call to the mock was the completition message
        assert calls[-1].args[0].split()[2] == "RunNotebook"
        assert calls[-1].args[0].split()[3] == "Manual"
        assert calls[-1].args[0].split()[4] in ["Cancelled", "NotStarted"]

    def test_start_job_notebook_and_cancel(
        self, item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example_wait.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Execute command
        job_start(notebook.full_path)

        # Extract the arguments passed to the mock
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        # Assert that the first call to the mock was to create the Notebook
        assert calls[0].args[0] == f"Importing '{nb_path}' → '{notebook.full_path}'..."

        # Assert that the second call to the mock was to run the Notebook
        regex = r"→ To see status run 'job run-status (.+) --id (.+)'"
        matches = re.match(regex, calls[1].args[0])
        assert matches
        job_instance_id = matches.group(2)

        # Sleep to avoid rely => No notebook execution state found in database for the runId ...
        time.sleep(1)
        job_run_status(notebook.full_path, job_instance_id)
        # Assert that the last call to the mock was the completition message
        calls = mock_questionary_print.call_args_list
        assert calls[-1].args[0].split()[2] == "RunNotebook"
        assert calls[-1].args[0].split()[3] == "Manual"
        assert (
            calls[-1].args[0].split()[4] == "NotStarted"
            or calls[-1].args[0].split()[4] == "InProgress"
        )

        mock_questionary_print.reset_mock()
        cli_executor.exec_command(
            f"job run-cancel {notebook.full_path} --id {job_instance_id} --wait"
        )

        # Assert that the last call to the mock was the completition message
        calls = mock_questionary_print.call_args_list
        assert calls[-1].args[0].split()[4] == "Cancelled"

        # Sleep to avoid rely => No notebook execution state found in database for the runId ...
        time.sleep(2)
        job_run_status(notebook.full_path, job_instance_id)
        # Assert that the last call to the mock was the completition message
        calls = mock_questionary_print.call_args_list
        assert calls[-1].args[0].split()[2] == "RunNotebook"
        assert calls[-1].args[0].split()[3] == "Manual"
        assert calls[-1].args[0].split()[4] == "Cancelled"

    def test_run_sch_notebook_no_params_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
    ):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Execute command
        cli_executor.exec_command(f"job run-sch {notebook.full_path}")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Schedule configuration is required for schedule creation",
        )

    def test_run_sch_notebook(self, item_factory, cli_executor, mock_questionary_print):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)
        config = "{'type': 'Cron', 'startDateTime': '2024-04-28T00:00:00', 'endDateTime': '2024-04-30T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'interval': 10}"
        input_config = "{'enabled': true, 'configuration': " + config + "}"

        # Execute command
        cli_executor.exec_command(f"job run-sch {notebook.full_path} -i {input_config}")

        time.sleep(2)
        job_run_list(notebook.full_path, schedule=True)

        # Assert
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        assert config in calls[-1].args[0]
        assert calls[-1].args[0].split()[1] == "True"

        schedule_id = calls[-1].args[0].split()[0]
        job_update(notebook.full_path, schedule_id, disable=False)
        time.sleep(2)
        job_run_list(notebook.full_path, schedule=True)

        calls = mock_questionary_print.call_args_list
        assert calls[-1].args[0].split()[1] == "False"

        # Change the schedule
        new_config = "{'type': 'Weekly', 'startDateTime': '2024-12-15T09:00:00', 'endDateTime': '2024-12-16T09:00:00', 'localTimeZoneId': 'UTC', 'times': ['19:43', '22:00'], 'weekdays': ['Monday', 'Tuesday']}"
        job_update(
            notebook.full_path,
            schedule_id,
            type="Weekly",
            interval="19:43,22:00",
            days="Monday,Tuesday",
            start="2024-12-15T09:00:00",
            end="2024-12-16T09:00:00",
            enable=True,
        )
        time.sleep(2)
        job_run_list(notebook.full_path, schedule=True)

        calls = mock_questionary_print.call_args_list
        assert calls[-1].args[0].split()[1] == "True"
        assert new_config in calls[-1].args[0]

    def test_run_schedule_notebook_wrong_params_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_fab_ui_print_error,
    ):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)
        config = "{'type': 'Cron', 'startDateTime': '2024-04-28T00:00:00', 'endDateTime': '2024-04-30T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'interval': 10}"
        input_config = "{'enabled': true, 'configuration': " + config + "}"

        # Execute command
        cli_executor.exec_command(
            f"job run-sch {notebook.full_path} --type weekly -i {input_config}"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Cannot use input in combination with schedule parameters",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-sch {notebook.full_path} --type weekly --interval 19:43,22:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "`type`, `interval`, `start`, and `end` are required parameters for schedule creation",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-sch {notebook.full_path} --type cron --interval 19:43,22:00 --start 2024-12-15T09:00:00 --end 2024-12-16T09:00:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid format for interval: 19:43,22:00. Must be an integer",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-sch {notebook.full_path} --type cron --interval 10 --start 2024-12-1509:00 --end 2024-12-16T09:00:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid timestamp format: 2024-12-1509:00. Must be in the format yyyy-MM-ddTHH:mm:ss",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-sch {notebook.full_path} --type cron --interval 10 --start 15/12/2024T09:00:00 --end 2024-12-16T09:00:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid timestamp format: 15/12/2024T09:00:00. Must be in the format yyyy-MM-ddTHH:mm:ss",
        )

    def test_run_schedule_update_notebook_wrong_params_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        # Setup
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)
        config = "{'type': 'Cron', 'startDateTime': '2024-04-28T00:00:00', 'endDateTime': '2024-04-30T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'interval': 10}"
        job_sch(
            notebook.full_path,
            input="{'enabled': true, 'configuration': " + config + "}",
        )

        job_run_list(notebook.full_path, schedule=True)

        # Assert
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        assert config in calls[-1].args[0]
        assert calls[-1].args[0].split()[1] == "True"

        schedule_id = calls[-1].args[0].split()[0]

        # Execute command
        config = "{'type': 'Cron', 'startDateTime': '2024-04-28T00:00:00', 'endDateTime': '2024-04-30T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'interval': 10}"
        input_config = "{'enabled': true, 'configuration': " + config + "}"
        cli_executor.exec_command(
            f"job run-update {notebook.full_path} --id {schedule_id} --type weekly -i {input_config}"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Cannot use input in combination with schedule parameters",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-update {notebook.full_path} --id {schedule_id} --type weekly --interval 19:43,22:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "`type`, `interval`, `start`, and `end` are required parameters for schedule creation",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-update {notebook.full_path} --id {schedule_id} --type cron --interval 19:43,22:00 --start 2024-12-15T09:00:00 --end 2024-12-16T09:00:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid format for interval: 19:43,22:00. Must be an integer",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-update {notebook.full_path} --id {schedule_id} --type cron --interval 10 --start 2024-12-1509:00 --end 2024-12-16T09:00:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid timestamp format: 2024-12-1509:00. Must be in the format yyyy-MM-ddTHH:mm:ss",
        )

        # Execute command
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run-update {notebook.full_path} --id {schedule_id} --type cron --interval 10 --start 15/12/2024T09:00:00 --end 2024-12-16T09:00:00"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid timestamp format: 15/12/2024T09:00:00. Must be in the format yyyy-MM-ddTHH:mm:ss",
        )

    def test_run_spark_job(self, item_factory, cli_executor, mock_questionary_print):
        # Setup
        data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        sj_path = os.path.join(data_path, "sample_items", "example.SparkJobDefinition")
        spark_jd = item_factory(ItemType.SPARK_JOB_DEFINITION, content_path=sj_path)
        fb_sjd = handle_context.get_command_context(spark_jd.full_path)
        fb_workspace = fb_sjd.parent

        lakehouse = item_factory(ItemType.LAKEHOUSE)
        lakehouse_id = handle_context.get_command_context(lakehouse.full_path).id
        set_cmd(
            spark_jd.full_path,
            "definition.parts[0].payload.defaultLakehouseArtifactId",
            lakehouse_id,
        )

        exec_file_path = os.path.join(data_path, "sample_code", "spark_job_simple.py")
        # Ref: https://learn.microsoft.com/en-us/fabric/data-engineering/spark-job-definition-api#upload-the-main-definition-file-and-other-lib-files
        with open(exec_file_path, "r") as file:
            payload = file.read()
            export_path = {
                "type": "sparkJobDefinition",
                "path": f"{fb_sjd.path_id}/Main/{os.path.basename(exec_file_path)}",
            }
            args = argparse.Namespace(command="test-job")
            utils_storage.write_to_storage(
                args, export_path, payload, export=False, content_type="text/plain"
            )
        # Ref: https://learn.microsoft.com/en-us/fabric/data-engineering/spark-job-definition-api#update-the-spark-job-definition-item-with-the-onelake-url-of-the-main-definition-file-and-other-lib-files
        abfss_path = f"abfss://{fb_workspace.id}@onelake.dfs.fabric.microsoft.com/{fb_sjd.id}/Main/{os.path.basename(exec_file_path)}"
        set_cmd(
            spark_jd.full_path, "definition.parts[0].payload.executableFile", abfss_path
        )

        # Execute command
        cli_executor.exec_command(f"job run {spark_jd.full_path}")

        # Assert
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        assert calls[-1].args[0] == "∟ Job instance status: Completed"

    def test_run_pipeline(self, item_factory, cli_executor, mock_questionary_print):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        fb_lakehouse = handle_context.get_command_context(lakehouse.full_path)
        lakehouse_id = fb_lakehouse.id
        workspace_id = fb_lakehouse.parent.id

        items_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items",
        )

        lakehouse_dependency = {
            "default_lakehouse": lakehouse_id,
            "default_lakehouse_name": lakehouse.display_name,
            "default_lakehouse_workspace_id": workspace_id,
        }
        nb_path = os.path.join(items_path, "example.Notebook")
        nb_content_path = os.path.join(nb_path, "notebook-content.ipynb")
        nb_json = json.loads(open(nb_content_path).read())
        nb_json["metadata"]["dependencies"]["lakehouse"] = lakehouse_dependency
        json.dump(nb_json, open(nb_content_path, "w"))

        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        fb_notebook = handle_context.get_command_context(notebook.full_path)
        notebook_id = fb_notebook.id
        ws_id = fb_notebook.parent.id

        pipeline_path = os.path.join(items_path, "example.DataPipeline")
        pipeline_content_path = os.path.join(pipeline_path, "pipeline-content.json")

        pipeline_json = json.loads(open(pipeline_content_path).read())
        pipeline_json["properties"]["activities"][0]["typeProperties"][
            "notebookId"
        ] = notebook_id
        pipeline_json["properties"]["activities"][0]["typeProperties"][
            "workspaceId"
        ] = ws_id
        json.dump(pipeline_json, open(pipeline_content_path, "w"))

        pipeline = item_factory(ItemType.DATA_PIPELINE, content_path=pipeline_path)

        # Execute command
        cli_executor.exec_command(f"job run {pipeline.full_path}")

        # Assert
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        assert calls[-1].args[0] == "∟ Job instance status: Completed"

    def test_run_param_job(self, item_factory, cli_executor, mock_questionary_print):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        fb_lakehouse = handle_context.get_command_context(lakehouse.full_path)
        lakehouse_id = fb_lakehouse.id
        workspace_id = fb_lakehouse.parent.id

        lakehouse_dependency = {
            "default_lakehouse": lakehouse_id,
            "default_lakehouse_name": lakehouse.display_name,
            "default_lakehouse_workspace_id": workspace_id,
        }
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        nb_content_path = os.path.join(nb_path, "notebook-content.ipynb")
        nb_json = json.loads(open(nb_content_path).read())
        nb_json["metadata"]["dependencies"]["lakehouse"] = lakehouse_dependency
        json.dump(nb_json, open(nb_content_path, "w"))

        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        _params = [
            "string_param:string=new_value",
            "int_param:int=10",
            "float_param:float=0.1234",
            "bool_param:bool=true",
        ]

        # Execute command
        cli_executor.exec_command(
            f"job run {notebook.full_path} --params {','.join(_params)}"
        )

        # Assert
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        assert calls[-1].args[0] == "∟ Job instance status: Completed"

        # Configure and run the pipeline

        fb_notebook = handle_context.get_command_context(notebook.full_path)
        notebook_id = fb_notebook.id
        ws_id = fb_notebook.parent.id

        pipeline_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.DataPipeline",
        )
        pipeline_content_path = os.path.join(pipeline_path, "pipeline-content.json")

        pipeline_json = json.loads(open(pipeline_content_path).read())
        pipeline_json["properties"]["activities"][0]["typeProperties"][
            "notebookId"
        ] = notebook_id
        pipeline_json["properties"]["activities"][0]["typeProperties"][
            "workspaceId"
        ] = ws_id
        json.dump(pipeline_json, open(pipeline_content_path, "w"))

        pipeline = item_factory(ItemType.DATA_PIPELINE, content_path=pipeline_path)

        _params = [
            "string_param:string=new_value",
            "int_param:int=10",
            "float_param:float=0.1234",
            "bool_param:bool=true",
            'obj_param:object={"key":{"key":2},"key":"value"}',
            "array_param:array=[1,2,3]",
            "secstr_param:secureString=secret",
        ]

        # Execute command
        cli_executor.exec_command(
            f"job run {pipeline.full_path} --params {','.join(_params)}"
        )

        # Assert
        calls = mock_questionary_print.call_args_list
        mock_questionary_print.assert_called()
        assert calls[-1].args[0] == "∟ Job instance status: Completed"

    def test_run_invalid_param_types_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_fab_ui_print_error,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        fb_lakehouse = handle_context.get_command_context(lakehouse.full_path)
        lakehouse_id = fb_lakehouse.id
        workspace_id = fb_lakehouse.parent.id

        lakehouse_dependency = {
            "default_lakehouse": lakehouse_id,
            "default_lakehouse_name": lakehouse.display_name,
            "default_lakehouse_workspace_id": workspace_id,
        }
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        nb_content_path = os.path.join(nb_path, "notebook-content.ipynb")
        nb_json = json.loads(open(nb_content_path).read())
        nb_json["metadata"]["dependencies"]["lakehouse"] = lakehouse_dependency
        json.dump(nb_json, open(nb_content_path, "w"))

        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)
        _params = ["string_param:string=new_value", "wrong_param:nonvalid=10"]

        # Execute command
        cli_executor.exec_command(
            f"job run {notebook.full_path} --params {','.join(_params)}"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid parameter type: nonvalid",
        )

        # Execute command
        _params = ["int_param:int=string_value"]
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run {notebook.full_path} --params {','.join(_params)}"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid value for parameter int_param of type int: string_value",
        )

        # Configure and run the pipeline

        fb_notebook = handle_context.get_command_context(notebook.full_path)
        notebook_id = fb_notebook.id
        ws_id = fb_notebook.parent.id

        pipeline_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.DataPipeline",
        )
        pipeline_content_path = os.path.join(pipeline_path, "pipeline-content.json")

        pipeline_json = json.loads(open(pipeline_content_path).read())
        pipeline_json["properties"]["activities"][0]["typeProperties"][
            "notebookId"
        ] = notebook_id
        pipeline_json["properties"]["activities"][0]["typeProperties"][
            "workspaceId"
        ] = ws_id
        json.dump(pipeline_json, open(pipeline_content_path, "w"))

        pipeline = item_factory(ItemType.DATA_PIPELINE, content_path=pipeline_path)

        # Execute command
        _params = ["string_param:string=new_value", "wrong_param:nonvalid=10"]
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run {pipeline.full_path} --params {','.join(_params)}"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            "Invalid parameter type: nonvalid",
        )

        # Unformatted json object
        # Execute command
        _params = ['obj_param:object={"key":{"key":2},"key":"value"']
        mock_fab_ui_print_error.reset_mock()
        cli_executor.exec_command(
            f"job run {pipeline.full_path} --params {','.join(_params)}"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_RUNNABLE,
            'Invalid value for parameter obj_param of type object: {"key":{"key":2},"key":"value"',
        )

    def test_run_table_maintenance(
        self, item_factory, virtual_item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        fb_lakehouse = handle_context.get_command_context(lakehouse.full_path)
        lakehouse_id = fb_lakehouse.id
        workspace_id = fb_lakehouse.parent.id
        environment = item_factory(ItemType.ENVIRONMENT)
        fb_environment = handle_context.get_command_context(environment.full_path)
        environment_id = fb_environment.id
        spark_pool = virtual_item_factory(VirtualItemContainerType.SPARK_POOL)
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example_create_tables.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)
        # Reset the mock to avoid the previous calls
        mock_questionary_print.reset_mock()
        conf = {
            "conf": {
                "spark.conf1": "value",
            },
            "defaultLakehouse": {
                "name": lakehouse.display_name,
                "id": lakehouse_id,
                "workspaceId": workspace_id,
            },
            "useStarterPool": False,
            "useWorkspacePool": spark_pool.display_name,
            "environment": {
                "name": environment.display_name,
                "id": environment_id,
            },
        }

        # Execute command
        cli_executor.exec_command(
            f"job run {notebook.full_path} --config {json.dumps(conf)} --params string_param:string=new_value"
        )

        # Extract the arguments passed to the mock
        calls = mock_questionary_print.call_args_list

        # Assert that the last call to the mock was the completition message
        assert calls[-1].args[0].split()[4] == "Completed"
        # Reset the mock to avoid the previous calls
        mock_questionary_print.reset_mock()
        maintenance_job_input = {
            "tableName": "customers",
            "optimizeSettings": {"vOrder": True, "zOrderBy": ["account_id"]},
            "vacuumSettings": {"retentionPeriod": "7.01:00:00"},
        }

        # Execute command
        job_run(
            lakehouse.full_path,
            input=json.dumps(maintenance_job_input),
        )

        calls = mock_questionary_print.call_args_list
        assert calls[-1].args[0] == "∟ Job instance status: Completed"

    def test_run_schedule_rm_invalid_param_types_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
    ):
        # Setup notebook and without schedule
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Test unexisting schedule removal
        cli_executor.exec_command(f"job run-rm {notebook.full_path} --id 00000000-0000-0000-0000-000000000000 --force")

        assert_fabric_cli_error(
            constant.ERROR_NOT_FOUND,
            "The requested resource could not be found",
        )
        
        # Test bad item path
        cli_executor.exec_command(f"job run-rm /bad_path/ --id 00000000-0000-0000-0000-000000000000 --force")

        assert_fabric_cli_error(
            constant.ERROR_NOT_FOUND,
            "The requested resource could not be found",
        )


    def test_run_schedule_rm(self, cli_executor, item_factory, mock_questionary_print):
        # Create notebook
        nb_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.Notebook",
        )
        notebook = item_factory(ItemType.NOTEBOOK, content_path=nb_path)

        # Create data pipeline
        dp_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.DataPipeline",
        )
        pipeline = item_factory(ItemType.DATA_PIPELINE, content_path=dp_path)

        # Create a spark job definition
        sjd_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data/sample_items/example.SparkJobDefinition",
        )
        spark_jd = item_factory(ItemType.SPARK_JOB_DEFINITION, content_path=sjd_path)


        # Init schedules for all items
        config = "{'type': 'Cron', 'startDateTime': '2024-01-23T00:00:00', 'endDateTime': '2024-10-07T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'interval': 10}"
        input_config = "{'enabled': true, 'configuration': " + config + "}"

        cli_executor.exec_command(f"job run-sch {notebook.full_path} -i {input_config}")
        cli_executor.exec_command(f"job run-sch {pipeline.full_path} -i {input_config}")
        cli_executor.exec_command(f"job run-sch {spark_jd.full_path} -i {input_config}")


        time.sleep(2)
        job_run_list(notebook.full_path, schedule=True)
        notebook_scheduled_id = mock_questionary_print.call_args_list[-1].args[0].split()[0]

        job_run_list(pipeline.full_path, schedule=True)
        pipeline_scheduled_id = mock_questionary_print.call_args_list[-1].args[0].split()[0]

        job_run_list(spark_jd.full_path, schedule=True)
        sparkjd_scheduled_id = mock_questionary_print.call_args_list[-1].args[0].split()[0]

        # Remove schedules with rm command
        cli_executor.exec_command(f"job run-rm {notebook.full_path} --id {notebook_scheduled_id} --force")
        cli_executor.exec_command(f"job run-rm {pipeline.full_path} --id {pipeline_scheduled_id} --force")
        cli_executor.exec_command(f"job run-rm {spark_jd.full_path} --id {sparkjd_scheduled_id} --force")

        # Check notebook schedule removal
        mock_questionary_print.reset_mock()
        job_run_list(notebook.full_path, schedule=True)
        assert len(mock_questionary_print.call_args_list) == 0

        mock_questionary_print.reset_mock()
        # Check data pipeline schedule removal
        job_run_list(pipeline.full_path, schedule=True)
        assert len(mock_questionary_print.call_args_list) == 0

        mock_questionary_print.reset_mock()
        # Check spark job definition schedule removal
        job_run_list(spark_jd.full_path, schedule=True)
        assert len(mock_questionary_print.call_args_list) == 0



# region Helper Methods
def job_run(path, params=None, config=None, input=None, timeout=None):
    job_exec(path, params, config, input, wait=True, timeout=timeout)


def job_start(path, params=None, config=None, input=None):
    job_exec(path, params, config, input, wait=False)


def job_exec(path, params=None, config=None, input=None, wait=False, timeout=None):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = _build_job_run_args(path, params, config, input, wait, timeout)
    context = handle_context.get_command_context(args.path)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    utils_job.build_config_from_args(args, context)
    fab_jobs_run.exec_command(args, context)


def _build_job_run_args(path, params, config, input, wait=False, timeout=None):
    command = "run" if wait else "start"
    return argparse.Namespace(
        command="job",
        jobs_command=command,
        command_path=f"job {command}",
        path=path,
        params=params,
        config=config,
        input=input,
        wait=wait,
        timeout=timeout,
    )


def job_run_list(path, schedule=False):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="job",
        jobs_command="list",
        command_path=f"job list",
        path=path,
        schedule=schedule,
    )
    context = handle_context.get_command_context(args.path)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    fab_jobs_run_list.exec_command(args, context)


def job_run_status(path, job_instance_id, schedule=False):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="job",
        jobs_command="status",
        command_path=f"job status",
        path=path,
        id=job_instance_id,
        schedule=schedule,
    )
    context = handle_context.get_command_context(args.path)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    fab_jobs_run_status.exec_command(args, context)


def job_run_cancel(path, job_instance_id, schedule=False, wait=True):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="job",
        jobs_command="cancel",
        command_path=f"job cancel",
        path=path,
        id=job_instance_id,
        wait=wait,
        schedule=schedule,
    )
    context = handle_context.get_command_context(args.path)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    fab_jobs_run_cancel.exec_command(args, context)


def job_sch(
    path,
    input=None,
    enable=False,
    type=None,
    interval=None,
    start=None,
    end=None,
    days=None,
):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="job",
        jobs_command="sch",
        command_path="job sch",
        path=path,
        input=input,
        enable=enable,
        type=type,
        interval=interval,
        start=start,
        end=end,
        days=days,
    )
    context = handle_context.get_command_context(args.path)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    utils_job.build_config_from_args(args, context, schedule=True)
    fab_jobs_run_sch.exec_command(args, context)


def job_update(
    path,
    id,
    input=None,
    enable=False,
    disable=True,
    type=None,
    interval=None,
    start=None,
    end=None,
    days=None,
):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="job",
        jobs_command="update",
        command_path="job update",
        path=path,
        schedule_id=id,
        input=input,
        enable=enable,
        disable=disable,
        type=type,
        interval=interval,
        start=start,
        end=end,
        days=days,
    )
    context = handle_context.get_command_context(args.path)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    utils_job.build_config_from_args(args, context, schedule=True)
    fab_jobs_run_update.exec_command(args, context)


def set_cmd(path, query, input, force=True):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="set",
        command_path="set",
        path=path,
        query=query,
        input=input,
        force=force,
    )
    context = handle_context.get_command_context(args.path)
    fab_fs_set.exec_command(args, context)


# endregion Helper Methods
