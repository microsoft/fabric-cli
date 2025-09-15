# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import datetime
import json
import os
import re
import random
import string
from collections import defaultdict
from typing import DefaultDict

from tests.test_commands.api_processors.api_processor_handler import APIProcessorHandler
from tests.test_commands.data.models import User
from tests.test_commands.data.static_test_data import (
    get_static_data,
    get_mock_data,
    StaticTestData,
)
from tests.test_commands.utils import is_record_mode

cassette_resource_counters: DefaultDict[str, int] = defaultdict(int)
generated_name_mapping: dict = {}
api_processor_handler = APIProcessorHandler(generated_name_mapping)
current_request = None

TESTED_XMS_HEADERS = [
    "x-ms-public-api-error-code",
    "x-ms-error-code",
    "x-ms-continuation",
    "x-ms-operation-id",
    "x-ms-rename-source",
    "x-ms-content-type",
    "x-ms-resource-type",
    "x-ms-onelake-shortcut-path",
]


def generate_random_string(
    vcr_instance, cassette_name, prefix="fabcli", length=10, type=None
):
    if not vcr_instance or not cassette_name:
        raise ValueError(
            "VCR instance and cassette name are required to generate random string"
        )

    if length < 5:
        raise ValueError("Minimum length for random string should be 5")

    global cassette_resource_counters

    cassette_path = os.path.join(vcr_instance.cassette_library_dir, cassette_name)
    cassette_resource_counters[cassette_path] += 1

    moniker = "{}{:06}".format(prefix, cassette_resource_counters[cassette_path])

    if vcr_instance.record_mode == "all":
        if type == "workspace":
            # Add creation timestamp for WS - to allow cleanup based on creation time.
            name = prefix + str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
        else:
            name = prefix + "".join(
                random.choices(string.ascii_lowercase + string.digits, k=length)
            )
        generated_name_mapping[name] = moniker
        return name

    return moniker


def update_generated_name_with_special_character(
    vcr_instance,
    generated_name,
    special_character,
):
    if vcr_instance.record_mode == "all":
        moniker = generated_name_mapping[generated_name]
        moniker += special_character
        updated_name = generated_name + special_character
        generated_name_mapping[updated_name] = moniker
        generated_name_mapping.pop(generated_name, None)
        return updated_name

    return generated_name + special_character


def process_request(request):
    global generated_name_mapping
    global current_request

    current_request = request
    if is_record_mode():
        api_processor_handler.handle_request(request)

    if _is_text_payload(request) and request.body:
        body_str = (
            str(request.body, "utf-8")
            if isinstance(request.body, bytes)
            else str(request.body)
        )

        # 1) Normal JSON string replacements in any fields that aren’t base64.
        for old, new in generated_name_mapping.items():
            if old in body_str:
                body_str = body_str.replace(old, new)

        if is_record_mode():
            body_str = _process_string_data(body_str)

        body_str = _process_global_strings(body_str)

        data = json.loads(body_str)

        # Now we have a Python dict for the JSON.
        # 2) Specifically handle base64-encoded payloads in data["definition"]["parts"]
        _replace_inline_base64(data, generated_name_mapping)

        _process_json_data_recursively(data, False)

        # Re-serialize the modified data back to JSON
        new_body_str = json.dumps(data)
        request.body = new_body_str

    # Also do replacements in the URI
    for old, new in generated_name_mapping.items():
        if old in request.uri:
            request.uri = request.uri.replace(old, new)

    if is_record_mode():
        request.uri = _process_string_data(request.uri)

    return request


def process_response(response):
    global generated_name_mapping
    global current_request

    if is_record_mode():
        api_processor_handler.handle_response(current_request, response)

    if _is_text_payload(response) and response["body"]["string"]:
        body = response["body"]["string"]
        body_str = str(body, "utf-8") if isinstance(body, bytes) else str(body)

        if not body_str or body_str == "" or body_str == "null":
            return response

        # 1) Normal JSON string replacements in any fields that aren’t base64.
        for old, new in generated_name_mapping.items():
            if old in body_str:
                body_str = body_str.replace(old, new)

        if is_record_mode():
            body_str = _process_string_data(body_str)

        body_str = _process_global_strings(body_str)

        try:
            data = json.loads(body_str)

            # Now we have a Python dict for the JSON.
            # 2) Specifically handle base64-encoded payloads in data["definition"]["parts"]
            _replace_inline_base64(data, generated_name_mapping)

            _process_json_data_recursively(data, True)

            # Re-serialize the modified data back to JSON
            new_body_str = json.dumps(data)
            response["body"]["string"] = new_body_str.encode("utf-8")
        except json.decoder.JSONDecodeError:
            # If decoding fails, skip
            pass

    if is_record_mode():
        headers = response["headers"]
        response["headers"] = _process_headers(headers)

    return response


