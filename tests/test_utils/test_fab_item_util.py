# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

import pytest

import fabric_cli.utils.fab_item_util as item_utils
from fabric_cli.client import fab_api_item as item_api
from fabric_cli.commands.fs.export import fab_fs_export_item as _export_item
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_types import OneLakeItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item, OneLakeItem, Tenant, Workspace


def test_extract_paths():
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
    root_folder = OneLakeItem(
        "Files", "0000", parent=item, nested_type=OneLakeItemType.FOLDER
    )
    lvl1_folder = OneLakeItem(
        "path", "0000", parent=root_folder, nested_type=OneLakeItemType.FOLDER
    )
    lvl2_folder = OneLakeItem(
        "to", "0000", parent=lvl1_folder, nested_type=OneLakeItemType.FOLDER
    )
    lvl3_folder = OneLakeItem(
        "item", "0000", parent=lvl2_folder, nested_type=OneLakeItemType.FILE
    )
    path_id, path_name = item_utils.extract_paths(lvl3_folder)
    assert path_id == "workspace_id/item_id/Files/path/to/item"
    assert (
        path_name == "workspace_name.Workspace/item_name.Lakehouse/Files/path/to/item"
    )


def test_obtain_id_names_for_onelake():
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
    root_folder = OneLakeItem(
        "Files", "0000", parent=item, nested_type=OneLakeItemType.FOLDER
    )
    lvl1_folder = OneLakeItem(
        "path", "0000", parent=root_folder, nested_type=OneLakeItemType.FOLDER
    )
    lvl2_folder = OneLakeItem(
        "to", "0000", parent=lvl1_folder, nested_type=OneLakeItemType.FOLDER
    )
    from_item = OneLakeItem(
        "item_from", "0000", parent=lvl2_folder, nested_type=OneLakeItemType.FILE
    )
    to_item = OneLakeItem(
        "item_to", "0000", parent=lvl2_folder, nested_type=OneLakeItemType.FILE
    )
    from_path_id, from_path_name, to_path_id, to_path_name = (
        item_utils.obtain_id_names_for_onelake(from_item, to_item)
    )
    assert from_path_id == "workspace_id/item_id/Files/path/to/item_from"
    assert (
        from_path_name
        == "workspace_name.Workspace/item_name.Lakehouse/Files/path/to/item_from"
    )
    assert to_path_id == "workspace_id/item_id/Files/path/to/item_to"
    assert (
        to_path_name
        == "workspace_name.Workspace/item_name.Lakehouse/Files/path/to/item_to"
    )


def test_get_item_with_definition(monkeypatch):
    tenant = Tenant(name="tenant_name", id="0000")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    non_export_item = Item(
        name="lh_name",
        id="lh_id",
        parent=workspace,
        item_type="Lakehouse",
    )

    export_item = Item(
        name="nt_name",
        id="ntid",
        parent=workspace,
        item_type="Notebook",
    )

    def mock_export_item(*args, **kwargs):
        return {"item_exported": "item"}

    monkeypatch.setattr(_export_item, "export_single_item", mock_export_item)

    def mock_get_item(*args, **kwargs):
        args = Namespace()
        args.text = json.dumps({"item_non_exported": "item"})
        return args

    monkeypatch.setattr(item_api, "get_item", mock_get_item)

    _args = Namespace()
    item = item_utils.get_item_with_definition(non_export_item, _args)
    assert item == {"item_non_exported": "item"}

    item = item_utils.get_item_with_definition(export_item, _args)
    assert item == {"item_exported": "item"}