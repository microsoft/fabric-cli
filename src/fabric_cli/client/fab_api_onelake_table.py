# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Client for the OneLake table APIs.

OneLake exposes a dedicated REST endpoint for interacting with tables in Fabric
(https://onelake.table.fabric.microsoft.com). It surfaces read-only metadata
operations compatible with two open standards:

- Delta tables, via the Unity Catalog API, under the ``/delta`` base path.
- Iceberg tables, via the Iceberg REST Catalog (IRC) API, under the ``/iceberg``
  base path.

The endpoint accepts the same token audience as the OneLake filesystem endpoints
(the Azure Storage audience), so every call here uses the ``onelake_table``
audience which reuses ``SCOPE_ONELAKE_DEFAULT`` while targeting the table host.

Overview: https://learn.microsoft.com/en-us/fabric/onelake/table-apis/table-apis-overview

Each function reads the following attributes from ``args`` (a ``Namespace``):

- ``ws_id``: workspace name or ID.
- ``item_id``: data item (e.g. lakehouse) name or ID.
- ``schema_name``: schema (namespace) name.
- ``table_name``: table name.
- ``prefix``: Iceberg prefix returned by :func:`get_config`.
"""

from argparse import Namespace

from fabric_cli.client import fab_api_client as fabric_api
from fabric_cli.client.fab_api_types import ApiResponse

_AUDIENCE = "onelake_table"
_DELTA_BASE = "delta"
_ICEBERG_BASE = "iceberg"
_UNITY_CATALOG = "api/2.1/unity-catalog"


# Delta (Unity Catalog) operations


def list_schemas(args: Namespace) -> ApiResponse:
    """List the schemas within a data item.

    If the data item doesn't support schemas, a fixed ``dbo`` schema is returned.
    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/delta-table-apis-overview
    """
    args.uri = (
        f"{_DELTA_BASE}/{args.ws_id}/{args.item_id}/{_UNITY_CATALOG}/schemas"
        f"?catalog_name={args.item_id}"
    )
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def list_tables(args: Namespace) -> ApiResponse:
    """List the tables found within a given schema.

    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/delta-table-apis-overview
    """
    args.uri = (
        f"{_DELTA_BASE}/{args.ws_id}/{args.item_id}/{_UNITY_CATALOG}/tables"
        f"?catalog_name={args.item_id}&schema_name={args.schema_name}"
    )
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def get_table(args: Namespace) -> ApiResponse:
    """Get metadata details for a table within a schema.

    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/delta-table-apis-overview
    """
    args.uri = (
        f"{_DELTA_BASE}/{args.ws_id}/{args.item_id}/{_UNITY_CATALOG}/tables/"
        f"{args.table_name}"
    )
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def schema_exists(args: Namespace) -> ApiResponse:
    """Check whether a schema exists within a data item.

    Returns a successful response if the schema is found (a 404 is raised
    centrally as a NotFound error otherwise).
    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/delta-table-apis-overview
    """
    args.uri = (
        f"{_DELTA_BASE}/{args.ws_id}/{args.item_id}/{_UNITY_CATALOG}/schemas/"
        f"{args.schema_name}"
    )
    args.method = "head"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def table_exists(args: Namespace) -> ApiResponse:
    """Check whether a table exists within a schema.

    Returns a successful response if the table is found (a 404 is raised
    centrally as a NotFound error otherwise).
    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/delta-table-apis-overview
    """
    args.uri = (
        f"{_DELTA_BASE}/{args.ws_id}/{args.item_id}/{_UNITY_CATALOG}/tables/"
        f"{args.table_name}"
    )
    args.method = "head"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


# Iceberg (Iceberg REST Catalog) operations


def get_config(args: Namespace) -> ApiResponse:
    """Get the Iceberg REST Catalog configuration for a data item.

    Returns the ``Prefix`` string used in subsequent requests. The warehouse is
    ``<WorkspaceID>/<dataItemID>``.
    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/iceberg-table-apis-overview
    """
    args.uri = f"{_ICEBERG_BASE}/v1/config?warehouse={args.ws_id}/{args.item_id}"
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def list_namespaces(args: Namespace) -> ApiResponse:
    """List the namespaces (schemas) within a data item.

    If the data item doesn't support schemas, a fixed ``dbo`` namespace is
    returned. ``prefix`` is obtained from :func:`get_config`.
    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/iceberg-table-apis-overview
    """
    args.uri = f"{_ICEBERG_BASE}/v1/{args.prefix}/namespaces"
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def get_namespace(args: Namespace) -> ApiResponse:
    """Get information about a namespace (schema) within a data item.

    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/iceberg-table-apis-overview
    """
    args.uri = f"{_ICEBERG_BASE}/v1/{args.prefix}/namespaces/{args.schema_name}"
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def list_iceberg_tables(args: Namespace) -> ApiResponse:
    """List the tables found within a given namespace (schema).

    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/iceberg-table-apis-overview
    """
    args.uri = f"{_ICEBERG_BASE}/v1/{args.prefix}/namespaces/{args.schema_name}/tables"
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)


def get_iceberg_table(args: Namespace) -> ApiResponse:
    """Get metadata details for a table within a namespace (schema).

    https://learn.microsoft.com/en-us/fabric/onelake/table-apis/iceberg-table-apis-overview
    """
    args.uri = (
        f"{_ICEBERG_BASE}/v1/{args.prefix}/namespaces/{args.schema_name}/tables/"
        f"{args.table_name}"
    )
    args.method = "get"
    args.audience = _AUDIENCE

    return fabric_api.do_request(args)
