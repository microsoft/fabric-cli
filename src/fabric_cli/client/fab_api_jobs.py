# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Any, Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse


def run_on_demand_item_job(
    args: Namespace, payload: Optional[str] = None
) -> tuple[ApiResponse, Any]:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/run-on-demand-item-job?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/instances?jobType={args.jobType}"
    args.method = "post"

    if payload is not None:
        response = fabric_api.do_request(args, data=payload)
    else:
        response = fabric_api.do_request(args)

    if response.status_code == 202:
        job_instance_url = response.headers.get("Location", "")
        # The location parameter is in the format:
        # https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{itemId}/jobs/instances/{jobInstanceId}
        instance_id = job_instance_url.split("/")[-1]
    else:
        instance_id = None

    return (response, instance_id)


def get_item_job_instance(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/get-item-job-instance?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/instances/{args.instance_id}"
    args.method = "get"

    return fabric_api.do_request(args)


def cancel_item_job_instance(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/cancel-item-job-instance?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/instances/{args.instance_id}/cancel"
    args.method = "post"

    return fabric_api.do_request(args)


def create_item_schedule(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/create-item-schedule?tabs=HTTP"""
    args.uri = (
        f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/{args.jobType}/schedules"
    )
    args.method = "post"

    return fabric_api.do_request(args, data=payload)


def update_item_schedule(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/update-item-schedule?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/{args.jobType}/schedules/{args.schedule_id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)


def get_item_schedule(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/get-item-schedule?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/{args.jobType}/schedules/{args.schedule_id}"
    args.method = "get"

    return fabric_api.do_request(args)


def list_item_schedules(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/list-item-schedules?tabs=HTTP"""
    args.uri = (
        f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/{args.jobType}/schedules"
    )
    args.method = "get"

    return fabric_api.do_request(args)


def list_item_runs(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/list-item-job-instances?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/instances"
    args.method = "get"

    return fabric_api.do_request(args)

def remove_item_schedule(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/delete-item-schedule?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.item_id}/jobs/{args.jobType}/schedules/{args.schedule_id}"
    args.method = "delete"

    return fabric_api.do_request(args)