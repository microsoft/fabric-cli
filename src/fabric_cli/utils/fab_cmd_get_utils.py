# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Any, Optional

from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client import fab_api_mirroring as mirroring_api
from fabric_cli.utils import fab_jmespath as utils_jmespath
from fabric_cli.utils import fab_storage as utils_storage
from fabric_cli.utils import fab_ui as utils_ui


def is_metadata_property_query(query: str) -> bool:
    """
    Check if the query is for a metadata property or nested sub-property.
    
    Examples:
        - "properties" -> True (exact match)
        - "properties.connectionString" -> True (nested property)
        - "id" -> True (exact match)
        - "someOtherField" -> False (not a metadata property)
    
    Args:
        query: The query string to check (assumed to be non-empty)
        
    Returns:
        bool: True if query matches a metadata property or its nested properties
    """
    from fabric_cli.core import fab_constant

    # Extract root property and check if it's a valid metadata property
    # This handles both exact matches and nested properties in one step
    root_property = query.split('.')[0]
    return root_property in fab_constant.ITEM_METADATA_PROPERTIES


def query_and_export(
    data: Any, args: Namespace, file_name: str, verbose: bool = True
) -> None:
    json_path_response = utils_jmespath.search(
        data, args.query, getattr(args, "deep_traversal", None)
    )

    if args.output:
        utils_storage.do_output(data=json_path_response, file_name=file_name, args=args)
    elif json_path_response and verbose:
        utils_ui.print_output_format(args, data=json_path_response)


def get_environment_metadata(item_def: dict, args: Namespace) -> dict:
    # Fetch libraries for published
    args.ext_uri = "/libraries"
    try:
        env_libraries = item_api.get_item(args, item_uri=True, ext_uri=True)
        if env_libraries.status_code == 200:
            env_libraries_def = json.loads(env_libraries.text)
            item_def.setdefault("published", {})["libraries"] = env_libraries_def
    except Exception as e:
        item_def.setdefault("published", {})["libraries"] = []

    # Fetch libraries for staging
    args.ext_uri = "/staging/libraries"
    try:
        env_libraries_staging = item_api.get_item(args, item_uri=True, ext_uri=True)
        if env_libraries_staging.status_code == 200:
            env_libraries_staging_def = json.loads(env_libraries_staging.text)
            item_def.setdefault("staging", {})["libraries"] = env_libraries_staging_def
    except Exception as e:
        item_def.setdefault("staging", {})["libraries"] = []

    # Fetch sparkComputeSettings for published
    args.ext_uri = "/sparkcompute"
    try:
        env_spark_compute = item_api.get_item(args, item_uri=True, ext_uri=True)
        if env_spark_compute.status_code == 200:
            env_spark_compute_def = json.loads(env_spark_compute.text)
            item_def.setdefault("published", {})[
                "sparkComputeSettings"
            ] = env_spark_compute_def
    except Exception as e:
        item_def.setdefault("published", {})["sparkComputeSettings"] = []

    # Fetch sparkComputeSettings for staging
    args.ext_uri = "/staging/sparkcompute"
    try:
        env_spark_compute_staging = item_api.get_item(args, item_uri=True, ext_uri=True)
        if env_spark_compute_staging.status_code == 200:
            env_spark_compute_staging_def = json.loads(env_spark_compute_staging.text)
            item_def.setdefault("staging", {})[
                "sparkComputeSettings"
            ] = env_spark_compute_staging_def
    except Exception as e:
        item_def.setdefault("staging", {})["sparkComputeSettings"] = []

    return item_def


def get_mirroreddb_metadata(item_def: dict, args: Namespace) -> dict:
    # Fetch status
    try:
        status = mirroring_api.get_mirroring_status(args)
        if status.status_code == 200:
            status_def = json.loads(status.text)
            item_def["status"] = status_def
    except Exception as e:
        item_def["status"] = []

    # Fetch tablesStatus
    try:
        tables_status = mirroring_api.get_table_mirroring_status(args)
        if tables_status.status_code == 200:
            tables_status_def = json.loads(tables_status.text)
            item_def["tablesStatus"] = tables_status_def["data"]
    except Exception as e:
        item_def["tablesStatus"] = []

    return item_def
