# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.utils import fab_jmespath as utils_jmespath
from fabric_cli.utils import fab_ui
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace) -> None:
    args.raw_response = True
    args.uri = args.endpoint
    if args.input is not None:
        response = fabric_api.do_request(args, json=args.input)
    elif args.file_path is not None:
        file_name = os.path.basename(args.file_path)
        with open(args.file_path, "rb") as file:
            file_content = {"file": (file_name, file)}
            response = fabric_api.do_request(args, files=file_content)
    else:
        response = fabric_api.do_request(args)

    # Build the JSON payload
    payload: Any = {
        "status_code": response.status_code,
    }

    if args.show_headers:
        payload["headers"] = dict(response.headers)

    payload["text"] = json.loads(response.text) if response.text.strip() else "(Empty)"

    # Filter based on JMESPath
    query = utils.process_nargs(args.query)
    if query:
        payload_jmespath = utils_jmespath.search(payload, query)
        if payload_jmespath:
            payload = payload_jmespath

    fab_ui.print_output_format(args, data=payload)
