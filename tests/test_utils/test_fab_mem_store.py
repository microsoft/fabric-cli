# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

import pytest

import fabric_cli.core.fab_state_config as state_config
import fabric_cli.utils.fab_mem_store as mem_store
from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.client import fab_api_connection as connection_api
from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.client import fab_api_gateway as gateway_api
from fabric_cli.client import fab_api_workspace as workspace_api
from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_hiearchy import (
    Item,
    Tenant,
    VirtualItem,
    VirtualItemContainer,
    VirtualWorkspace,
    VirtualWorkspaceItem,
    Workspace,
)


def test_add_worspace_to_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_list_workspaces(args):
        status_code = 200
        text = '{"value": [{"displayName": "default", "type": "Workspace", "id": "default_id"}]}'
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "list_workspaces", mock_api_list_workspaces)

    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, type="Workspace")
    _api_workspace = Workspace("default", "default_id", tenant, type="Workspace")

    mem_store.upsert_workspace_to_cache(workspace)
    assert mem_store.get_workspace_id(tenant, "ws_name.Workspace") == "ws_id"
    assert (
        mem_store.get_workspace_id(tenant=tenant, name="ws_name.Workspace") == "ws_id"
    )
    assert mem_store.get_workspace_id(tenant, name="ws_name.Workspace") == "ws_id"
    assert mem_store.get_workspace_id(tenant, "default.Workspace") == "default_id"
    assert (
        mem_store.get_workspace_id(tenant=tenant, name="default.Workspace")
        == "default_id"
    )
    assert mem_store.get_workspace_id(tenant, name="default.Workspace") == "default_id"

    assert mem_store.get_workspaces(tenant) == [_api_workspace, workspace]

    assert mem_store.get_workspaces(tenant=tenant) == [_api_workspace, workspace]


def test_update_worspace_to_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_list_workspaces(args):
        status_code = 200
        text = '{"value": []}'
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "list_workspaces", mock_api_list_workspaces)

    # Mocking the clear_cache function so that it does not clear the cache
    def mock_clear_cache():
        None

    # Mocking the clear function
    monkeypatch.setattr(
        mem_store._get_workspaces_from_cache.cache, "clear", mock_clear_cache
    )

    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, type="Workspace")
    workspace_updated = Workspace("renamed", "ws_id", tenant, type="Workspace")

    # Add a workspace to the cache
    mem_store.upsert_workspace_to_cache(workspace)
    # Check if the workspace is added to the cache
    assert mem_store.get_workspace_id(tenant, workspace.name) == workspace.id
    # Update the workspace name
    mem_store.upsert_workspace_to_cache(workspace_updated)
    # Check if the workspace name is updated in the cache
    assert (
        mem_store.get_workspace_id(tenant, workspace_updated.name)
        == workspace_updated.id
    )
    # Check that the previous name is not in the cache
    with pytest.raises(FabricCLIError) as e:
        mem_store.get_workspace_id(tenant, workspace.name)
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_delete_workspace_from_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_list_workspaces(args):
        status_code = 200
        text = '{"value": []}'
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "list_workspaces", mock_api_list_workspaces)

    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, type="Workspace")

    # Add a workspace to the cache
    mem_store.upsert_workspace_to_cache(workspace)
    # Check if the workspace is added to the cache
    assert mem_store.get_workspace_id(tenant, workspace.name) == workspace.id
    # Delete the workspace from the cache
    mem_store.delete_workspace_from_cache(workspace)
    # Check that the workspace is deleted from the cache
    with pytest.raises(FabricCLIError) as e:
        mem_store.get_workspace_id(tenant, workspace.name)
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_add_item_to_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")
    # Mocking the get_workspaces function so that it does not make an API call
    _items_from_api = {
        "value": [{"displayName": "itemName", "type": "Notebook", "id": "001"}]
    }
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, type="Workspace")
    item = Item("itemName", "001", workspace, "Notebook")
    _items_reply = [item]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_ls_workspaces(args, workspace_id):
        status_code = 200
        text = json.dumps(_items_from_api)
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "ls_workspace_items", mock_api_ls_workspaces)

    # Assert that workspace cache works
    assert mem_store.get_workspace_items(workspace) == _items_reply
    assert mem_store._get_workspace_items_from_cache.cache.currsize == 1
    assert mem_store.get_item_id(workspace, item.name) == item.id

    # After adding an item to the cache, the caches should have 0 items
    new_item = Item("item_name", "002", workspace, "Lakehouse")
    mem_store.upsert_item_to_cache(new_item)
    assert mem_store._get_workspace_items_from_cache.cache.currsize == 0


