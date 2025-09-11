# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core.hiearchy.fab_hiearchy import Workspace
from fabric_cli.utils import fab_cmd_get_utils as utils_get


def exec(workspace: Workspace, args: Namespace, verbose: bool = True) -> dict:
    args.ws_id = workspace.id

    workspace_def = {}
    response = workspace_api.get_workspace(args)

    if response.status_code == 200:
        workspace_def = json.loads(response.text)

        # Add managed private endpoints
        try:
            managed_private_endpoints = (
                workspace_api.ls_workspace_managed_private_endpoints(args)
            )
            if managed_private_endpoints.status_code == 200:
                managed_private_endpoints_def = json.loads(
                    managed_private_endpoints.text
                )
                workspace_def["managedPrivateEndpoints"] = (
                    managed_private_endpoints_def["value"]
                )
        except Exception:
            pass

        # Add Spark settings
        try:
            spark_settings = workspace_api.get_workspace_spark_settings(args)
            if spark_settings.status_code == 200:
                spark_settings_def = json.loads(spark_settings.text)
                workspace_def["sparkSettings"] = spark_settings_def
        except Exception:
            pass

        # Add role assignments
        try:
            acls = workspace_api.acl_list_from_workspace(args)
            if acls.status_code == 200:
                acls_def = json.loads(acls.text)
                workspace_def["roleAssignments"] = acls_def["value"]
        except Exception:
            pass

        utils_get.query_and_export(workspace_def, args, workspace.full_name, verbose)

    return workspace_def
