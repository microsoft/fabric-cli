# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import re
import time
from argparse import Namespace
from typing import Any, Optional

from requests.structures import CaseInsensitiveDict
from fabric_cli.client import fab_api_jobs as jobs_api
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import FabricJobType
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils.fab_http_polling_utils import get_polling_interval
from fabric_cli.utils import fab_ui


def add_item_props_to_args(args: Namespace, context: Item) -> None:
    # Add the item properties to the args
    args.ws_id = context.workspace.id
    args.item_id = context.id
    args.item_type = context.type
    args.item = context.name
    args.jobType = context.job_type.value


def build_config_from_args(
    args: Namespace, item: Item, schedule: Optional[bool] = False
):
    # Input and Params cannot be used at the same time because they affect the same property
    if getattr(args, "input", None) and (
        getattr(args, "params", None) or getattr(args, "config", None)
    ):
        raise FabricCLIError(
            f"Cannot use input in combination with params or config arguments at the same time.",
            fab_constant.ERROR_NOT_RUNNABLE,
        )

    _process_input(args)
    if schedule:
        _process_schedule_args(args)
    else:
        _process_params(args, item)
        _process_config(args, item)


def wait_for_job_completion(
    job_args: Namespace,
    job_ins_id,
    job_response: ApiResponse,
    timeout: Optional[int] = None,
    custom_polling_interval: Optional[int] = None
) -> None:
    args = Namespace(
        ws_id=getattr(job_args, "ws_id", None),
        item_id=getattr(job_args, "item_id", None),
        instance_id=job_ins_id,
        command=(
            getattr(job_args, "command_path", None)
            if hasattr(job_args, "command_path")
            else getattr(job_args, "command", None)
        ),
        output_format=getattr(job_args, "output_format", None),
    )
    attempts = 0
    status = "NotStarted"
    content = None

    initial_interval = get_polling_interval(job_response.headers, custom_polling_interval)
    if (timeout is not None and timeout < initial_interval):
        initial_interval = timeout
    time.sleep(initial_interval)
    total_wait_time = initial_interval

    # Retry until the job is completed or the timeout is reached
    while timeout is None or total_wait_time < timeout:
        _t1 = time.time()
        response = jobs_api.get_item_job_instance(args)
        api_call_time = int(time.time() - _t1)
        
        # Add API call time to total wait time
        total_wait_time += api_call_time

        if response.status_code == 200:
            content = json.loads(response.text)
            status = content["status"]

            # Available statuses are: NotStarted, InProgress, Completed, Deduped, Failed, Cancelled
            if status in ["Completed", "Cancelled", "Deduped"]:
                fab_ui.print_progress(f"Job instance status: {status}")
                if status == "Completed":
                    fab_ui.print_output_format(
                        args, message=f"Job instance '{job_ins_id}' completed"
                    )
                else:
                    fab_logger.log_warning(
                        f"Job instance {job_ins_id} finished with status: {status}"
                    )
                return
            elif status == "Failed":
                fab_ui.print_output_error(
                    FabricCLIError(
                        ErrorMessages.Common.job_instance_failed(job_ins_id),
                        fab_constant.ERROR_JOB_FAILED,
                    ),
                    command=args.command,
                    output_format_type=args.output_format,
                )
                fab_ui.print_entries_unix_style([content], content.keys(), header=True)
                return
            elif status in ["NotStarted", "InProgress"]:
                fab_ui.print_progress(f"Job instance status: {status}")
                
                interval = get_polling_interval(response.headers, custom_polling_interval)
                
                time.sleep(interval)
                total_wait_time += interval

            else:
                fab_logger.log_warning(
                    f"Job instance '{job_ins_id}' unknown status: {status}"
                )
                fab_ui.print_entries_unix_style([content], content.keys(), header=True)
                return
        attempts += 1

    raise TimeoutError(
        f"Job instance '{job_ins_id}' timed out after {total_wait_time} seconds"
    )