def test_delete_item_from_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")
    # Mocking the get_workspaces function so that it does not make an API call
    _items_from_api = {
        "value": [{"displayName": "itemName", "type": "Notebook", "id": "001"}]
    }
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    item = Item("itemName", "001", workspace, "Notebook")
    _items_reply = [item]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_ls_workspaces(args, workspace_id):
        status_code = 200
        text = json.dumps(_items_from_api)
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "ls_workspace_items", mock_api_ls_workspaces)

    # Assert that workspace cache works
    assert mem_store.get_workspace_items(workspace) == _items_reply
    assert mem_store._get_workspace_items_from_cache.cache.currsize == 1
    assert mem_store.get_item_id(workspace, item.name) == item.id

    # Delete the item from the cache
    mem_store.delete_item_from_cache(item)
    _items_from_api = {"value": []}

    # Check that the item is deleted from the cache
    with pytest.raises(FabricCLIError) as e:
        mem_store.get_item_id(workspace, item.name)
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_skip_unrecognized_item_type(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")
    # Mocking the get_workspaces function so that it does not make an API call
    _items_from_api = {
        "value": [
            {"displayName": "itemName", "type": "Notebook", "id": "001"},
            {"displayName": "otheritemName", "type": "Unrecognized", "id": "002"},
        ]
    }
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    item = Item("itemName", "001", workspace, "Notebook")
    _items_reply = [item]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_ls_workspaces(args, workspace_id):
        status_code = 200
        text = json.dumps(_items_from_api)
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "ls_workspace_items", mock_api_ls_workspaces)

    # Assert that workspace cache works
    assert mem_store.get_workspace_items(workspace) == _items_reply
    assert mem_store._get_workspace_items_from_cache.cache.currsize == 1
    assert mem_store.get_item_id(workspace, item.name) == item.id


def test_add_spark_pool_to_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")
    # Mocking the get_workspaces function so that it does not make an API call
    _spark_pools_from_api = {"value": [{"name": "poolName", "id": "001"}]}
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    container = VirtualItemContainer(".sparkpools", None, workspace)
    spark_pool = VirtualItem("poolName", "001", container, "SparkPool")
    _spark_pools_reply = [spark_pool]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_ls_spark_pools(args, workspace_id):
        status_code = 200
        text = json.dumps(_spark_pools_from_api)
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(
        workspace_api, "ls_workspace_spark_pools", mock_api_ls_spark_pools
    )

    # Assert that workspace cache works
    assert mem_store.get_spark_pools(container) == _spark_pools_reply
    assert mem_store._get_spark_pools_from_cache.cache.currsize == 1
    assert mem_store.get_spark_pool_id(container, spark_pool.name) == spark_pool.id

    # After adding an item to the cache, the caches should have 0 items
    new_spark_pool = VirtualItem("poolName", "002", container, "SparkPool")
    mem_store.upsert_spark_pool_to_cache(new_spark_pool)
    assert mem_store._get_spark_pools_from_cache.cache.currsize == 0


def test_delete_spark_pool_from_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")
    # Mocking the get_workspaces function so that it does not make an API call
    _spark_pools_from_api = {"value": [{"name": "poolName", "id": "001"}]}
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    container = VirtualItemContainer(".sparkpools", None, workspace)
    spark_pool = VirtualItem("poolName", "001", container, "SparkPool")
    _spark_pools_reply = [spark_pool]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_ls_spark_pools(args, workspace_id):
        status_code = 200
        text = json.dumps(_spark_pools_from_api)
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(
        workspace_api, "ls_workspace_spark_pools", mock_api_ls_spark_pools
    )

    # Assert that workspace cache works
    assert mem_store.get_spark_pools(container) == _spark_pools_reply
    assert mem_store._get_spark_pools_from_cache.cache.currsize == 1
    assert mem_store.get_spark_pool_id(container, spark_pool.name) == spark_pool.id

    # Delete the item from the cache
    mem_store.delete_spark_pool_from_cache(spark_pool)
    _spark_pools_from_api = {"value": []}

    # Check that the item is deleted from the cache
    with pytest.raises(FabricCLIError) as e:
        mem_store.get_spark_pool_id(container, spark_pool.name)
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_add_managed_identity_to_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    container = VirtualItemContainer(".managedIdentities", None, workspace)
    managed_identity = VirtualItem(
        "ws_name", "principal_id", container, "ManagedIdentity"
    )
    _managed_identities_reply = [managed_identity]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_get_workspace(args):
        status_code = 200
        text = '{"displayName": "ws_name", "type": "Workspace", "id": "default_id", "workspaceIdentity": {"servicePrincipalId": "principal_id"}}'
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "get_workspace", mock_api_get_workspace)

    # Assert that workspace cache works
    assert mem_store.get_managed_identities(container) == _managed_identities_reply
    assert mem_store._get_managed_identities_from_cache.cache.currsize == 1
    assert (
        mem_store.get_managed_identity_id(container, managed_identity.name)
        == managed_identity.id
    )

    # After adding an item to the cache, the caches should have 0 items
    new_managed_identity = VirtualItem(
        "identityName", "002", container, "ManagedIdentity"
    )
    mem_store.upsert_managed_identity_to_cache(new_managed_identity)
    assert mem_store._get_managed_identities_from_cache.cache.currsize == 0