def _process_headers(headers):
    updated_headers = {}
    for key, values in headers.items():
        if not key.lower().startswith("x-ms") or key.lower() in TESTED_XMS_HEADERS:
            updated_headers[key] = [_process_string_data(v) for v in values]
    return updated_headers


def _process_string_data(data: str) -> str:
    updated_data = data
    updated_data = _replace_user_details(
        updated_data, get_static_data().user, get_mock_data().user
    )
    updated_data = _replace_user_details(
        updated_data, get_static_data().admin, get_mock_data().admin
    )
    updated_data = _replace_subscription(updated_data)
    updated_data = _replace_sp_id(updated_data)
    updated_data = _replace_capacity_id(updated_data)
    updated_data = _replace_resource_group_name(updated_data)
    updated_data = _replace_sql_server_name(updated_data)
    updated_data = _replace_labels_ids(updated_data)
    return updated_data

def _process_global_strings(data: str) -> str:
    updated_data = data
    updated_data = _replace_email_addresses(updated_data)
    return updated_data


def _replace_capacity_id(data: str) -> str:
    capacity_id = get_static_data().capacity.id
    if capacity_id and capacity_id.lower() in data.lower():
        # Perform case-insensitive replacement
        pattern = re.compile(re.escape(capacity_id), re.IGNORECASE)
        return pattern.sub(get_mock_data().capacity.id, data)
    else:
        return data


def _replace_resource_group_name(data: str) -> str:
    replacements = {
        f"/resourceGroups/{get_static_data().azure_resource_group}/": f"/resourceGroups/{get_mock_data().azure_resource_group}/",
    }
    for old, new in replacements.items():
        if old.lower() in data.lower():
            pattern = re.compile(re.escape(old), re.IGNORECASE)
            data = pattern.sub(new, data)
    return data


def _replace_sql_server_name(data: str) -> str:
    """
    Replace SQL server names in subscription resource paths.
    Matches patterns like: /subscriptions/.../resourceGroups/.../providers/Microsoft.Sql/servers/fabriccli
    Only replaces when the full subscription path context exists.
    """
    static_server = get_static_data().sql_server.server
    mock_server = get_mock_data().sql_server.server

    if static_server and mock_server:
        # Define the pattern once and reuse it for both search and replacement
        pattern = (
            r"(/subscriptions/[^/]+/resourceGroups/[^/]+/providers/Microsoft\.Sql/servers/)"
            + re.escape(static_server)
            + r"(/|\")"
        )

        if re.search(pattern, data, re.IGNORECASE):
            replacement = r"\1" + mock_server + r"\2"
            data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)

    return data


def _replace_user_details(
    data: str, user_details: User, mock_user_details: User
) -> str:
    updated_data = data

    user_id = user_details.id
    if user_id and user_id.lower() in updated_data.lower():
        pattern = re.compile(re.escape(user_id), re.IGNORECASE)
        updated_data = pattern.sub(mock_user_details.id, updated_data)

    user_upn = user_details.upn
    if user_upn and user_upn.lower() in updated_data.lower():
        pattern = re.compile(re.escape(user_upn), re.IGNORECASE)
        updated_data = pattern.sub(mock_user_details.upn, updated_data)

    return updated_data

def _replace_email_addresses(data: str) -> str:
    # Mock UPNs that should be excluded from replacement
    mock_user_upn = get_mock_data().user.upn
    mock_admin_upn = get_mock_data().admin.upn
    excluded_emails = [mock_user_upn, mock_admin_upn, "lisa@fabrikam.com"]

    email_pattern = r"(\"?)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(\"?)"

    def replace_email(match):
        email = match.group(2)
        if email in excluded_emails:
            return match.group(0)
        return f"{match.group(1)}unknown@mocked_user{match.group(3)}"

    return re.sub(email_pattern, replace_email, data)

def _replace_subscription(data: str) -> str:
    subscription_id = get_static_data().azure_subscription_id
    if subscription_id and subscription_id.lower() in data.lower():
        pattern = re.compile(re.escape(subscription_id), re.IGNORECASE)
        return pattern.sub(get_mock_data().azure_subscription_id, data)
    else:
        return data


def _replace_sp_id(data: str) -> str:
    sp_id = get_static_data().service_principal.id
    if sp_id and sp_id.lower() in data.lower():
        pattern = re.compile(re.escape(sp_id), re.IGNORECASE)
        return pattern.sub(get_mock_data().service_principal.id, data)
    else:
        return data


