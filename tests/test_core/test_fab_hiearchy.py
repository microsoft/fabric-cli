# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest

import fabric_cli.core.fab_constant as fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import *
from fabric_cli.core.hiearchy.fab_hiearchy import *


def test_create_tenant():
    tenant = Tenant(name="tenant_name", id="0000")
    assert tenant.id == "0000"
    assert tenant.name == "tenant_name.Tenant"
    assert tenant.type == FabricElementType.TENANT
    assert tenant.parent is None
    assert tenant.path == "/"
    assert tenant.check_command_support(Command.FS_LS)


def test_create_workspace():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    assert workspace.parent == tenant
    assert workspace.tenant.id == "0000"
    assert workspace.tenant.name == "tenant_name.Tenant"
    assert workspace.id == "workspace_id"
    assert workspace.name == "workspace_name.Workspace"
    assert workspace.type == FabricElementType.WORKSPACE
    assert workspace.path == "/workspace_name.Workspace"
    assert tenant.check_command_support(Command.FS_LS)

    assert str(workspace) == "[Workspace] (workspace_name, workspace_id)"


def test_create_invalid_workspace():
    tenant = Tenant(name="tenant_name", id="0000")

    with pytest.raises(FabricCLIError) as e:
        Workspace(
            name="workspace_name", id="workspace_id", parent=tenant, type="Invalid"
        )
    assert e.value.status_code == fab_constant.ERROR_INVALID_WORKSPACE_TYPE


def test_create_virtual_workspace():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = VirtualWorkspace(
        name=".capacities", id="virtual_workspace_id", parent=tenant
    )
    assert workspace.parent == tenant
    assert workspace.tenant.id == "0000"
    assert workspace.tenant.name == "tenant_name.Tenant"
    assert workspace.id == "virtual_workspace_id"
    assert workspace.name == ".capacities"
    assert workspace.type == FabricElementType.VIRTUAL_WORKSPACE
    assert workspace.vws_type == VirtualWorkspaceType.CAPACITY
    assert workspace.path == "/.capacities"
    assert workspace.check_command_support(Command.FS_LS)


def test_create_invalid_virtual_workspace():
    tenant = Tenant(name="tenant_name", id="0000")

    with pytest.raises(FabricCLIError) as e:
        VirtualWorkspace(name="_invalid", id="workspace_id", parent=tenant)
    assert e.value.status_code == fab_constant.ERROR_INVALID_WORKSPACE_TYPE


def test_create_item():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    item = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="Lakehouse",
    )
    assert item.parent == workspace
    assert item.tenant.id == "0000"
    assert item.tenant.name == "tenant_name.Tenant"
    assert item.workspace.id == "workspace_id"
    assert item.workspace.name == "workspace_name.Workspace"
    assert item.id == "item_id"
    assert item.name == "item_name.Lakehouse"
    assert item.type == FabricElementType.ITEM
    assert item.item_type == ItemType.LAKEHOUSE
    assert item.path == "/workspace_name.Workspace/item_name.Lakehouse"
    assert item.job_type == FabricJobType.TABLE_MAINTENANCE
    item.check_command_support(Command.FS_CD)

    # Raise error on unsupported command
    with pytest.raises(FabricCLIError) as e:
        item.check_command_support(Command.ACL_SET)
    assert e.value.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND


def test_create_invalid_item():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )

    with pytest.raises(FabricCLIError) as e:
        Item(
            name="item_name",
            id="item_id",
            parent=workspace,
            item_type="Invalid",
        )
    assert e.value.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE

    with pytest.raises(FabricCLIError) as e:
        Item(
            name="item_name",
            id=None,
            parent=workspace,
            item_type="Inv$lid",
        )
    assert e.value.status_code == fab_constant.WARNING_INVALID_ITEM_NAME


def test_create_virtual_item():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="My workspace", id="workspace_id", parent=tenant, type="Personal"
    )
    container = VirtualItemContainer(name=".sparkpools", id=None, parent=workspace)
    item = VirtualItem(
        name="mySparkPool",
        id="virtual_item_id",
        parent=container,
        item_type="SparkPool",
    )
    assert item.parent == container
    assert item.workspace == workspace
    assert item.tenant.id == "0000"
    assert item.tenant.name == "tenant_name.Tenant"
    assert item.workspace.id == "workspace_id"
    assert item.workspace.name == "My workspace.Personal"
    assert item.id == "virtual_item_id"
    assert item.name == "mySparkPool.SparkPool"
    assert item.type == FabricElementType.VIRTUAL_ITEM
    assert item.item_type == VirtualItemType.SPARK_POOL
    assert item.path == "/My workspace.Personal/.sparkpools/mySparkPool.SparkPool"
    assert item.check_command_support(Command.FS_EXISTS)


