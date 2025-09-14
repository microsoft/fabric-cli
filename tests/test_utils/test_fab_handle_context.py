# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

import pytest

import fabric_cli.core.fab_auth as auth
import fabric_cli.core.fab_handle_context as handle_context
import fabric_cli.utils.fab_mem_store as mem_store
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_types as types
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy import fab_hiearchy as hierarchy


def mock_get_fabric_ids(
    monkeypatch,
    tenant_id="0000",
    workspace_id="1111",
    item_id="2222",
    capacity_id="3333",
    connection_id="4444",
    gateway_id="5555",
    domain_id="6666",
    sparkpool_id="7777",
    managed_identity_id="8888",
    managed_private_endpoint_id="9999",
    # external_data_share_id="1010",
):
    ctxt = Context()

    _tenant = hierarchy.Tenant(name="tenant_name", id=tenant_id)

    def mock_get_tenant():
        return _tenant

    # monkeypatch.setattr(Context, "get_tenant", mock_get_tenant)
    monkeypatch.setattr(auth.FabAuth(), "get_tenant", mock_get_tenant)

    def mock_get_workspace_id(tenant, workspace_name):
        return workspace_id

    monkeypatch.setattr(mem_store, "get_workspace_id", mock_get_workspace_id)

    def mock_get_item_id(workspace, item_name):
        return item_id

    monkeypatch.setattr(mem_store, "get_item_id", mock_get_item_id)

    def mock_get_capacity_id(vws, capacity_name):
        return capacity_id

    monkeypatch.setattr(mem_store, "get_capacity_id", mock_get_capacity_id)

    def mock_get_connection_id(workspace, connection_name):
        return connection_id

    monkeypatch.setattr(mem_store, "get_connection_id", mock_get_connection_id)

    def mock_get_gateway_id(workspace, gateway_name):
        return gateway_id

    monkeypatch.setattr(mem_store, "get_gateway_id", mock_get_gateway_id)

    def mock_get_domain_id(workspace, domain_name):
        return domain_id

    monkeypatch.setattr(mem_store, "get_domain_id", mock_get_domain_id)

    def mock_get_sparkpool_id(virtual_item_container, sparkpool_name):
        return sparkpool_id

    monkeypatch.setattr(mem_store, "get_spark_pool_id", mock_get_sparkpool_id)

    def mock_get_managed_identity_id(virtual_item_container, managed_identity_name):
        return managed_identity_id

    monkeypatch.setattr(
        mem_store, "get_managed_identity_id", mock_get_managed_identity_id
    )

    def mock_get_managed_private_endpoint_id(
        virtual_item_container, managed_private_endpoint_name
    ):
        return managed_private_endpoint_id

    monkeypatch.setattr(
        mem_store,
        "get_managed_private_endpoint_id",
        mock_get_managed_private_endpoint_id,
    )

    # def mock_get_external_data_share_id(virtual_item_container, external_data_share_name):
    #    return external_data_share_id
    #
    # monkeypatch.setattr(mem_store, "get_external_data_share_id", mock_get_external_data_share_id)


