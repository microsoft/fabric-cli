# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from typing import Optional

from cachetools import TTLCache, cached, keys

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.client import fab_api_folders as folders_api
from fabric_cli.client import fab_api_gateway as gateway_api
from fabric_cli.client import fab_api_item as item_api
from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core import fab_state_config as state_config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import VirtualItemType, VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_hiearchy import (
    ExternalDataShareVirtualItem,
    Folder,
    Item,
    Tenant,
    VirtualItem,
    VirtualItemContainer,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_item_util as item_utils

# Workspaces


def _get_workspaces_from_api(tenant: Tenant) -> list[Workspace]:
    workspaces = []
    args = Namespace()
    response = workspace_api.list_workspaces(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        for ws in data["value"]:
            try:
                ws = Workspace(ws["displayName"], ws["id"], tenant, ws["type"])
            except FabricCLIError as e:
                if e.status_code == fab_constant.ERROR_INVALID_WORKSPACE_TYPE:
                    pass
                else:
                    raise e
            else:
                workspaces.append(ws)

    return workspaces


# We add the explicit function to build the cache key for the item id
# This is necessary because unnamed and named arguments generate different cache keys
# by default, and we need to be able to generate the same cache key for the same arguments
def build_ws_cache_key(tenant: Tenant):
    return keys.hashkey(tenant.id)


@cached(TTLCache(maxsize=1024, ttl=60), key=build_ws_cache_key)
def _get_workspaces_from_cache(tenant: Tenant) -> list[Workspace]:
    return _get_workspaces_from_api(tenant)


def get_workspaces(tenant: Tenant) -> list[Workspace]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_workspaces_from_cache(tenant)
    return _get_workspaces_from_api(tenant)


def _get_workspace_id_from_api(tenant: Tenant, ws_name: str):

    workspaces = get_workspaces(tenant)

    for ws in workspaces:
        if ws.name == ws_name:
            return ws.id

    return None


def get_workspace_id(tenant: Tenant, name) -> str:
    ws_id = _get_workspace_id_from_api(tenant, name)

    if ws_id is None:
        _get_workspaces_from_cache.cache.clear()
        ws_id = _get_workspace_id_from_api(tenant, name)

    if ws_id:
        return ws_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Workspace", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def _upsert_workspace_to_cache_list(workspace: Workspace):
    tenant = workspace.tenant
    # Retrieve existing workspaces from the cache or API
    _cache_key = build_ws_cache_key(tenant)
    workspaces: list[Workspace] = _get_workspaces_from_cache.cache.get(
        _cache_key, _get_workspaces_from_api(tenant)
    )

    # If there is a workspace with the same id, update it
    _update = False
    for i, ws in enumerate(workspaces):
        if ws.id == workspace.id:
            workspaces[i] = workspace
            _update = True
            break
    # If there is no workspace with the same id, add it
    if not _update:
        workspaces.append(workspace)

    # Update the cache with the new list of workspaces
    _get_workspaces_from_cache.cache.__setitem__(_cache_key, workspaces)


def upsert_workspace_to_cache(workspace: Workspace):
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        _upsert_workspace_to_cache_list(workspace)


def _delete_workspace_from_cache_list(workspace: Workspace):
    worspaces = get_workspaces(workspace.tenant)
    # Look for the workspace in the cache and delete it
    for i, ws in enumerate(worspaces):
        if workspace.id == ws.id:
            worspaces.pop(i)
            break
    cache_key = build_ws_cache_key(workspace.tenant)
    _get_workspaces_from_cache.cache.__setitem__(cache_key, worspaces)


def delete_workspace_from_cache(workspace: Workspace):
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        _delete_workspace_from_cache_list(workspace)


# Capacities


def get_capacities(tenant: Tenant) -> list[VirtualWorkspaceItem]:
    capacities = []
    args = Namespace()
    response = capacity_api.list_capacities(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        capacities = []
        for cp in data["value"]:
            capacity = VirtualWorkspaceItem(
                cp["displayName"],
                cp["id"],
                tenant,
                VirtualWorkspaceItemType.CAPACITY,
            )
            capacities.append(capacity)

    return capacities


def _get_capacity_id(tenant: Tenant, capacity_name: str) -> str:

    capacities = get_capacities(tenant)

    for c in capacities:
        if c.name == capacity_name:
            return c.id

    return None


def get_capacity_id(tenant: Tenant, name) -> str:
    capacity_name = name.strip("/")
    capacity_id = _get_capacity_id(tenant, capacity_name)

    if capacity_id:
        return capacity_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Capacity", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_capacity_to_cache(capacity: VirtualWorkspaceItem) -> None:
    return


def delete_capacity_from_cache(capacity: VirtualWorkspaceItem) -> None:
    return


# Connections


def get_connections(tenant: Tenant) -> list[VirtualWorkspaceItem]:
    connections = []
    args = Namespace()
    response = connection_api.list_connections(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        connections = []
        for cp in data["value"]:
            connection = VirtualWorkspaceItem(
                cp["displayName"] if cp["displayName"] else cp["id"],
                cp["id"],
                tenant,
                VirtualWorkspaceItemType.CONNECTION,
            )
            connections.append(connection)

    return connections


def _get_connection_id(tenant: Tenant, connection_name: str) -> str:

    connections = get_connections(tenant)

    for c in connections:
        if c.name == connection_name:
            return c.id

    return None


def get_connection_id(tenant: Tenant, name) -> str:
    connection_name = name.strip("/")
    connection_id = _get_connection_id(tenant, connection_name)

    if connection_id:
        return connection_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Connection", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_connection_to_cache(connection: VirtualWorkspaceItem) -> None:
    return


def delete_connection_from_cache(connection: VirtualWorkspaceItem) -> None:
    return


# Gateways


def get_gateways(tenant: Tenant) -> list[VirtualWorkspaceItem]:
    gateways = []
    args = Namespace()
    response = gateway_api.list_gateways(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        gateways = []
        for cp in data["value"]:
            gateway = VirtualWorkspaceItem(
                cp["displayName"] if "displayName" in cp else cp["id"],
                cp["id"],
                tenant,
                VirtualWorkspaceItemType.GATEWAY,
            )
            gateways.append(gateway)

    return gateways


def _get_gateway_id(tenant: Tenant, gateway_name: str) -> str:

    gateways = get_gateways(tenant)

    for c in gateways:
        if c.name == gateway_name:
            return c.id

    return None


def get_gateway_id(tenant: Tenant, name) -> str:
    gateway_name = name.strip("/")
    gateway_id = _get_gateway_id(tenant, gateway_name)

    if gateway_id:
        return gateway_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Gateway", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_gateway_to_cache(gateway: VirtualWorkspaceItem) -> None:
    return


def delete_gateway_from_cache(gateway: VirtualWorkspaceItem) -> None:
    return


# Domains


def get_domains(tenant: Tenant) -> list[VirtualWorkspaceItem]:
    domains = []
    args = Namespace()
    response = domain_api.list_domains(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        for d in data["domains"]:
            domain = VirtualWorkspaceItem(
                d["displayName"],
                d["id"],
                tenant,
                VirtualWorkspaceItemType.DOMAIN,
            )
            domains.append(domain)

    return domains


def _get_domain_id(tenant: Tenant, domain_name: str) -> str:

    domains = get_domains(tenant)

    for d in domains:
        if d.name == domain_name:
            return d.id

    return None


def get_domain_id(tenant: Tenant, name) -> str:
    domain_name = name.strip("/")
    domain_id = _get_domain_id(tenant, domain_name)

    if domain_id:
        return domain_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Domain", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_domain_to_cache(domain: VirtualWorkspaceItem) -> None:
    return


def delete_domain_from_cache(domain: VirtualWorkspaceItem) -> None:
    return


# Items


# We add the explicit function to build the cache key for the item id
# This is necessary because unnamed and named arguments generate different cache keys
# by default, and we need to be able to generate the same cache key for the same arguments
def build_item_cache_key(workspace: Workspace):
    # Combine args and kwargs into a single key
    return keys.hashkey((workspace.tenant.id, workspace.id))


def _get_workspace_items_from_api(workspace: Workspace) -> list[Item]:
    items = []
    args = Namespace()
    response = workspace_api.ls_workspace_items(args, workspace.id)
    # Seems to be a bug in the API, for which Mirrored Databases are duplicated, one as a MirroredDatabase and other as MirroredWarehouse
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        items = []
        for item in data["value"]:
            try:
                items.append(
                    Item(
                        item["displayName"],
                        item["id"],
                        (
                            workspace
                            if "folderId" not in item
                            else get_folder(workspace, item["folderId"])
                        ),
                        item["type"],
                    )
                )
            except FabricCLIError as e:
                if e.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE:
                    pass
                else:
                    raise e

    return items


@cached(TTLCache(maxsize=1024, ttl=60), key=build_item_cache_key)
def _get_workspace_items_from_cache(workspace: Workspace) -> list[Item]:
    return _get_workspace_items_from_api(workspace)


def get_workspace_items(workspace: Workspace) -> list[Item]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_workspace_items_from_cache(workspace)
    return _get_workspace_items_from_api(workspace)


def _get_item_id(workspace: Workspace, item_name: str) -> str:
    ws_items = get_workspace_items(workspace)
    for item in ws_items:
        if item.name == item_name:
            return item.id
    return None


def get_item_id(workspace: Workspace, name) -> str:
    item_name = name.strip("/")
    item_id = _get_item_id(workspace, item_name)

    # if not found, invalidate the cache and try again
    if item_id is None:
        _get_workspace_items_from_cache.cache.clear()
        item_id = _get_item_id(workspace, item_name)

    if item_id:
        return item_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Item", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_item_to_cache(item: Item) -> None:
    # Invalidate both item cache and folder cache to maintain consistency
    # when creating items inside folders
    invalidate_item_cache(item.parent)
    
    if isinstance(item.parent, Folder):
        invalidate_folder_cache(item.workspace)


def invalidate_item_cache(workspace: Workspace) -> None:
    # Invalidation of the cache for the workspace
    cache_key = build_item_cache_key(workspace)
    if _get_workspace_items_from_cache.cache.get(cache_key, None) is not None:
        del _get_workspace_items_from_cache.cache[cache_key]


def delete_item_from_cache(item: Item) -> None:
    # Due to dependent elements (e.g. SQLEndpoint for Lakehouse), we need to invalidate the cache
    invalidate_item_cache(item.parent)


# Folders


# We add the explicit function to build the cache key for the folder id
# This is necessary because unnamed and named arguments generate different cache keys
# by default, and we need to be able to generate the same cache key for the same arguments
def build_folder_cache_key(workspace: Workspace):
    # Combine args and kwargs into a single key
    return keys.hashkey((workspace.tenant.id, workspace.id))


def _extract_root_folders(
    folder: dict, cli_folders: list[Folder], workspace: Workspace
) -> bool:
    if "parentFolderId" not in folder:
        cli_folders.append(Folder(folder["displayName"], folder["id"], workspace))
        return True
    return False


def _extract_nested_folders(folder: dict, cli_folders: list[Folder]) -> bool:
    parent_folder = next(
        (f for f in cli_folders if f.id == folder["parentFolderId"]), None
    )
    if parent_folder:
        cli_folders.append(
            Folder(
                folder["displayName"],
                folder["id"],
                parent_folder,
            )
        )
        return True
    return False


def _get_workspace_folders_from_api(workspace: Workspace) -> list[Folder]:
    cli_folders: list[Folder] = []
    args = Namespace()
    args.ws_id = workspace.id
    response = folders_api.list_folders(args)
    # Seems to be a bug in the API, for which Mirrored Databases are duplicated, one as a MirroredDatabase and other as MirroredWarehouse
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        json_folders = data["value"]
        # Extract Root folders
        json_folders[:] = [
            f
            for f in json_folders
            if not _extract_root_folders(f, cli_folders, workspace)
        ]

        while len(json_folders) > 0:
            json_folders[:] = [
                f for f in json_folders if not _extract_nested_folders(f, cli_folders)
            ]

    return cli_folders


@cached(TTLCache(maxsize=1024, ttl=60), key=build_folder_cache_key)
def _get_workspace_folders_from_cache(workspace: Workspace) -> list[Folder]:
    return _get_workspace_folders_from_api(workspace)


def get_workspace_folders(workspace: Workspace) -> list[Folder]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_workspace_folders_from_cache(workspace)
    return _get_workspace_folders_from_api(workspace)


def _get_folder_id(workspace: Workspace, folder_name: str) -> Optional[str]:
    ws_folders = get_workspace_folders(workspace)
    for folder in ws_folders:
        if folder.name == folder_name:
            return folder.id
    return None


def get_folder_id(workspace: Workspace, name) -> str:
    folder_name = name.strip("/")
    folder_id = _get_folder_id(workspace, folder_name)

    # if not found, invalidate the cache and try again
    if folder_id is None:
        _get_workspace_folders_from_cache.cache.clear()
        folder_id = _get_folder_id(workspace, folder_name)

    if folder_id:
        return folder_id

    raise FabricCLIError(
        ErrorMessages.Common.folder_not_found(name), fab_constant.ERROR_NOT_FOUND
    )


def _get_nested_folder_id(folder: Folder, folder_name: str) -> Optional[str]:
    ws_folders = get_workspace_folders(folder.workspace)
    for f in ws_folders:
        if f.parent == folder and f.name == folder_name:
            return f.id
    return None


def get_nested_folder_id(folder: Folder, name) -> str:
    folder_name = name.strip("/")
    folder_id = _get_nested_folder_id(folder, folder_name)

    # if not found, invalidate the cache and try again
    if folder_id is None:
        _get_workspace_folders_from_cache.cache.clear()
        folder_id = _get_nested_folder_id(folder, folder_name)

    if folder_id:
        return folder_id

    raise FabricCLIError(
        ErrorMessages.Common.folder_not_found(name), fab_constant.ERROR_NOT_FOUND
    )


def get_folder(workspace: Workspace, id: str) -> Folder:
    ws_folders = get_workspace_folders(workspace)
    for folder in ws_folders:
        if folder.id == id:
            return folder
    return None


def upsert_folder_to_cache(folder: Folder) -> None:
    invalidate_folder_cache(folder.workspace)


def invalidate_folder_cache(workspace: Workspace) -> None:
    # Invalidation of the cache for the workspace
    cache_key = build_folder_cache_key(workspace)
    if _get_workspace_folders_from_cache.cache.get(cache_key, None) is not None:
        del _get_workspace_folders_from_cache.cache[cache_key]


def delete_folder_from_cache(folder: Folder) -> None:
    invalidate_folder_cache(folder.workspace)


# Virtual Items


def build_virtual_item_cache_key(container: VirtualItemContainer):
    # Combine args and kwargs into a single key
    return keys.hashkey((container.tenant.id, container.workspace.id))


def build_virtual_item_id_cache_key(
    container: VirtualItemContainer | Workspace, item: Item
):
    workspace_id = (
        container.id if isinstance(container, Workspace) else container.workspace.id
    )
    return keys.hashkey(container.tenant.id, workspace_id, item.id)


# SSpark Pools


def _get_spark_pools_from_api(container: VirtualItemContainer) -> list[VirtualItem]:
    spark_pools = []
    args = Namespace()
    response = workspace_api.ls_workspace_spark_pools(args, container.workspace.id)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        for sp in data["value"]:
            spark_pool = VirtualItem(
                sp["name"],
                sp["id"],
                container,
                str(VirtualItemType.SPARK_POOL),
            )
            spark_pools.append(spark_pool)

    return spark_pools


@cached(TTLCache(maxsize=1024, ttl=60), key=build_virtual_item_cache_key)
def _get_spark_pools_from_cache(container: VirtualItemContainer) -> list[VirtualItem]:
    return _get_spark_pools_from_api(container)


def get_spark_pools(container: VirtualItemContainer) -> list[VirtualItem]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_spark_pools_from_cache(container)
    return _get_spark_pools_from_api(container)


def _get_spark_pool_id(container: VirtualItemContainer, spark_pool_name: str) -> str:
    ws_spark_pools = get_spark_pools(container)
    for sp in ws_spark_pools:
        if sp.name == spark_pool_name:
            return sp.id
    return None


def get_spark_pool_id(container: VirtualItemContainer, name) -> str:
    spark_pool_name = name.strip("/")
    spark_pool_id = _get_spark_pool_id(container, spark_pool_name)

    # if not found, invalidate the cache and try again
    if spark_pool_id is None:
        _get_spark_pools_from_cache.cache.clear()
        spark_pool_id = _get_spark_pool_id(container, spark_pool_name)

    if spark_pool_id:
        return spark_pool_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found({"type": "Spark Pool", "name": name}),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_spark_pool_to_cache(spark_pool: VirtualItem) -> None:
    invalidate_spark_pool_cache(spark_pool.parent)


def invalidate_spark_pool_cache(container: VirtualItemContainer) -> None:
    # Invalidation of the cache for the workspace
    cache_key = build_virtual_item_cache_key(container)
    if _get_spark_pools_from_cache.cache.get(cache_key, None) is not None:
        del _get_spark_pools_from_cache.cache[cache_key]


def delete_spark_pool_from_cache(spark_pool: VirtualItem) -> None:
    invalidate_spark_pool_cache(spark_pool.parent)


# S Managed Identities


def _get_managed_identities_from_api(
    container: VirtualItemContainer,
) -> list[VirtualItem]:
    ws_name = container.workspace.short_name
    managed_identities = []
    args = Namespace()
    args.ws_id = container.workspace.id
    response = workspace_api.get_workspace(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        managed_identity_data = data.get("workspaceIdentity", None)
        if managed_identity_data:
            mng_identity = VirtualItem(
                ws_name,  # Managed Identities are only one per workspace and have the workspace name
                managed_identity_data["servicePrincipalId"],
                container,
                str(VirtualItemType.MANAGED_IDENTITY),
            )
            managed_identities.append(mng_identity)

    return managed_identities


@cached(TTLCache(maxsize=1024, ttl=60), key=build_virtual_item_cache_key)
def _get_managed_identities_from_cache(
    container: VirtualItemContainer,
) -> list[VirtualItem]:
    return _get_managed_identities_from_api(container)


def get_managed_identities(container: VirtualItemContainer) -> list[VirtualItem]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_managed_identities_from_cache(container)
    return _get_managed_identities_from_api(container)


def _get_managed_identity_id(
    container: VirtualItemContainer, managed_identity_name: str
) -> str:
    ws_managed_identities = get_managed_identities(container)
    for mi in ws_managed_identities:
        if mi.name == managed_identity_name:
            return mi.id
    return None


def get_managed_identity_id(container: VirtualItemContainer, name) -> str:
    managed_identity_name = name.strip("/")
    managed_identity_id = _get_managed_identity_id(container, managed_identity_name)

    # if not found, invalidate the cache and try again
    if managed_identity_id is None:
        _get_managed_identities_from_cache.cache.clear()
        managed_identity_id = _get_managed_identity_id(container, managed_identity_name)

    if managed_identity_id:
        return managed_identity_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found(
            {"type": "Managed Identity", "name": name}
        ),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_managed_identity_to_cache(managed_identity: VirtualItem) -> None:
    invalidate_managed_identity_cache(managed_identity.parent)


def invalidate_managed_identity_cache(container: VirtualItemContainer) -> None:
    # Invalidation of the cache for the workspace
    cache_key = build_virtual_item_cache_key(container)
    if _get_managed_identities_from_cache.cache.get(cache_key, None) is not None:
        del _get_managed_identities_from_cache.cache[cache_key]


def delete_managed_identity_from_cache(managed_identity: VirtualItem) -> None:
    invalidate_managed_identity_cache(managed_identity.parent)


# Managed Private Endpoints


def _get_managed_private_endpoints_from_api(
    container: VirtualItemContainer,
) -> list[VirtualItem]:
    managed_private_endpoints = []
    args = Namespace()
    args.ws_id = container.workspace.id
    response = workspace_api.ls_workspace_managed_private_endpoints(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        for sp in data["value"]:
            mpe = VirtualItem(
                sp["name"],
                sp["id"],
                container,
                str(VirtualItemType.MANAGED_PRIVATE_ENDPOINT),
            )
            managed_private_endpoints.append(mpe)

    return managed_private_endpoints


@cached(TTLCache(maxsize=1024, ttl=60), key=build_virtual_item_cache_key)
def _get_managed_private_endpoints_from_cache(
    container: VirtualItemContainer,
) -> list[VirtualItem]:
    return _get_managed_private_endpoints_from_api(container)


def get_managed_private_endpoints(container: VirtualItemContainer) -> list[VirtualItem]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_managed_private_endpoints_from_cache(container)
    return _get_managed_private_endpoints_from_api(container)


def _get_managed_private_endpoint_id(
    container: VirtualItemContainer, managed_private_endpoint_name: str
) -> str:
    ws_managed_private_endpoints = get_managed_private_endpoints(container)
    for mpe in ws_managed_private_endpoints:
        if mpe.name == managed_private_endpoint_name:
            return mpe.id
    return None


def get_managed_private_endpoint_id(container: VirtualItemContainer, name) -> str:
    managed_private_endpoint_name = name.strip("/")
    managed_private_endpoint_id = _get_managed_private_endpoint_id(
        container, managed_private_endpoint_name
    )

    # if not found, invalidate the cache and try again
    if managed_private_endpoint_id is None:
        _get_managed_private_endpoints_from_cache.cache.clear()
        managed_private_endpoint_id = _get_managed_private_endpoint_id(
            container, managed_private_endpoint_name
        )

    if managed_private_endpoint_id:
        return managed_private_endpoint_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found(
            {"type": "Managed Private Endpoint", "name": name}
        ),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_managed_private_endpoint_to_cache(
    managed_private_endpoint: VirtualItem,
) -> None:
    invalidate_managed_private_endpoint_cache(managed_private_endpoint.parent)


def invalidate_managed_private_endpoint_cache(container: VirtualItemContainer) -> None:
    # Invalidation of the cache for the workspace
    cache_key = build_virtual_item_cache_key(container)
    if _get_managed_private_endpoints_from_cache.cache.get(cache_key, None) is not None:
        del _get_managed_private_endpoints_from_cache.cache[cache_key]


def delete_managed_private_endpoint_from_cache(
    managed_private_endpoint: VirtualItem,
) -> None:
    invalidate_managed_private_endpoint_cache(managed_private_endpoint.parent)


#  External Data Shares


def get_external_data_shares(
    container: Workspace,
) -> list[ExternalDataShareVirtualItem]:
    external_data_shares = []
    external_data_shares_for_item = []
    args = Namespace()
    args.ws_id = container.id

    ws_items = get_workspace_items(container)

    for item in ws_items:
        if item.item_type in item_utils.item_types_supporting_external_data_shares():
            external_data_shares_for_item = get_external_data_shares_for_item(
                container, item
            )
            for eds in external_data_shares_for_item:
                external_data_shares.append(eds)

    return external_data_shares


def get_external_data_shares_for_item(
    container: Workspace, item: Item
) -> list[ExternalDataShareVirtualItem]:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        return _get_external_data_shares_for_item_from_cache(container, item)
    return _get_external_data_shares_for_item_from_api(container, item)


@cached(TTLCache(maxsize=1024, ttl=600), key=build_virtual_item_id_cache_key)
def _get_external_data_shares_for_item_from_cache(
    container: Workspace, item: Item
) -> list[ExternalDataShareVirtualItem]:
    return _get_external_data_shares_for_item_from_api(container, item)


def _get_external_data_shares_for_item_from_api(
    container: Workspace, item: Item
) -> list[ExternalDataShareVirtualItem]:
    external_data_shares_for_item = []
    args = Namespace()
    args.ws_id = container.id
    args.item_id = item.id

    response = item_api.list_item_external_data_shares(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        for eds in data["value"]:
            try:
                external_data_shares_for_item.append(
                    ExternalDataShareVirtualItem(
                        item_utils.get_external_data_share_name(item.name, eds["id"]),
                        eds["id"],
                        container,
                        str(VirtualItemType.EXTERNAL_DATA_SHARE),
                        eds["status"],
                        eds["itemId"],
                    )
                )
            except FabricCLIError as e:
                if e.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE:
                    pass
                else:
                    raise e

    return external_data_shares_for_item


def _get_external_data_share_id(
    ws_container: Workspace, external_data_share_name: str
) -> str:
    item_name = item_utils.get_item_name_from_eds_name(external_data_share_name)
    item_id = get_item_id(ws_container, item_name)
    item = Item(
        item_name.split(".")[0],
        item_id,
        ws_container,
        item_name.split(".")[1],
    )
    item_external_data_shares = get_external_data_shares_for_item(ws_container, item)
    for eds in item_external_data_shares:
        if eds.name == external_data_share_name:
            return eds.id
    return None


def get_external_data_share_id(container: VirtualItemContainer, name) -> str:
    external_data_share_name = name.strip("/")
    ws_container = container.parent
    external_data_share_id = _get_external_data_share_id(
        ws_container, external_data_share_name
    )

    if external_data_share_id:
        return external_data_share_id

    raise FabricCLIError(
        ErrorMessages.Common.resource_not_found(
            {"type": "External Data Share", "name": name}
        ),
        fab_constant.ERROR_NOT_FOUND,
    )


def upsert_external_data_share_to_cache(
    external_data_share: VirtualItem, item: Item
) -> None:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        _invalidate_external_data_share_cache(external_data_share.parent, item)


def _invalidate_external_data_share_cache(
    container: VirtualItemContainer, item: Item
) -> None:
    # Invalidation of the cache for the workspace Item
    item_cache_key = build_virtual_item_id_cache_key(container, item)
    if (
        _get_external_data_shares_for_item_from_cache.cache.get(item_cache_key, None)
        is not None
    ):
        del _get_external_data_shares_for_item_from_cache.cache[item_cache_key]


def delete_external_data_share_from_cache(
    external_data_share: VirtualItem,
) -> None:
    if state_config.get_config(fab_constant.FAB_CACHE_ENABLED) == "true":
        item_name = item_utils.get_item_name_from_eds_name(external_data_share.name)
        ws_container = external_data_share.workspace
        item_id = get_item_id(ws_container, item_name)
        item = Item(
            item_name.split(".")[0],
            item_id,
            ws_container,
            item_name.split(".")[1],
        )
        _invalidate_external_data_share_cache(external_data_share.parent, item)


# Clear caches


def clear_caches() -> None:
    _get_workspaces_from_cache.cache.clear()
    _get_workspace_items_from_cache.cache.clear()
    _get_spark_pools_from_cache.cache.clear()
    _get_managed_identities_from_cache.cache.clear()
    _get_managed_private_endpoints_from_cache.cache.clear()
    _get_external_data_shares_for_item_from_cache.cache.clear()
    fab_logger.log_debug("Caches cleared")
