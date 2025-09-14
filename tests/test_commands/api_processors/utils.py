# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

def load_response_json_body(response):
    """
    Utility to extract and decode a JSON body from a response object.
    Handles both bytes and str, and returns None if body is empty/null.
    """
    if _is_text_payload(response):
        body = response["body"]["string"] if "body" in response and "string" in response["body"] else None
        if not body:
            return None
        body_str = str(body, "utf-8") if isinstance(body, bytes) else str(body)
        if not body_str or body_str == "" or body_str == "null":
            return None

        return json.loads(body_str)
    
    return None


def load_request_json_body(request):
    """
    Utility to extract and decode a JSON body from a request object.
    Handles both bytes and str, and returns None if body is empty/null.
    """
    if _is_text_payload(request) and request.body:
        body_str = (
            str(request.body, "utf-8")
            if isinstance(request.body, bytes)
            else str(request.body)
        )

        return json.loads(body_str)

    return None


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
