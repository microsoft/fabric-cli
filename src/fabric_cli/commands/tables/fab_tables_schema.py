# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from deltalake import DeltaTable
from deltalake.exceptions import TableNotFoundError

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace) -> None:
    schema_fields = _get_table_schema(args)
    fab_ui.print_grey("Schema extracted successfully")
    fab_ui.print_output_format(args, data=schema_fields, show_headers=True)


def _get_table_schema(args: Namespace) -> list[dict]:
    token = FabAuth().get_access_token(fab_constant.SCOPE_ONELAKE_DEFAULT)
    if args.schema:
        local_path = f"Tables/{args.schema}/{args.table_name}"
    else:
        local_path = f"Tables/{args.table_name}"

    table_uri = (
        f"abfss://{args.ws_id}@{fab_constant.API_ENDPOINT_ONELAKE}"
        f"/{args.lakehouse_id}/{local_path}"
    )

    try:
        table = DeltaTable(
            table_uri,
            storage_options={
                "bearer_token": token,
                "use_fabric_endpoint": "true",
            },
        )
        return table.schema().json()["fields"]
    except TableNotFoundError:
        raise FabricCLIError(
            "Failed to extract the table schema. Please ensure the path points to a valid Delta table",
            fab_constant.ERROR_INVALID_DELTA_TABLE,
        )
