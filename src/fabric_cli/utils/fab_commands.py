# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core import fab_constant
from fabric_cli.utils.fab_util import get_os_specific_command

COMMANDS = {
    "Core Commands": {
        "assign": "Assign a capacity or resource to a workspace.",
        "cd": "Change to a workspace, item, or folder.",
        get_os_specific_command("cp"): "Copy an item or file.",
        "export": "Export an item.",
        "exists": "Check if a workspace, item, or file exists.",
        "get": "Get workspace or item properties.",
        "import": "Import an item to create or update it.",
        get_os_specific_command("ls"): "List workspaces, items, and files.",
        get_os_specific_command("ln"): "Create a shortcut.",
        "mkdir": "Create a workspace, item, or directory.",
        get_os_specific_command("mv"): "Move an item or file.",
        "open": "Open a workspace or item in the browser.",
        "pwd": "Print the current working directory.",
        get_os_specific_command(
            "rm"
        ): "Delete a workspace, item, or file.",
        "set": "Set workspace or item properties.",
        "start": "Start a resource.",
        "stop": "Stop a resource.",
        "unassign": "Unassign a resource from a workspace.",
    },
    "Resource Commands": {
        "acl": fab_constant.COMMAND_ACLS_DESCRIPTION,
        "label": fab_constant.COMMAND_LABELS_DESCRIPTION,
        "job": fab_constant.COMMAND_JOBS_DESCRIPTION,
        "table": fab_constant.COMMAND_TABLES_DESCRIPTION,
    },
    "Util Commands": {
        "api": fab_constant.COMMAND_API_DESCRIPTION,
        "auth": fab_constant.COMMAND_AUTH_DESCRIPTION,
        "config": fab_constant.COMMAND_CONFIG_DESCRIPTION,
        "desc": fab_constant.COMMAND_DESCRIBE_DESCRIPTION,
    },
    "Flags": {
        "--help": "Show help for command.",
        "--version": "Show version.",
    },
}