def test_create_virtual_workspace_item():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = VirtualWorkspace(
        name=".capacities", id="virtual_workspace_id", parent=tenant
    )
    item = VirtualWorkspaceItem(
        name="c01",
        id="virtual_item_id",
        parent=workspace,
        item_type="Capacity",
    )
    assert item.parent == workspace
    assert item.tenant.id == "0000"
    assert item.tenant.name == "tenant_name.Tenant"
    assert item.workspace.id == "virtual_workspace_id"
    assert item.workspace.name == ".capacities"
    assert item.id == "virtual_item_id"
    assert item.name == "c01.Capacity"
    assert item.type == FabricElementType.VIRTUAL_WORKSPACE_ITEM
    assert item.item_type == VirtualWorkspaceItemType.CAPACITY
    assert item.path == "/.capacities/c01.Capacity"
    assert item.check_command_support(Command.FS_EXISTS)


def test_create_onelakeelement():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    item = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="Lakehouse",
    )
    onelake_root = OneLakeItem(
        name="Files",
        id="0000",
        parent=item,
        nested_type=OneLakeItemType.FOLDER,
    )
    onelake_folder = OneLakeItem(
        name="some_folder",
        id="0000",
        parent=onelake_root,
        nested_type=OneLakeItemType.FOLDER,
    )
    onelake_file = OneLakeItem(
        name="file.csv",
        id="0000",
        parent=onelake_folder,
        nested_type=OneLakeItemType.FILE,
    )

    assert onelake_file.parent == onelake_folder
    assert onelake_file.tenant.id == "0000"
    assert onelake_file.tenant.name == "tenant_name.Tenant"
    assert onelake_file.workspace.id == "workspace_id"
    assert onelake_file.workspace.name == "workspace_name.Workspace"
    assert onelake_file.item == item
    assert onelake_file.item.id == "item_id"
    assert onelake_file.item.name == "item_name.Lakehouse"
    assert onelake_file.item.item_type == ItemType.LAKEHOUSE
    assert onelake_file.id == "0000"
    assert onelake_file.name == "file.csv"
    assert onelake_file.type == FabricElementType.ONELAKE
    assert onelake_file.nested_type == OneLakeItemType.FILE
    assert (
        onelake_file.path
        == "/workspace_name.Workspace/item_name.Lakehouse/Files/some_folder/file.csv"
    )
    assert onelake_file.local_path == "Files/some_folder/file.csv"
    assert onelake_file.check_command_support(Command.FS_EXISTS)
    assert onelake_file.path_id == "/workspace_id/item_id/Files/some_folder/file.csv"
    assert onelake_file.root_folder == "Files"
    assert onelake_file.is_shortcut_path() == False

    onelake_copy = OneLakeItem(
        name="file.csv",
        id="0000",
        parent=onelake_folder,
        nested_type=OneLakeItemType.FILE,
    )
    assert onelake_file == onelake_copy

    # Different path
    onelake_different_folder = OneLakeItem(
        name="different_folder",
        id="0000",
        parent=onelake_root,
        nested_type=OneLakeItemType.FOLDER,
    )
    onelake_copy = OneLakeItem(
        name="file.csv",
        id="0000",
        parent=onelake_different_folder,
        nested_type=OneLakeItemType.FILE,
    )
    assert onelake_file != onelake_copy

    # Different type
    onelake_copy = OneLakeItem(
        name="file.csv",
        id="0000",
        parent=onelake_folder,
        nested_type=OneLakeItemType.TABLE,
    )

    assert onelake_file != onelake_copy


def test_create_invalid_virtualworkspace_item_type():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = VirtualWorkspace(
        name=".capacities", id="virtual_workspace_id", parent=tenant
    )

    with pytest.raises(FabricCLIError) as e:
        VirtualWorkspaceItem(
            name="c01",
            id="virtual_item_id",
            parent=workspace,
            item_type="Invalid",
        )
    assert e.value.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE


def test_create_invalid_virtualworkspace():
    tenant = Tenant(name="tenant_name", id="0000")

    with pytest.raises(FabricCLIError) as e:
        VirtualWorkspace(name="_invalid", id="workspace_id", parent=tenant)
    assert e.value.status_code == fab_constant.ERROR_INVALID_WORKSPACE_TYPE


def test_create_invalid_virtual_item_container():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Personal"
    )

    with pytest.raises(FabricCLIError) as e:
        VirtualItemContainer(name="invalid", id=None, parent=workspace)
    assert e.value.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE


def test_create_invalid_virtual_item():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    virtual_item_container = VirtualItemContainer(
        name=".sparkpools", id=None, parent=workspace
    )

    with pytest.raises(FabricCLIError) as e:
        VirtualItem(
            name="myFolder",
            id="virtual_item_id",
            parent=virtual_item_container,
            item_type="Invalid",
        )
    assert e.value.status_code == fab_constant.ERROR_INVALID_ITEM_TYPE


