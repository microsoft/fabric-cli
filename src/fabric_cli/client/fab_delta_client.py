# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from deltalake import DeltaTable
from deltalake.exceptions import DeltaError

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages

# Item types whose OneLake Tables/ folder contains standard Delta tables.
# SemanticModel is explicitly excluded: its Tables/ entries are columnar
# semantic-model representations, not Delta-compatible parquet.
_DELTA_SUPPORTED_ITEM_TYPES: frozenset[str] = frozenset(
    {
        "Lakehouse",
        "Warehouse",
        "KQLDatabase",
        "MirroredDatabase",
        "SQLDatabase",
    }
)


def get_table_schema(args: Namespace, local_path: str) -> list[dict]:
    """Return schema fields for a Delta table on OneLake.

    Single seam for DeltaTable construction: owns item-type validation,
    URI building, storage_options assembly, token acquisition, and
    exception mapping.
    """
    item_type = getattr(args, "item_type", None)
    if item_type is not None and item_type not in _DELTA_SUPPORTED_ITEM_TYPES:
        raise FabricCLIError(
            ErrorMessages.Table.unsupported_item_type_for_delta(item_type),
            fab_constant.ERROR_INVALID_ITEM_TYPE,
        )

    token = FabAuth().get_access_token(fab_constant.SCOPE_ONELAKE_DEFAULT)
    if token is None:
        raise FabricCLIError(
            ErrorMessages.Auth.access_token_failed(),
            fab_constant.ERROR_AUTHENTICATION_FAILED,
        )

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
        schema_dict = json.loads(table.schema().to_json())
        schema_fields = schema_dict.get("fields")
        if not isinstance(schema_fields, list):
            raise ValueError(
                "Delta table schema JSON does not contain a valid 'fields' list."
            )
        return schema_fields
    except (DeltaError, json.JSONDecodeError, ValueError) as exc:
        raise FabricCLIError(
            "Failed to extract the table schema. Please ensure the path points to a valid Delta table.",
            fab_constant.ERROR_INVALID_DELTA_TABLE,
        ) from exc
