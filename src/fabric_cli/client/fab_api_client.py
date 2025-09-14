# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import platform
import re
import time
from argparse import Namespace
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter, Retry

from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant, fab_logger, fab_state_config
from fabric_cli.core.fab_exceptions import (
    AzureAPIError,
    FabricAPIError,
    FabricCLIError,
    OnelakeAPIError,
)
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_error_parser as utils_errors
from fabric_cli.utils import fab_files as files_utils
from fabric_cli.utils.fab_http_polling_utils import get_polling_interval
from fabric_cli.utils import fab_ui as utils_ui

GUID_PATTERN = r"([a-f0-9\-]{36})"
FABRIC_WORKSPACE_URI_PATTERN = rf"workspaces/{GUID_PATTERN}"




def do_request(
    args,
    json=None,
    data=None,
    files=None,
    timeout_sec=240,
    continuation_token=None,
    hostname=None,
) -> ApiResponse:
    json_file = getattr(args, "json_file", None)
    audience_value = getattr(args, "audience", None)
    headers_value = getattr(args, "headers", None)
    method = getattr(args, "method", "get")
    wait = getattr(args, "wait", True)  # Operations are synchronous by default
    raw_response = getattr(args, "raw_response", False)
    request_params = getattr(args, "request_params", {})
    uri = args.uri.split("?")[0]
    # Get query parameters from URI and add them to request_params extracted from args
    _params_from_uri = args.uri.split("?")[1] if len(args.uri.split("?")) > 1 else None
    if _params_from_uri:
        _params = _params_from_uri.split("&")
        for _param in _params:
            _key, _value = _param.split("=")
            request_params[_key] = _value

    if json_file is not None:
        json = files_utils.load_json_from_path(json_file)

    # Get endpoint and token, and set continuation token if present (pbi and storage audience)
    if audience_value == "storage":
        scope = fab_constant.SCOPE_ONELAKE_DEFAULT
        url = _transform_workspace_url_for_private_link_if_needed(
            fab_constant.API_ENDPOINT_ONELAKE, uri, is_onelake_api=True
        )
    elif audience_value == "azure":
        scope = fab_constant.SCOPE_AZURE_DEFAULT
        url = fab_constant.API_ENDPOINT_AZURE
    elif audience_value == "powerbi":
        scope = fab_constant.SCOPE_FABRIC_DEFAULT
        url = fab_constant.API_ENDPOINT_POWER_BI
    else:
        scope = fab_constant.SCOPE_FABRIC_DEFAULT
        url = _transform_workspace_url_for_private_link_if_needed(
            url=fab_constant.API_ENDPOINT_FABRIC,
            uri=uri,
            hostname=hostname,
        )
        url += f"/{fab_constant.API_VERSION_FABRIC}"

    if continuation_token:
        request_params["continuationToken"] = continuation_token

    # Build url
    url = f"https://{url}/{uri}"
    if request_params:
        url += f"?{requests.compat.urlencode(request_params)}"

    # Get token
    from fabric_cli.core.fab_auth import FabAuth
    token = FabAuth().get_access_token(scope)

    # Build headers
    from fabric_cli.core.fab_context import Context as FabContext
    ctxt_cmd = FabContext().command
    headers = {
        "Authorization": "Bearer " + str(token),
        "User-Agent": f"{fab_constant.API_USER_AGENT}/{fab_constant.FAB_VERSION} ({ctxt_cmd}; {platform.system()}; {platform.machine()}; {platform.release()})",
    }

    if files is None:
        headers["Content-Type"] = "application/json"

    if headers_value is not None:
        if isinstance(args.headers, dict):
            headers.update(args.headers)
        else:
            raise FabricCLIError(
                ErrorMessages.Common.invalid_headers_format(),
                fab_constant.ERROR_INVALID_OPERATION,
            )

    try:
        session = requests.Session()
        retries_count = 3
        retries = Retry(
            total=retries_count, backoff_factor=1, status_forcelist=[502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)

        request_params = {
            "headers": headers,
            "timeout": timeout_sec,
        }

        if files is not None:
            request_params["files"] = files
        elif json is not None:
            request_params["json"] = json
        elif data is not None:
            request_params["data"] = data

        for attempt in range(retries_count + 1):

            fab_logger.log_debug_http_request(
                method, url, headers, timeout_sec, attempt, json, data, files
            )
            start_time = time.time()
            response = session.request(method=method, url=url, **request_params)
            fab_logger.log_debug_http_response(
                response.status_code, response.headers, response.text, start_time
            )

            api_error_code = response.headers.get(
                "x-ms-public-api-error-code", None
            ) or response.headers.get("x-ms-error-code", None)

            if raw_response:
                return ApiResponse(
                    status_code=response.status_code,
                    text=response.text,
                    content=response.content,
                    headers=response.headers,
                )

            match response.status_code:
                case 401:
                    raise FabricCLIError(
                        ErrorMessages.Common.unauthorized(),
                        api_error_code or fab_constant.ERROR_UNAUTHORIZED,
                    )
                case 403:
                    raise FabricCLIError(
                        ErrorMessages.Common.forbidden(),
                        api_error_code or fab_constant.ERROR_FORBIDDEN,
                    )
                case 404:
                    raise FabricCLIError(
                        ErrorMessages.Common.resource_not_found(),
                        fab_constant.ERROR_NOT_FOUND,
                    )
                case 429:
                    retry_after = int(response.headers["Retry-After"])
                    utils_ui.print_info(
                        f"Rate limit exceeded. {attempt}º retrying attemp in {retry_after} seconds"
                    )
                    time.sleep(retry_after)
                    continue
                # We handle 202 status code in a different way for Fabric and Azure APIs
                # if the Location header is present, we ignore it if it is the Get Item Job Instance API url returned by the Run On Demand Item Job API
                case 202 if (
                    wait
                    and scope == fab_constant.SCOPE_FABRIC_DEFAULT
                    and "/jobs/instances/" not in response.headers.get("Location", "")
                ):
                    api_response = ApiResponse(
                        status_code=response.status_code,
                        text=response.text,
                        content=response.content,
                        headers=response.headers,
                    )
                    fab_logger.log_debug(f"Operation started. Polling for result...")
                    return _handle_fab_long_running_op(api_response)
                case 201 | 202 if wait and scope == fab_constant.SCOPE_AZURE_DEFAULT:
                    # Track Azure API asynchronous operations
                    api_response = ApiResponse(
                        status_code=response.status_code,
                        text=response.text,
                        content=response.content,
                        headers=response.headers,
                    )
                    fab_logger.log_debug(f"Operation started. Polling for result...")
                    return _handle_azure_async_op(api_response)
                case c if c in [200, 201, 202, 204]:
                    api_response = ApiResponse(
                        status_code=response.status_code,
                        text=response.text,
                        content=response.content,
                        headers=response.headers,
                    )
                    return _handle_successful_response(args, api_response)
                case _:
                    if fab_constant.API_ENDPOINT_FABRIC in url or (
                        hostname and hostname in url
                    ):
                        raise FabricAPIError(response.text)
                    elif fab_constant.API_ENDPOINT_ONELAKE in url:
                        raise OnelakeAPIError(response.text)
                    elif fab_constant.API_ENDPOINT_AZURE in url:
                        raise AzureAPIError(response.text)
                    raise FabricCLIError(
                        ErrorMessages.Client.unexpected_error_response(
                            response.status_code,
                            response.text,
                        ),
                        utils_errors.map_http_status_code_to_error_code(
                            response.status_code
                        ),
                    )

        raise FabricCLIError(
            ErrorMessages.Common.max_retries_exceeded(retries_count),
            fab_constant.ERROR_MAX_RETRIES_EXCEEDED,
        )

    except requests.RequestException as ex:
        fab_logger.log_debug_http_request_exception(ex)
        raise FabricCLIError(
            ErrorMessages.Common.unexpected_error(str(ex)),
            fab_constant.ERROR_UNEXPECTED_ERROR,
        ) from ex


# Utils


def _handle_successful_response(args: Namespace, response: ApiResponse) -> ApiResponse:
    if fab_constant.DEBUG:
        _print_response_details(response)

    _continuation_token = None

    # In ADLS Gen2 / Onelake, check for x-ms-continuation token in response headers
    if "x-ms-continuation" in response.headers:
        # utils_ui.print_info(
        #     f"Continuation token found for Onelake. Fetching next page of results..."
        # )
        _continuation_token = response.headers["x-ms-continuation"]
    # In Fabric, check for continuation token in response text
    elif response.text != "" and response.text != "null":
        if "continuationToken" in response.text:
            _text = json.loads(response.text)
            if _text and "continuationToken" in _text:
                _continuation_token = _text["continuationToken"]
                # utils_ui.print_info(
                #     f"Continuation token found for Fabric. Fetching next page of results..."
                # )

    if _continuation_token:
        _response = do_request(args, continuation_token=_continuation_token)
    if _continuation_token and _response.status_code == 200:
        response.status_code = 200
        response.append_text(_response.text)

    return response


def _print_response_details(response: ApiResponse) -> None:
    response_details = dict(
        {
            "status_code": response.status_code,
            "response": response.text,
            "headers": dict(response.headers),
        }
    )

    try:
        response_details["response"] = dict(json.loads(response.text))
    except json.JSONDecodeError:
        pass

    fab_logger.log_debug(json.dumps(dict(response_details), indent=4))


def _handle_fab_long_running_op(response: ApiResponse) -> ApiResponse:
    location_header = response.headers.get("Location", "")
    operation_id = response.headers.get("x-ms-operation-id", "")

    if not location_header and not operation_id:
        return response

    operation_uri = f"operations/{operation_id}"
    hostname = urlparse(location_header).hostname or fab_constant.API_ENDPOINT_FABRIC

    return _poll_operation(
        audience="fabric",
        uri=operation_uri,
        original_response=response,
        scope=fab_constant.SCOPE_FABRIC_DEFAULT,
        check_status=True,
        hostname=hostname,
    )


def _handle_azure_async_op(response: ApiResponse) -> ApiResponse:
    uri = response.headers.get("Azure-AsyncOperation")
    if uri is None:
        # Check fot the Location header
        uri = response.headers.get("Location")
        check_status = False
    else:
        check_status = True

    if uri is None or not fab_constant.API_ENDPOINT_AZURE in uri:
        raise AzureAPIError(response.text)

    uri = uri[
        uri.find(fab_constant.API_ENDPOINT_AZURE)
        + len(fab_constant.API_ENDPOINT_AZURE) :
    ]
    return _poll_operation(
        "azure",
        uri,
        response,
        fab_constant.SCOPE_AZURE_DEFAULT,
        check_status,
    )


def _poll_operation(
    audience,
    uri,
    original_response: ApiResponse,
    scope,
    check_status,
    hostname=None,
) -> ApiResponse:
    args = Namespace()
    args.uri = uri
    args.audience = audience
    args.method = "get"
    args.wait = False
    args.params = {}
    
    initial_interval = get_polling_interval(original_response.headers)
    time.sleep(initial_interval)
    
    while True:
        response = do_request(args, hostname=hostname)

        if response.status_code == 200:
            if check_status:
                result_json = response.json()
                status = result_json.get("status")
                #
                if status == "Succeeded" or status == "Completed":
                    fab_logger.log_progress(status)
                    if scope == fab_constant.SCOPE_AZURE_DEFAULT:
                        original_response.status_code = 200
                        return original_response
                    elif scope == fab_constant.SCOPE_FABRIC_DEFAULT:
                        return _fetch_operation_result(
                            args, uri, response, original_response
                        )
                elif status == "Failed":
                    fab_logger.log_progress(status)
                    raise FabricCLIError(
                        ErrorMessages.Common.operation_failed(
                            str(result_json.get("error"))
                        ),
                        fab_constant.ERROR_OPERATION_FAILED,
                    )
                elif status == "Cancelled":
                    fab_logger.log_progress(status)
                    raise FabricCLIError(
                        ErrorMessages.Common.operation_cancelled(
                            str(result_json.get("error"))
                        ),
                        fab_constant.ERROR_OPERATION_CANCELLED,
                    )
                else:
                    # Any other status is considered running
                    _log_operation_progress(result_json)
                    interval = get_polling_interval(response.headers)
                    time.sleep(interval)
            else:
                original_response.status_code = 200
                return original_response
        elif not check_status and response.status_code in [202, 201]:
            interval = get_polling_interval(response.headers)
            time.sleep(interval)
        else:
            raise FabricCLIError(
                ErrorMessages.Client.unexpected_error_response(
                    response.status_code,
                    response.text,
                ),
                utils_errors.map_http_status_code_to_error_code(response.status_code),
            )


def _fetch_operation_result(
    args: Namespace, uri: str, response: ApiResponse, original_response: ApiResponse
) -> ApiResponse:
    # If it is an Operation API, fetch the result
    if "operations/" in uri:
        try:
            location_header = response.headers.get("Location", "")
            hostname = (
                urlparse(location_header).hostname or fab_constant.API_ENDPOINT_FABRIC
            )
            args.uri = f"{uri}/result"
            args.method = "get"
            return do_request(args, hostname=hostname)
        except FabricAPIError as e:
            if e.status_code != "OperationHasNoResult":
                raise e
            original_response.status_code = 200
            return original_response
    else:
        # If it is not an Operation API (e.g. Job Instance), return the response
        return response


def _log_operation_progress(result_json: dict) -> None:
    # Common behaviour for Azure and Fabric REST APIs
    status = result_json.get("status")
    percentage_complete = result_json.get("percentageComplete")
    if percentage_complete is None:
        # But sometimes is missing in the response
        fab_logger.log_progress(status)
    else:
        fab_logger.log_progress(status, percentage_complete)


def _transform_workspace_url_for_private_link_if_needed(
    url: str, uri: str, is_onelake_api: bool = False, hostname: Optional[str] = None
) -> str:
    """
    Transform workspace-level API URLs to use private link format when enabled.
    Applies to both fabric and storage (onelake) audience requests.

    Args:
        url: The full URL to be transformed
        uri: The URI part of the request (used for extracting workspace ID)
        is_onelake_api: Whether this is an OneLake API request (default: False)
        hostname: Optional hostname to use instead of default url

    Returns:
        Transformed URL if conditions are met, otherwise original URL
    """

    if hostname:
        return hostname

    is_private_links_config_enabled = fab_state_config.get_config(
        fab_constant.FAB_WS_PRIVATE_LINKS_ENABLED
    )
    if (
        not is_private_links_config_enabled
        or str(is_private_links_config_enabled).lower() != "true"
    ):
        return url

    # Extract workspace ID by checking API type and URI pattern
    workspace_id = None

    if is_onelake_api:
        # For OneLake APIs, check if first segment is a valid GUID
        uri_segments = uri.strip("/").split("/")
        if uri_segments and re.match(
            rf"^{GUID_PATTERN}$", uri_segments[0], re.IGNORECASE
        ):
            workspace_id = uri_segments[0]
    elif "admin/" in uri.lower():
        return url
    else:
        # For Fabric APIs, extract from workspaces/{workspace-id}/... pattern
        match = re.search(FABRIC_WORKSPACE_URI_PATTERN, uri, re.IGNORECASE)
        if match:
            workspace_id = match.group(1)

    if not workspace_id:
        return url

    return _construct_private_link_url(url, workspace_id, is_onelake_api)


def _construct_private_link_url(
    url: str, workspace_id: str, is_onelake_api: bool = False
) -> str:
    """
    Construct a private link URL for the given workspace ID.
    Applies to both fabric and storage (onelake) audience requests.

    Args:
        url: The original URL to be transformed
        workspace_id: The workspace ID to be included in the URL
        is_onelake_api: Whether this is an OneLake API request (default: False)

    Returns:
        The transformed private link URL
    """
    # Remove dashes from workspace ID and get first 2 characters for region
    workspace_id_clean = workspace_id.replace("-", "")
    region_code = workspace_id[:2]
    ws_private_link_base_url = f"{workspace_id_clean}.z{region_code}"

    # Transform the URL to private link format
    # New url for OneLake DFS APIs: {workspace-id-no-dash}.z{xy}.{original-url}
    # New url for Fabric APIs: {workspace-id-no-dash}.z{xy}.w.{original-url}
    ws_private_link_url = (
        f"{ws_private_link_base_url}.{url}"
        if is_onelake_api
        else f"{ws_private_link_base_url}.w.{url}"
    )

    return ws_private_link_url


def check_token_expired(response: ApiResponse) -> bool:
    if response.status_code == 401:
        try:
            _text = json.loads(response.text)
            if _text.get("errorCode", "") == "TokenExpired":
                return True
        except json.JSONDecodeError:
            pass
    return False