def test_delete_managed_identity_from_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    _ws_reply = '{"displayName": "ws_name", "type": "Workspace", "id": "default_id", "workspaceIdentity": {"servicePrincipalId": "principal_id"}}'

    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    container = VirtualItemContainer(".managedIdentities", None, workspace)
    managed_identity = VirtualItem(
        "ws_name", "principal_id", container, "ManagedIdentity"
    )
    _managed_identities_reply = [managed_identity]

    # Mocking the get_workspaces function so that it does not make an API call
    def mock_api_get_workspace(args):
        status_code = 200
        text = _ws_reply
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(workspace_api, "get_workspace", mock_api_get_workspace)

    # Assert that workspace cache works
    assert mem_store.get_managed_identities(container) == _managed_identities_reply
    assert mem_store._get_managed_identities_from_cache.cache.currsize == 1
    assert (
        mem_store.get_managed_identity_id(container, managed_identity.name)
        == managed_identity.id
    )

    _ws_reply = '{"displayName": "ws_name", "type": "Workspace", "id": "default_id"}'

    # Delete the item from the cache
    mem_store.delete_managed_identity_from_cache(managed_identity)
    _managed_identities_reply = []

    # Check that the item is deleted from the cache
    with pytest.raises(FabricCLIError) as e:
        mem_store.get_managed_identity_id(container, managed_identity.name)
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_add_managed_private_endpoint_to_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    _api_reply = '{"value": [{"name": "mpe_name", "id": "mpe_id"}]}'
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    container = VirtualItemContainer(".managedPrivateEndpoints", None, workspace)
    managed_private_endpoint = VirtualItem(
        "mpe_name", "mpe_id", container, "ManagedPrivateEndpoint"
    )
    _managed_private_endpoints_reply = [managed_private_endpoint]

    def mock_api_ls_workspace_managed_private_endpoints(args):
        status_code = 200
        text = _api_reply
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(
        workspace_api,
        "ls_workspace_managed_private_endpoints",
        mock_api_ls_workspace_managed_private_endpoints,
    )

    # Assert that workspace cache works
    assert (
        mem_store.get_managed_private_endpoints(container)
        == _managed_private_endpoints_reply
    )
    assert mem_store._get_managed_private_endpoints_from_cache.cache.currsize == 1
    assert (
        mem_store.get_managed_private_endpoint_id(
            container, managed_private_endpoint.name
        )
        == managed_private_endpoint.id
    )

    # After adding an item to the cache, the caches should have 0 items
    new_managed_private_endpoint = VirtualItem(
        "identityName", "002", container, "ManagedPrivateEndpoint"
    )
    mem_store.upsert_managed_private_endpoint_to_cache(new_managed_private_endpoint)
    assert mem_store._get_managed_private_endpoints_from_cache.cache.currsize == 0