def _replace_inline_base64(data, mapping):
    """
    Finds and processes any part in data["definition"]["parts"]
    where payloadType == "InlineBase64". Decodes the payload,
    does string replacements, and re-encodes it.
    """
    definition = data.get("definition")
    if not isinstance(definition, dict):
        return

    parts = definition.get("parts", [])
    for part in parts:
        if part.get("payloadType") == "InlineBase64":
            original_payload = part.get("payload")
            if not original_payload:
                continue

            try:
                decoded_bytes = base64.b64decode(original_payload)
                decoded_str = decoded_bytes.decode("utf-8")
                for old, new in mapping.items():
                    decoded_str = decoded_str.replace(old, new)

                reencoded = base64.b64encode(decoded_str.encode("utf-8")).decode(
                    "utf-8"
                )
                part["payload"] = reencoded
            except Exception:
                # If decoding fails (not valid base64) or not valid UTF-8, skip
                pass


def _process_json_data_recursively(data, is_response: bool):
    _remove_credentials_details(data)
    if is_response:
        _replace_response_connection_details(data)
        _replace_response_sql_endpoint_properties(data)
        _replace_invitationUrl(data)
    else:
        _replace_request_connection_details(data)

    if isinstance(data, dict):
        for _, value in data.items():
            _process_json_data_recursively(value, is_response)

    if isinstance(data, list):
        for obj in data:
            _process_json_data_recursively(obj, is_response)


def _remove_credentials_details(data: dict):
    if isinstance(data, dict) and "credentialDetails" in data:
        data["credentialDetails"] = "mocked_credential_details"


def _replace_response_connection_details(data: dict):
    if isinstance(data, dict) and "connectionDetails" in data:
        connection_details = data["connectionDetails"]
        if "path" in connection_details and (
            connection_details["path"] == _get_sql_server_path(get_static_data())
            or connection_details["path"] == _get_sql_server_path(get_mock_data())
        ):
            data["connectionDetails"] = {
                "path": _get_sql_server_path(get_mock_data()),
                "type": connection_details["type"],
            }
        else:
            data["connectionDetails"] = {
                "path": "connection_details_mock_path",
                "type": "connection_details_mock_type",
            }


def _replace_request_connection_details(data: dict):
    if isinstance(data, dict) and "connectionDetails" in data:
        data["connectionDetails"] = "mock_request_connection_details"

def _replace_response_sql_endpoint_properties(data: dict):
    if isinstance(data, dict) and "sqlEndpointProperties" in data and data["sqlEndpointProperties"] is not None:
        sql_endpoint_properties = data["sqlEndpointProperties"]
        if "connectionString" in sql_endpoint_properties and sql_endpoint_properties["connectionString"] is not None:
            sql_endpoint_properties["connectionString"] = "mock_connection_string"
        if "id" in sql_endpoint_properties and sql_endpoint_properties["id"] is not None:
            sql_endpoint_properties["id"] = "mock_sql_endpoint_properties_id"

def _replace_invitationUrl(data: dict):
    if isinstance(data, dict) and "invitationUrl" in data:
        data["invitationUrl"] = "mock_invitation_url"


def _replace_labels_ids(data: str) -> str:
    if get_static_data().labels:
        for label in get_static_data().labels:
            if label.id.lower() in data.lower():
                mock_label = list(
                    filter(lambda x: x.name == label.name, get_mock_data().labels)
                )[0]
                pattern = re.compile(re.escape(label.id), re.IGNORECASE)
                data = pattern.sub(mock_label.id, data)
    return data


def _get_sql_server_path(test_data: StaticTestData) -> str:
    return f"{test_data.sql_server.server}.database.windows.net;{test_data.sql_server.database}"


def _is_text_payload(entity):
    # Currently, we only support json payloads
    text_content_list = ["application/json"]

    content_type = _get_content_type(entity)
    if content_type:
        return any(content_type.startswith(x) for x in text_content_list)
    return True


def _get_content_type(entity):
    # 'headers' is a field of 'request', but it is a dict-key in 'response'
    headers = getattr(entity, "headers", None)
    if headers is None:
        headers = entity.get("headers")

    content_type = None
    if headers:
        content_type = headers.get("content-type", headers.get("Content-Type", None))
        if content_type:
            # content-type could an array from response, let us extract it out
            content_type = (
                content_type[0] if isinstance(content_type, list) else content_type
            )
            content_type = content_type.split(";")[0].lower()
    return content_type