def _extract_times(times: str) -> list[str]:
    # Extract the times from the input string
    time_list = times.strip("[]").split(",")
    for time in time_list:
        if not re.match(r"\d{2}:\d{2}", time):
            raise FabricCLIError(
                f"Invalid time format: {time}. Must be in the format HH:mm",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
    return time_list


def _extract_days(days: str) -> list[str]:
    if not days:
        raise FabricCLIError(
            "Days parameter is required for weekly schedule",
            fab_constant.ERROR_NOT_RUNNABLE,
        )
    # Extract the days from the input string
    day_list = days.strip("[]").split(",")
    for day in day_list:
        if day not in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            raise FabricCLIError(
                f"Invalid day: {day}. Must be one of Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
    return day_list


def _process_schedule_args(args: Namespace) -> None:
    if getattr(args, "configuration", None):
        if (
            args.enable
            or (
                not getattr(args, "disable", True)
            )  # Disable only on update, not on create
            or args.type
            or args.start
            or args.end
            or args.interval
            or args.days
        ):
            raise FabricCLIError(
                "Cannot use input in combination with schedule parameters",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
        # Do nothing else, the configuration is already set
    elif args.type or args.start or args.end or args.interval or args.days:
        if not (args.type and args.start and args.end and args.interval):
            raise FabricCLIError(
                "`type`, `interval`, `start`, and `end` are required parameters for schedule creation.",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
        # Build the schedule configuration
        schedule = {}
        args.type = args.type.capitalize()
        schedule["type"] = args.type
        match args.type:
            case "Cron":
                if not re.match(r"^\d+$", args.interval):
                    raise FabricCLIError(
                        f"Invalid format for interval: {args.interval}. Must be an integer.",
                        fab_constant.ERROR_NOT_RUNNABLE,
                    )
                schedule["interval"] = int(args.interval)
            case "Daily":
                times = _extract_times(args.interval)
                schedule["times"] = times
            case "Weekly" if not args.days:
                raise FabricCLIError(
                    "Weekly schedule requires the days parameter.",
                    fab_constant.ERROR_NOT_RUNNABLE,
                )
            case "Weekly":
                times = _extract_times(args.interval)
                days = _extract_days(args.days)
                schedule["times"] = times
                schedule["weekdays"] = days

        # Raise an error if the startDateTime is not in the format YYYY-MM-DDTHH:MM:SS
        datetime_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
        if not re.match(datetime_pattern, args.start):
            raise FabricCLIError(
                f"Invalid timestamp format: {args.start}. Must be in the format yyyy-MM-ddTHH:mm:ss",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
        schedule["startDateTime"] = args.start
        if not re.match(datetime_pattern, args.end):
            raise FabricCLIError(
                f"Invalid timestamp format: {args.end}. Must be in the format yyyy-MM-ddTHH:mm:ss",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
        schedule["endDateTime"] = args.end

        schedule["localTimeZoneId"] = "UTC"

        args.configuration = json.dumps(schedule)
    elif args.enable or (not getattr(args, "disable", True)):
        # Case were enable or disable is the only argument
        args.configuration = None
    else:
        # No schedule configuration provided
        raise FabricCLIError(
            "Schedule configuration is required for schedule creation.",
            fab_constant.ERROR_NOT_RUNNABLE,
        )


def _process_input(args: Namespace) -> None:
    # Normalize the content array to a single string without quotes in case is an list
    if getattr(args, "input", None):
        if isinstance(args.input, list):
            normalized_content = " ".join(args.input).strip("\"'")
        elif isinstance(args.input, str):
            normalized_content = args.input.strip("\"'")
        else:
            raise FabricCLIError(
                f"Invalid JSON content: {args.input}.",
                fab_constant.ERROR_NOT_RUNNABLE,
            )

        if normalized_content.startswith("{") and normalized_content.endswith("}"):
            # Override ' for " to make it a valid JSON
            configuration = json.loads(normalized_content.replace("'", '"'))
        else:
            # Validate that the content is a valid file path
            try:
                with open(normalized_content, "r") as file:
                    configuration = json.load(file)
            except Exception as e:
                raise FabricCLIError(
                    f"Invalid JSON content: {normalized_content}. Error: {str(e)}",
                    fab_constant.ERROR_NOT_RUNNABLE,
                )

        args.configuration = json.dumps(configuration)
        args.input = None


def _process_config(args: Namespace, item: Item) -> None:
    if getattr(args, "config", None):
        if item.job_type != FabricJobType.RUN_NOTEBOOK:
            raise FabricCLIError(
                f"Configuration payload not supported for job type: {item.job_type.value}.",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
        if isinstance(args.config, list):
            normalized_content = " ".join(args.config).strip("\"'")
        elif isinstance(args.config, str):
            normalized_content = args.config.strip("\"'")
        else:
            raise FabricCLIError(
                f"Invalid JSON content: {args.config}.",
                fab_constant.ERROR_NOT_RUNNABLE,
            )

        if normalized_content.startswith("{") and normalized_content.endswith("}"):
            # Override ' for " to make it a valid JSON
            config = json.loads(normalized_content.replace("'", '"'))
        else:
            # Validate that the content is a valid file path
            try:
                with open(normalized_content, "r") as file:
                    config = json.load(file)
            except Exception as e:
                raise FabricCLIError(
                    f"Invalid JSON content: {normalized_content}. Error: {str(e)}",
                    fab_constant.ERROR_NOT_RUNNABLE,
                )

        if getattr(args, "configuration", None):
            _config_str: str = str(args.configuration)
            current_config = json.loads(_config_str)
            current_config["configuration"] = config
            args.configuration = json.dumps(current_config)
        else:
            args.configuration = json.dumps({"configuration": config})

        args.config = None


def _process_notebook_param(type: str, value: str) -> dict:
    # Cast the value to the correct type
    # https://learn.microsoft.com/en-us/fabric/data-engineering/author-execute-notebook#reference-run-a-notebook
    # Supported types: string, int, float, bool
    match type:
        case "string":
            return {"type": type, "value": value.strip("\"'")}
        case "int":
            return {"type": type, "value": int(value)}
        case "float":
            return {"type": type, "value": float(value)}
        case "bool":
            return {"type": type, "value": value.lower() == "true"}
        case _:
            raise FabricCLIError(
                f"Invalid parameter type: {type}. Supported types: string, int, float, bool.",
                fab_constant.ERROR_NOT_RUNNABLE,
            )


def _process_pipeline_param(type: str, value: str) -> Any:
    # Cast the value to the correct type
    # https://learn.microsoft.com/en-us/fabric/data-engineering/author-execute-pipeline#reference-run-a-pipeline
    # Supported types: string, int, float, bool, array, object, secureString
    match type:
        case "string" | "secureString":
            return value.strip("\"'")
        case "int":
            return int(value)
        case "float":
            return float(value)
        case "bool":
            return value.lower() == "true"
        case "array" | "object":
            return json.loads(value)
        case _:
            raise FabricCLIError(
                f"Invalid parameter type: {type}. Supported types: string, secureString, int, float, bool, array, object.",
                fab_constant.ERROR_NOT_RUNNABLE,
            )


def _process_params(args: Namespace, item: Item) -> None:
    if getattr(args, "params", None):
        if isinstance(args.params, list):
            norm_params = " ".join(args.params)
        else:
            norm_params = args.params
        job_type = item.job_type
        # Parameters in name:type=value format, separated by commas
        # Example: -P param1:str=hello,param2:int=123,param3:object={"key":{"key":2},"key":"value"}},param4:int=2
        # Build a regular expression to validate the format and extract the parameters
        pattern = r"((?:\w+:\w+=.+?)(?=(?:,\s*\w+:\w+=)|$))"
        matches = re.findall(pattern, norm_params)
        if not matches:
            raise FabricCLIError(
                f"Invalid parameter format: {norm_params}",
                fab_constant.ERROR_NOT_RUNNABLE,
            )
        params = {}
        for param in matches:
            key, value = param.split("=", 1)
            name, _type = key.split(":", 1)
            try:
                match job_type:
                    case FabricJobType.RUN_NOTEBOOK:
                        params[name] = _process_notebook_param(_type, value)
                    case FabricJobType.PIPELINE:
                        params[name] = _process_pipeline_param(_type, value)
                    case _:
                        raise FabricCLIError(
                            f"Parameters not supported for job type: {job_type.value}. Please use the input argument instead",
                            fab_constant.ERROR_NOT_RUNNABLE,
                        )
            except ValueError as e:
                raise FabricCLIError(
                    f"Invalid value for parameter {name} of type {_type}: {value}. Error: {str(e)}",
                    fab_constant.ERROR_NOT_RUNNABLE,
                )
            except json.JSONDecodeError as e:
                raise FabricCLIError(
                    f"Invalid value for parameter {name} of type {_type}: {value}. Error: {str(e)}",
                    fab_constant.ERROR_NOT_RUNNABLE,
                )

        if getattr(args, "configuration", None):
            # Merge the configuration properties with the existing parameters
            _config_str: str = str(args.configuration)
            current_config = json.loads(_config_str)
            current_config["parameters"] = params
            args.configuration = json.dumps(current_config)
        else:
            args.configuration = json.dumps({"parameters": params})

        args.params = None


def validate_timeout_polling_interval(args: Namespace) -> None:
    """Validate that polling interval is not greater than or equal to timeout."""
    timeout = getattr(args, "timeout", None)
    polling_interval = getattr(args, "polling_interval", None)
    
    if timeout is not None and polling_interval is not None and polling_interval >= timeout:
        raise FabricCLIError(
            f"Custom polling interval ({polling_interval}s) cannot be greater than or equal to timeout ({timeout}s)",
            fab_constant.ERROR_INVALID_INPUT,
        )