def test_get_command_tenant(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Tenant("tenant_name", "0000")
    assert local_context == expected_context

    path = ".."
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context

    Context().context = handle_context.get_command_context("/cliws4.Workspace")
    path = ".."
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context


def test_get_command_context_absolute_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.Workspace"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    assert local_context == expected_context


def test_get_command_context_absolute_workspace_special_chars(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/My'Workspace\\/ for Work.Workspace"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Workspace(
        name="My'Workspace/ for Work",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    assert local_context == expected_context


def test_get_command_context_absolute_personal_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/My workspace.pErsonal"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Workspace(
        name="My workspace",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Personal",
    )
    assert local_context == expected_context


# def test_get_command_context_absolute_invalid_personal_workspace(monkeypatch):
#    mock_get_fabric_ids(monkeypatch)
#
#    path = "/Inv$alid.Personal"
#
#    with pytest.raises(FabricCLIError) as e:
#        handle_context.get_command_context(path)
#    assert str(e.value.status_code) == fab_constant.WARNING_INVALID_WORKSPACE_NAME


def test_get_command_context_absolute_invalid_workspace_type(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.W0rksp4c3/"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


# def test_get_command_context_absolute_invalid_workspace_name(monkeypatch):
#    mock_get_fabric_ids(monkeypatch)
#
#    path = "/cli*ws4.WorkSPace/"
#
#    with pytest.raises(FabricCLIError) as e:
#        handle_context.get_command_context(path)
#    assert str(e.value.status_code) == fab_constant.WARNING_INVALID_WORKSPACE_NAME


def test_get_command_context_absolute_item(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.WorkSPace/item1.notebook"
    normalized_path = "/cliws4.Workspace/item1.Notebook"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Item(
        name="item1",
        id="2222",
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Workspace",
        ),
        item_type="Notebook",
    )
    assert local_context == expected_context
    assert local_context.path == normalized_path


def test_get_command_context_absolute_invalid_item_type(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.WorkSPace/item1.Invalid"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


def test_get_command_context_absolute_invalid_item_name(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.WorkSPace/ite:m1.Lakehouse"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.WARNING_INVALID_SPECIAL_CHARACTERS


def test_get_command_context_absolute_onelake(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    def mock_get_onelake_details(path):
        response = Namespace()
        response.status_code = 200
        match path.split("/")[-1]:
            case "Tables" | "Files" | "TableMaintenance" | "MyDir" | "MyTable":
                response.headers = {"x-ms-resource-type": "directory"}
            case "MySht":
                response.headers = {
                    "x-ms-resource-type": "directory",
                    "x-ms-onelake-shortcut-path": "true",
                }
            case "MyFile.csv":
                response.headers = {"x-ms-resource-type": "file"}
            case _:
                raise Exception("Invalid path")

        return response

    monkeypatch.setattr(
        handle_context, "_get_onelake_details", mock_get_onelake_details
    )

    path = "/cliws4.Workspace/item1.Lakehouse/Tables/MyTable"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.OneLakeItem(
        name="MyTable",
        id="0000",
        parent=hierarchy.OneLakeItem(
            name="Tables",
            id="0000",
            parent=hierarchy.Item(
                name="item1",
                id="2222",
                parent=hierarchy.Workspace(
                    name="cliws4",
                    id="1111",
                    parent=hierarchy.Tenant("tenant_name", "0000"),
                    type="Workspace",
                ),
                item_type="Lakehouse",
            ),
            nested_type=types.OneLakeItemType.FOLDER,
        ),
        nested_type=types.OneLakeItemType.TABLE,
    )
    assert local_context == expected_context
    local_context.path == path

    path = "/cliws4.Workspace/item1.Lakehouse/Files/MyDir/MyFile.csv"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.OneLakeItem(
        name="MyFile.csv",
        id="0000",
        parent=hierarchy.OneLakeItem(
            name="MyDir",
            id="0000",
            parent=hierarchy.OneLakeItem(
                name="Files",
                id="0000",
                parent=hierarchy.Item(
                    name="item1",
                    id="2222",
                    parent=hierarchy.Workspace(
                        name="cliws4",
                        id="1111",
                        parent=hierarchy.Tenant("tenant_name", "0000"),
                        type="Workspace",
                    ),
                    item_type="Lakehouse",
                ),
                nested_type=types.OneLakeItemType.FOLDER,
            ),
            nested_type=types.OneLakeItemType.FOLDER,
        ),
        nested_type=types.OneLakeItemType.FILE,
    )
    assert local_context == expected_context
    local_context.path == path

    path = "/cliws4.Workspace/item1.Lakehouse/TableMaintenance"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.OneLakeItem(
        name="TableMaintenance",
        id="0000",
        parent=hierarchy.Item(
            name="item1",
            id="2222",
            parent=hierarchy.Workspace(
                name="cliws4",
                id="1111",
                parent=hierarchy.Tenant("tenant_name", "0000"),
                type="Workspace",
            ),
            item_type="Lakehouse",
        ),
        nested_type=types.OneLakeItemType.FOLDER,
    )
    assert local_context == expected_context
    local_context.path.rstrip("/") == path

    path = "/cliws4.Workspace/item1.Lakehouse/Files/MySht.Shortcut"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.OneLakeItem(
        name="MySht",
        id="0000",
        parent=hierarchy.OneLakeItem(
            name="Files",
            id="0000",
            parent=hierarchy.Item(
                name="item1",
                id="2222",
                parent=hierarchy.Workspace(
                    name="cliws4",
                    id="1111",
                    parent=hierarchy.Tenant("tenant_name", "0000"),
                    type="Workspace",
                ),
                item_type="Lakehouse",
            ),
            nested_type=types.OneLakeItemType.FOLDER,
        ),
        nested_type=types.OneLakeItemType.SHORTCUT,
    )
    assert local_context == expected_context
    local_context.path == path


def test_get_command_context_absolute_invalid(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.Workspace/..../cliws3.Workspace"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


def test_get_command_absolute_backwards_tenant(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.Workspace/.."
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Tenant("tenant_name", "0000")
    assert local_context == expected_context


def test_get_command_absolute_backwards_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = (
        "/cliws1.Workspace//item1.lakehouse/../../cliws2.Workspace/./item2.Lakehouse/.."
    )
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Workspace(
        name="cliws2",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    assert local_context == expected_context
    assert local_context.path == "/cliws2.Workspace"


def test_get_command_context_relative_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    Context().context = hierarchy.Tenant("tenant_name", "0000")
    path = "cliws4.Workspace"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    assert local_context == expected_context


def test_get_command_context_relative_home_workspace_spn(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    monkeypatch.setattr(
        auth.FabAuth(), "get_identity_type", lambda: "service_principal"
    )

    path = "~"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_OPERATION


def test_get_command_context_relative_home_workspace_nonexistent_user(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    monkeypatch.setattr(auth.FabAuth(), "get_identity_type", lambda: "user")

    _single_workspace_name = "My Workspace"
    _single_workspace = f"{_single_workspace_name}.Workspace"

    ("1111", _single_workspace)

    def mock_list_workspaces(args):
        return [
            hierarchy.Workspace(
                _single_workspace_name,
                "1111",
                hierarchy.Tenant("tenant_name", "0000"),
                "Workspace",
            )
        ]

    monkeypatch.setattr(mem_store, "get_workspaces", mock_list_workspaces)

    path = "~"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND


def test_get_command_context_relative_home_workspace_user(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    monkeypatch.setattr(auth.FabAuth(), "get_identity_type", lambda: "user")

    _personal_workspace = "My Workspace"

    def mock_list_workspaces(args):
        return [
            hierarchy.Workspace(
                "My Workspace",
                "1111",
                hierarchy.Tenant("tenant_name", "0000"),
                "Personal",
            )
        ]

    monkeypatch.setattr(mem_store, "get_workspaces", mock_list_workspaces)

    path = "~"
    expected_context = hierarchy.Workspace(
        name=_personal_workspace,
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Personal",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context
    assert local_context.path == f"/{_personal_workspace}.Personal"

    path = "~/"
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context
    assert local_context.path == f"/{_personal_workspace}.Personal"

    path = "~/item1.SparkJobDefinition"
    expected_context = hierarchy.Item(
        name="item1",
        id="2222",
        parent=hierarchy.Workspace(
            name=_personal_workspace,
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Personal",
        ),
        item_type="SparkJobDefinition",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context
    assert (
        local_context.path
        == f"/{_personal_workspace}.Personal/item1.SparkJobDefinition"
    )


def test_get_command_context_relative_invalid_home_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    monkeypatch.setattr(auth.FabAuth(), "get_identity_type", lambda: "user")

    _personal_workspace = "My Workspace"

    def mock_list_workspaces(args):
        return [
            hierarchy.Workspace(
                "My Workspace",
                "1111",
                hierarchy.Tenant("tenant_name", "0000"),
                "Personal",
            )
        ]

    monkeypatch.setattr(mem_store, "get_workspaces", mock_list_workspaces)

    path = "/~"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH

    path = "~/~"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


def test_get_command_context_relative_item(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    Context().context = hierarchy.Tenant("tenant_name", "0000")
    path = "cliws4.Workspace/item1.Lakehouse"
    expected_context = hierarchy.Item(
        name="item1",
        id="2222",
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Workspace",
        ),
        item_type="Lakehouse",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context


def test_get_command_context_relative(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    ws_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    Context().context = ws_context
    path = "item1.SparkJobDefinition/"
    expected_context = hierarchy.Item(
        name="item1",
        id="2222",
        parent=ws_context,
        item_type="SparkJobDefinition",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context


def test_get_command_context_relative_backwards_ws(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    ws_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    Context().context = ws_context
    path = "item1.SparkJobDefinition/../"
    local_context = handle_context.get_command_context(path)
    assert local_context == ws_context


def test_get_command_context_relative_backwards_tnt(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    ws_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    Context().context = ws_context
    path = ".."
    expected_context = hierarchy.Tenant("tenant_name", "0000")
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context


def test_get_command_context_relative_empty_path(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    ws_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    Context().context = ws_context
    path = ""
    local_context = handle_context.get_command_context(path)
    assert local_context == ws_context


def test_get_command_context_relative_current_path(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    item_context = hierarchy.Item(
        name="item1",
        id="2222",
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Workspace",
        ),
        item_type="SparkJobDefinition",
    )

    Context().context = item_context
    path = "."
    local_context = handle_context.get_command_context(path)
    assert local_context == item_context


def test_get_command_context_relative_previous_path(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    _tenant = hierarchy.Tenant("tenant_name", "0000")
    ws_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=_tenant,
        type="Workspace",
    )
    Context().context = ws_context
    path = ".."
    local_context = handle_context.get_command_context(path)
    assert local_context == _tenant


def test_get_command_context_relative_invalid_path(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    _tenant = hierarchy.Tenant("tenant_name", "0000")
    ws_context = hierarchy.Workspace(
        name="cliws4",
        id="1111",
        parent=_tenant,
        type="Workspace",
    )
    Context().context = ws_context
    path = "item1.SparkJobDefinition/..."
    with pytest.raises(FabricCLIError):
        handle_context.get_command_context(path)


def test_get_command_context_absolute_workspace_space(monkeypatch):
    mock_get_fabric_ids(monkeypatch)
    ws_context = hierarchy.Workspace(
        name="cli ws4",
        id="1111",
        parent=hierarchy.Tenant("tenant_name", "0000"),
        type="Workspace",
    )
    Context().context = ws_context

    path = "/cli ws4.Workspace"
    local_context = handle_context.get_command_context(path)
    assert local_context == ws_context

    path_array = path.split(" ")
    local_context = handle_context.get_command_context(path_array)
    assert local_context == ws_context


def test_get_command_context_invalid_workspace_name(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/cliws4.Workspace)"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH

    path = "/cliws4.Workspace$"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


def test_get_command_context_virtual_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/.capacities"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspace(
        name=".capacities",
        id=None,
        parent=hierarchy.Tenant("tenant_name", "0000"),
    )
    assert local_context == expected_context

    path = "/.connections"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspace(
        name=".connections",
        id=None,
        parent=hierarchy.Tenant("tenant_name", "0000"),
    )
    assert local_context == expected_context

    path = "/.gateways"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspace(
        name=".gateways",
        id=None,
        parent=hierarchy.Tenant("tenant_name", "0000"),
    )
    assert local_context == expected_context

    path = "/.domains"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspace(
        name=".domains",
        id=None,
        parent=hierarchy.Tenant("tenant_name", "0000"),
    )
    assert local_context == expected_context


def test_get_command_context_invalid_virtual_workspace(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/.invalid"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


def test_get_command_context_virtual_workspace_item(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/.capacities/item1.Capacity"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspaceItem(
        name="item1",
        id="3333",
        parent=hierarchy.VirtualWorkspace(
            name=".capacities",
            id=None,
            parent=hierarchy.Tenant("tenant_name", "0000"),
        ),
        item_type="Capacity",
    )
    assert local_context == expected_context

    path = "/.connections/item1.Connection"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspaceItem(
        name="item1",
        id="4444",
        parent=hierarchy.VirtualWorkspace(
            name=".connections",
            id=None,
            parent=hierarchy.Tenant("tenant_name", "0000"),
        ),
        item_type="Connection",
    )
    assert local_context == expected_context

    path = "/.gateways/item1.Gateway"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspaceItem(
        name="item1",
        id="5555",
        parent=hierarchy.VirtualWorkspace(
            name=".gateways",
            id=None,
            parent=hierarchy.Tenant("tenant_name", "0000"),
        ),
        item_type="Gateway",
    )
    assert local_context == expected_context

    path = "/.domains/item1.Domain"
    local_context = handle_context.get_command_context(path)
    expected_context = hierarchy.VirtualWorkspaceItem(
        name="item1",
        id="6666",
        parent=hierarchy.VirtualWorkspace(
            name=".domains",
            id=None,
            parent=hierarchy.Tenant("tenant_name", "0000"),
        ),
        item_type="Domain",
    )
    assert local_context == expected_context


def test_get_command_context_missing_virtual_workspace_item(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    def mock_get_vws_item_id(workspace, item_name):
        raise FabricCLIError("Item not found", fab_constant.ERROR_NOT_FOUND)

    monkeypatch.setattr(mem_store, "get_capacity_id", mock_get_vws_item_id)
    path = "/.capacities/item1.Capacity"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    monkeypatch.setattr(mem_store, "get_connection_id", mock_get_vws_item_id)
    path = "/.connections/item1.Connection"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    monkeypatch.setattr(mem_store, "get_gateway_id", mock_get_vws_item_id)
    path = "/.gateways/item1.Gateway"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    monkeypatch.setattr(mem_store, "get_domain_id", mock_get_vws_item_id)
    path = "/.domains/item1.Domain"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND


def test_get_command_context_non_traversable_item(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/myWorkspace.Workspace/MyDashboard.Dashboard/MyDashboardItem.DashboardItem"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_UNSUPPORTED_COMMAND


def test_get_command_context_non_traversable_virtual_item(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    path = "/.capacities/item1.Capacity/non_traversable"

    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_INVALID_PATH


def test_get_command_context_missing_ws(monkeypatch):
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")

    def mock_get_tenant():
        return _tenant

    # monkeypatch.setattr(Context, "get_tenant", mock_get_tenant)
    monkeypatch.setattr(auth.FabAuth(), "get_tenant", mock_get_tenant)

    def mock_get_workspace_id(tenant, workspace_name):
        raise FabricCLIError("Workspace not found", fab_constant.ERROR_NOT_FOUND)

    monkeypatch.setattr(mem_store, "get_workspace_id", mock_get_workspace_id)

    path = "/cliws4.WorkSPace/"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    path = "/cliws4.WorkSPace/"
    expected_context = hierarchy.Workspace(
        name="cliws4",
        id=None,
        parent=_tenant,
        type="Workspace",
    )
    local_context = handle_context.get_command_context(path, raise_error=False)
    assert expected_context == local_context

    path = "/cliws4.WorkSPace/item1.notebook"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path, raise_error=False)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND


def test_get_command_context_missing_item(monkeypatch):
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")

    def mock_get_tenant():
        return _tenant

    # monkeypatch.setattr(Context, "get_tenant", mock_get_tenant)
    monkeypatch.setattr(auth.FabAuth(), "get_tenant", mock_get_tenant)

    def mock_get_workspace_id(tenant, workspace_name):
        return "1111"

    monkeypatch.setattr(mem_store, "get_workspace_id", mock_get_workspace_id)

    def mock_get_item_id(workspace, item_name):
        raise FabricCLIError("Item not found", fab_constant.ERROR_NOT_FOUND)

    monkeypatch.setattr(mem_store, "get_item_id", mock_get_item_id)

    path = "/cliws4.WorkSPace/item1.lakehouse/Files"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path, raise_error=False)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    path = "/cliws4.WorkSPace/item1.lakehouse"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path, raise_error=True)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    path = "/cliws4.WorkSPace/item1.lakehouse"
    expected_context = hierarchy.Item(
        name="item1",
        id=None,
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=_tenant,
            type="Workspace",
        ),
        item_type="Lakehouse",
    )
    local_context = handle_context.get_command_context(path, raise_error=False)
    assert expected_context == local_context


def test_virtual_item_container(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    Context().context = hierarchy.Tenant("tenant_name", "0000")
    path = "cliws4.Workspace/.sparkpools"
    expected_context = hierarchy.VirtualItemContainer(
        name=".sparkpools",
        id=None,
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Workspace",
        ),
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context

    path = "cliws4.Workspace/.managedidentities"
    expected_context = hierarchy.VirtualItemContainer(
        name=".managedidentities",
        id=None,
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Workspace",
        ),
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context

    path = "cliws4.Workspace/.managedprivateendpoints"
    expected_context = hierarchy.VirtualItemContainer(
        name=".managedprivateendpoints",
        id=None,
        parent=hierarchy.Workspace(
            name="cliws4",
            id="1111",
            parent=hierarchy.Tenant("tenant_name", "0000"),
            type="Workspace",
        ),
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context


def test_virtual_items(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    Context().context = hierarchy.Tenant("tenant_name", "0000")
    path = "cliws4.Workspace/.sparkpools/item1.SparkPool"
    expected_context = hierarchy.VirtualItem(
        name="item1",
        id="7777",
        parent=hierarchy.VirtualItemContainer(
            name=".sparkpools",
            id=None,
            parent=hierarchy.Workspace(
                name="cliws4",
                id="1111",
                parent=hierarchy.Tenant("tenant_name", "0000"),
                type="Workspace",
            ),
        ),
        item_type="SparkPool",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context

    path = "cliws4.Workspace/.managedidentities/item1.ManagedIdentity"
    expected_context = hierarchy.VirtualItem(
        name="item1",
        id="8888",
        parent=hierarchy.VirtualItemContainer(
            name=".managedidentities",
            id=None,
            parent=hierarchy.Workspace(
                name="cliws4",
                id="1111",
                parent=hierarchy.Tenant("tenant_name", "0000"),
                type="Workspace",
            ),
        ),
        item_type="ManagedIdentity",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context

    path = "cliws4.Workspace/.managedprivateendpoints/item1.ManagedPrivateEndpoint"
    expected_context = hierarchy.VirtualItem(
        name="item1",
        id="9999",
        parent=hierarchy.VirtualItemContainer(
            name=".managedprivateendpoints",
            id=None,
            parent=hierarchy.Workspace(
                name="cliws4",
                id="1111",
                parent=hierarchy.Tenant("tenant_name", "0000"),
                type="Workspace",
            ),
        ),
        item_type="ManagedPrivateEndpoint",
    )
    local_context = handle_context.get_command_context(path)
    assert local_context == expected_context


def test_virtual_items_missing(monkeypatch):
    mock_get_fabric_ids(monkeypatch)

    def mock_get_missing_virtual_item_id(virtual_item_container, sparkpool_name):
        raise FabricCLIError("Sparkpool not found", fab_constant.ERROR_NOT_FOUND)

    monkeypatch.setattr(
        mem_store, "get_spark_pool_id", mock_get_missing_virtual_item_id
    )
    monkeypatch.setattr(
        mem_store, "get_managed_identity_id", mock_get_missing_virtual_item_id
    )
    monkeypatch.setattr(
        mem_store, "get_managed_private_endpoint_id", mock_get_missing_virtual_item_id
    )

    path = "cliws4.Workspace/.sparkpools/item1.SparkPool"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    path = "cliws4.Workspace/.managedidentities/item1.ManagedIdentity"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND

    path = "cliws4.Workspace/.managedprivateendpoints/item1.ManagedPrivateEndpoint"
    with pytest.raises(FabricCLIError) as e:
        handle_context.get_command_context(path)
    assert str(e.value.status_code) == fab_constant.ERROR_NOT_FOUND