def test_delete_managed_private_endpoint_from_cache(monkeypatch):
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")

    _api_reply = '{"value": [{"name": "mpe_name", "id": "mpe_id"}]}'
    tenant = Tenant("tenant_name", "0000")
    workspace = Workspace("ws_name", "ws_id", tenant, "Workspace")
    container = VirtualItemContainer(".managedPrivateEndpoints", None, workspace)
    managed_private_endpoint = VirtualItem(
        "mpe_name", "mpe_id", container, "ManagedPrivateEndpoint"
    )
    _managed_private_endpoints_reply = [managed_private_endpoint]

    def mock_api_ls_workspace_managed_private_endpoints(args):
        status_code = 200
        text = _api_reply
        return type("", (), {"status_code": status_code, "text": text})

    # Mocking the clear function
    monkeypatch.setattr(
        workspace_api,
        "ls_workspace_managed_private_endpoints",
        mock_api_ls_workspace_managed_private_endpoints,
    )

    # Assert that workspace cache works
    assert (
        mem_store.get_managed_private_endpoints(container)
        == _managed_private_endpoints_reply
    )
    assert mem_store._get_managed_private_endpoints_from_cache.cache.currsize == 1
    assert (
        mem_store.get_managed_private_endpoint_id(
            container, managed_private_endpoint.name
        )
        == managed_private_endpoint.id
    )

    _api_reply = '{"value": []}'

    # Delete the item from the cache
    mem_store.delete_managed_private_endpoint_from_cache(managed_private_endpoint)
    _managed_private_endpoints_reply = []

    # Check that the item is deleted from the cache
    with pytest.raises(FabricCLIError) as e:
        mem_store.get_managed_private_endpoint_id(
            container, managed_private_endpoint.name
        )
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_gateways(monkeypatch):
    tenant = Tenant("tenant_name", "0000")
    virtual_ws = VirtualWorkspace(".gateways", "ws_id", tenant)
    gateway = VirtualWorkspaceItem("gw_name", "gw_id", virtual_ws, "Gateway")
    nameless_gateway = VirtualWorkspaceItem("gw_id", "gw_id", virtual_ws, "Gateway")
    _gateways_reply = [gateway, nameless_gateway]

    _api_reply = (
        '{"value": [{"displayName": "gw_name", "id": "gw_id"}, {"id": "gw_id"}]}'
    )

    def mock_api_list_gateways(args):
        status_code = 200
        text = _api_reply
        return type("", (), {"status_code": status_code, "text": text})

    monkeypatch.setattr(gateway_api, "list_gateways", mock_api_list_gateways)

    assert mem_store.get_gateways(virtual_ws) == _gateways_reply
    assert mem_store.get_gateway_id(virtual_ws, gateway.name) == gateway.id
    assert mem_store.get_gateway_id(virtual_ws, nameless_gateway.name) == gateway.id

    new_gateway = VirtualWorkspaceItem("new_gw_name", "gw_id", virtual_ws, "Gateway")

    mem_store.upsert_gateway_to_cache(new_gateway)

    # Upserting doesn't affect the cache, we still get the same result
    assert mem_store.get_gateways(virtual_ws) == _gateways_reply
    assert mem_store.get_gateway_id(virtual_ws, gateway.name) == new_gateway.id
    assert mem_store.get_gateway_id(virtual_ws, nameless_gateway.name) == gateway.id

    with pytest.raises(FabricCLIError) as e:
        mem_store.get_gateway_id(virtual_ws, "non_existent")
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_connections(monkeypatch):
    tenant = Tenant("tenant_name", "0000")
    virtual_ws = VirtualWorkspace(".connections", "ws_id", tenant)
    connection = VirtualWorkspaceItem("conn_name", "conn_id", virtual_ws, "Connection")
    nameless_con = VirtualWorkspaceItem("conn_id", "conn_id", virtual_ws, "Connection")
    _connections_reply = [connection, nameless_con]

    _api_reply = '{"value": [{"displayName": "conn_name", "id": "conn_id"}, {"displayName": null, "id": "conn_id"}]}'

    def mock_api_list_connections(args):
        status_code = 200
        text = _api_reply
        return type("", (), {"status_code": status_code, "text": text})

    monkeypatch.setattr(connection_api, "list_connections", mock_api_list_connections)

    assert mem_store.get_connections(virtual_ws) == _connections_reply
    assert mem_store.get_connection_id(virtual_ws, connection.name) == connection.id
    assert mem_store.get_connection_id(virtual_ws, nameless_con.name) == connection.id

    new_connection = VirtualWorkspaceItem(
        "new_conn_name", "conn_id", virtual_ws, "Connection"
    )

    mem_store.upsert_connection_to_cache(new_connection)

    # Upserting doesn't affect the cache, we still get the same result
    assert mem_store.get_connections(virtual_ws) == _connections_reply
    assert mem_store.get_connection_id(virtual_ws, connection.name) == new_connection.id
    assert (
        mem_store.get_connection_id(virtual_ws, nameless_con.name) == new_connection.id
    )

    with pytest.raises(FabricCLIError) as e:
        mem_store.get_connection_id(virtual_ws, "non_existent")
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_domains(monkeypatch):
    tenant = Tenant("tenant_name", "0000")
    virtual_ws = VirtualWorkspace(".domains", "ws_id", tenant)
    domain = VirtualWorkspaceItem("domain_name", "domain_id", virtual_ws, "Domain")
    _domains_reply = [domain]

    _api_reply = '{"domains": [{"displayName": "domain_name", "id": "domain_id"}]}'

    def mock_api_list_domains(args):
        status_code = 200
        text = _api_reply
        return type("", (), {"status_code": status_code, "text": text})

    monkeypatch.setattr(domain_api, "list_domains", mock_api_list_domains)

    assert mem_store.get_domains(virtual_ws) == _domains_reply
    assert mem_store.get_domain_id(virtual_ws, domain.name) == domain.id

    new_domain = VirtualWorkspaceItem(
        "new_domain_name", "domain_id", virtual_ws, "Domain"
    )

    mem_store.upsert_domain_to_cache(new_domain)

    # Upserting doesn't affect the cache, we still get the same result
    assert mem_store.get_domains(virtual_ws) == _domains_reply
    assert mem_store.get_domain_id(virtual_ws, domain.name) == new_domain.id

    with pytest.raises(FabricCLIError) as e:
        mem_store.get_domain_id(virtual_ws, "non_existent")
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_capacities(monkeypatch):
    tenant = Tenant("tenant_name", "0000")
    virtual_ws = VirtualWorkspace(".capacities", "ws_id", tenant)
    capacity = VirtualWorkspaceItem(
        "capacity_name", "capacity_id", virtual_ws, "Capacity"
    )
    _capacities_reply = [capacity]

    _api_reply = '{"value": [{"displayName": "capacity_name", "id": "capacity_id"}]}'

    def mock_api_list_capacities(args):
        status_code = 200
        text = _api_reply
        return type("", (), {"status_code": status_code, "text": text})

    monkeypatch.setattr(capacity_api, "list_capacities", mock_api_list_capacities)

    assert mem_store.get_capacities(virtual_ws) == _capacities_reply
    assert mem_store.get_capacity_id(virtual_ws, capacity.name) == capacity.id

    new_capacity = VirtualWorkspaceItem(
        "new_capacity_name", "capacity_id", virtual_ws, "Capacity"
    )

    mem_store.upsert_capacity_to_cache(new_capacity)

    # Upserting doesn't affect the cache, we still get the same result
    assert mem_store.get_capacities(virtual_ws) == _capacities_reply
    assert mem_store.get_capacity_id(virtual_ws, capacity.name) == new_capacity.id

    with pytest.raises(FabricCLIError) as e:
        mem_store.get_capacity_id(virtual_ws, "non_existent")
    assert e.value.status_code == con.ERROR_NOT_FOUND


