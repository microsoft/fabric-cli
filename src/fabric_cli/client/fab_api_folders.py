# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def create_folder(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/create-folder?tabs=HTTP"""

    args.uri = f"workspaces/{args.ws_id}/folders"
    args.method = "post"

    # payload contains the displayName and parentFolderId
    return fabric_api.do_request(args, data=payload)


def delete_folder(args: Namespace, bypass_confirmation: Optional[bool] = False) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/delete-folder?tabs=HTTP"""

    args.uri = f"workspaces/{args.ws_id}/folders/{args.folder_id}"
    args.method = "delete"

    return api_utils.delete_resource(args, bypass_confirmation)


def get_folder(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/get-folder?tabs=HTTP"""

    args.uri = f"workspaces/{args.ws_id}/folders/{args.folder_id}"
    args.method = "get"

    return fabric_api.do_request(args)


def list_folders(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/list-folders?tabs=HTTP"""

    if hasattr(args, "request_params") and "recursive" in args.request_params:
        args.uri = f"workspaces/{args.ws_id}/folders"
    elif hasattr(args, "recursive"):
        args.uri = f"workspaces/{args.ws_id}/folders?recursive={args.recursive}"
    else:
        args.uri = f"workspaces/{args.ws_id}/folders?recursive=True"

    if hasattr(args, "folder_id"):
        args.request_params["rootFolderId"] = args.folder_id

    args.method = "get"

    return fabric_api.do_request(args)


def move_folder(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/move-folder?tabs=HTTP"""

    args.uri = f"workspaces/{args.ws_id}/folders/{args.folder_id}/move"
    args.method = "post"

    # payload contains the folderId and newParentFolderId
    return fabric_api.do_request(args, data=payload)


def update_folder(args: Namespace, payload: str) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/update-folder?tabs=HTTP"""

    args.uri = f"workspaces/{args.ws_id}/folders/{args.folder_id}"
    args.method = "patch"

    return fabric_api.do_request(args, data=payload)
