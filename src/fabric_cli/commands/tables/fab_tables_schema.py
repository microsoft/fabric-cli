# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_delta_client as delta_client
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace) -> None:
    schema_fields = _get_table_schema(args)
    fab_ui.print_grey("Schema extracted successfully")
    fab_ui.print_output_format(args, data=schema_fields, show_headers=True)


def _get_table_schema(args: Namespace) -> list[dict]:
    return delta_client.get_table_schema(args, args.table_local_path)