def test_clear_caches():
    mem_store.clear_caches()
    state_config.set_config(con.FAB_CACHE_ENABLED, "true")
    mem_store._get_workspaces_from_cache.cache.update({"key": "value"})
    mem_store._get_workspace_items_from_cache.cache.update({"key": "value"})
    mem_store._get_spark_pools_from_cache.cache.update({"key": "value"})
    mem_store._get_managed_identities_from_cache.cache.update({"key": "value"})
    mem_store._get_managed_private_endpoints_from_cache.cache.update({"key": "value"})
    assert mem_store._get_workspaces_from_cache.cache.currsize == 1
    assert mem_store._get_workspace_items_from_cache.cache.currsize == 1
    assert mem_store._get_spark_pools_from_cache.cache.currsize == 1
    assert mem_store._get_managed_identities_from_cache.cache.currsize == 1
    assert mem_store._get_managed_private_endpoints_from_cache.cache.currsize == 1
    mem_store.clear_caches()
    assert mem_store._get_workspaces_from_cache.cache.currsize == 0
    assert mem_store._get_workspace_items_from_cache.cache.currsize == 0
    assert mem_store._get_spark_pools_from_cache.cache.currsize == 0
    assert mem_store._get_managed_identities_from_cache.cache.currsize == 0
    assert mem_store._get_managed_private_endpoints_from_cache.cache.currsize == 0
