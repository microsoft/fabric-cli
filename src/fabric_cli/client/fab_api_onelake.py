# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client import fab_api_utils as api_utils
from fabric_cli.client.fab_api_types import ApiResponse


def delete_dir(
    args: Namespace, bypass_confirmation: bool, verbose: bool = True
) -> bool:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/delete?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.directory}/?recursive=true"
    args.method = "delete"
    args.audience = "storage"

    return api_utils.delete_resource(args, bypass_confirmation, verbose)


def list_tables_files(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/get-properties?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.directory}/?recursive=false&resource=filesystem"
    args.method = "get"
    args.audience = "storage"

    return fabric_api.do_request(args)


def list_tables_files_recursive(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/get-properties?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = args.directory
    args.method = "get"
    args.audience = "storage"

    return fabric_api.do_request(args)


def create_dir(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.directory}/?resource=directory"
    args.method = "put"
    args.audience = "storage"
    headers = {"If-None-Match": "*"}
    args.headers = headers

    return fabric_api.do_request(args)


def move_rename(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.headers = {"x-ms-rename-source": args.from_path}
    args.uri = f"{args.to_path}"
    args.method = "put"
    args.audience = "storage"

    return fabric_api.do_request(args)


def get(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.from_path}"
    args.method = "get"
    args.audience = "storage"

    return fabric_api.do_request(args)


def get_properties(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.from_path}"
    args.method = "head"
    args.audience = "storage"

    return fabric_api.do_request(args)


def read(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.from_path}"
    args.method = "get"
    args.audience = "storage"

    return fabric_api.do_request(args)


def touch_file(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.to_path}/?resource=file"
    args.method = "put"
    args.audience = "storage"

    return fabric_api.do_request(args)


def append_file(
    args: Namespace,
    content: str | bytes,
    position: int,
    content_type: Optional[str] = "application/json",
    content_length: Optional[int] = None,
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/update?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.to_path}?action=append&position={position}"
    args.method = "patch"
    args.audience = "storage"
    content_length = content_length if content_length else len(content)
    args.headers = {
        "Content-Length": str(content_length),
        "Content-Type": content_type,  # This is included to avoid the requests library to decode the content as json
        "x-ms-content-type": content_type,
    }

    return fabric_api.do_request(args, data=content)


def flush_file(
    args: Namespace, position: int, content_type: Optional[str] = "application/json"
) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/update?view=rest-storageservices-datalakestoragegen2-2019-12-12"""
    args.uri = f"{args.to_path}?action=flush&position={position}"
    args.method = "patch"
    args.audience = "storage"
    args.headers = {
        "Content-Length": "0",
        "x-ms-content-type": content_type,
    }

    return fabric_api.do_request(args)


# ACLs
def acl_list_data_access_roles(args: Namespace) -> ApiResponse:
    """https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-data-access-security/list-data-access-roles?tabs=HTTP"""
    args.uri = f"workspaces/{args.ws_id}/items/{args.id}/dataAccessRoles"
    args.method = "get"

    return fabric_api.do_request(args)