def test_command_support():
    # TODO: Improve using custom config and not rely on the default one
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    lakehouse_item = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="Lakehouse",
    )
    lakehouse_item.check_command_support(Command.FS_CD)

    # Raise error on unsupported command for missing support
    with pytest.raises(FabricCLIError) as e:
        lakehouse_item.check_command_support(Command.ACL_SET)
    assert e.value.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND

    report_item = Item(
        name="report_name",
        id="report_id",
        parent=workspace,
        item_type="Report",
    )
    # Case of explicit supported item for command
    report_item.check_command_support(Command.FS_IMPORT)
    # Case of explicit unsupported item for command
    with pytest.raises(FabricCLIError) as e:
        report_item.check_command_support(Command.FS_START)
    assert e.value.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND


def test_create_virtual_item_container():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="My workspace", id="workspace_id", parent=tenant, type="Personal"
    )
    container = VirtualItemContainer(name=".sparkpools", id=None, parent=workspace)
    assert container.parent == workspace
    assert container.tenant.id == "0000"
    assert container.tenant.name == "tenant_name.Tenant"
    assert container.workspace.id == "workspace_id"
    assert container.workspace.name == "My workspace.Personal"
    assert container.id == None
    assert container.name == ".sparkpools"
    assert container.type == FabricElementType.VIRTUAL_ITEM_CONTAINER
    assert container.vic_type == VirtualItemContainerType.SPARK_POOL
    assert container.item_type == VirtualItemType.SPARK_POOL

    assert container.path == "/My workspace.Personal/.sparkpools"
    assert container.path_id == "/workspace_id"
    assert container.check_command_support(Command.FS_CD)


def test_get_item_payloads():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )

    _base_payload = {
        "parts": {
            "key": "value",
        }
    }

    # Test Notebook
    notebook = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="Notebook",
    )

    _expected_payload = {
        "type": "Notebook",
        "description": "Imported from fab",
        "displayName": "item_name",
        "folderId": None,
        "definition": {"format": "ipynb", "parts": _base_payload["parts"]},
    }

    # Check that the payload is correct
    assert notebook.get_payload(_base_payload) == _expected_payload

    # Test Spark Job Definition
    spark_job_def = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="SparkJobDefinition",
    )

    _expected_payload = {
        "type": "SparkJobDefinition",
        "description": "Imported from fab",
        "displayName": "item_name",
        "folderId": None,
        "definition": {
            "format": "SparkJobDefinitionV1",
            "parts": _base_payload["parts"],
        },
    }

    # Check that the payload is correct
    assert spark_job_def.get_payload(_base_payload) == _expected_payload

    # Test EventHouse
    event_house = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="EventHouse",
    )

    _expected_payload = {
        "type": "Eventhouse",
        "description": "Imported from fab",
        "displayName": "item_name",
        "folderId": None,
        "definition": _base_payload,
    }

    # Check that the payload is correct
    assert event_house.get_payload(_base_payload) == _expected_payload

    # Test Report
    report = Item(
        name="item_name",
        id="item_id",
        parent=workspace,
        item_type="Report",
    )

    _expected_payload = {
        "type": "Report",
        "description": "Imported from fab",
        "displayName": "item_name",
        "folderId": None,
        "definition": _base_payload,
    }

    # Check that the payload is correct
    assert report.get_payload(_base_payload) == _expected_payload

    # Unsuported item
    with pytest.raises(FabricCLIError) as e:
        unsupported_item = Item(
            name="item_name",
            id="item_id",
            parent=workspace,
            item_type="Lakehouse",
        )
        unsupported_item.get_payload(_base_payload)
    assert e.value.status_code == fab_constant.ERROR_UNSUPPORTED_COMMAND


def test_create_folder():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    folder = Folder(name="folder_name", id="folder_id", parent=workspace)
    assert folder.parent == workspace
    assert folder.tenant.id == "0000"
    assert folder.tenant.name == "tenant_name.Tenant"
    assert folder.workspace.id == "workspace_id"
    assert folder.workspace.name == "workspace_name.Workspace"
    assert folder.id == "folder_id"
    assert folder.name == "folder_name.Folder"
    assert folder.type == FabricElementType.FOLDER
    assert folder.path == "/workspace_name.Workspace/folder_name.Folder"
    assert folder.check_command_support(Command.FS_LS)


def test_create_subfolder():
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    folder = Folder(name="folder_name", id="folder_id", parent=workspace)
    subfolder = Folder(name="subfolder_name", id="subfolder_id", parent=folder)
    assert subfolder.parent == folder
    assert subfolder.tenant.id == "0000"
    assert subfolder.tenant.name == "tenant_name.Tenant"
    assert subfolder.workspace.id == "workspace_id"
    assert subfolder.workspace.name == "workspace_name.Workspace"
    assert subfolder.parent.id == "folder_id"
    assert subfolder.parent.name == "folder_name.Folder"
    assert subfolder.id == "subfolder_id"
    assert subfolder.name == "subfolder_name.Folder"
    assert subfolder.type == FabricElementType.FOLDER
    assert (
        subfolder.path
        == "/workspace_name.Workspace/folder_name.Folder/subfolder_name.Folder"
    )
    assert subfolder.check_command_support(Command.FS_LS)
