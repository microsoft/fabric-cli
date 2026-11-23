# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
from argparse import Namespace
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

import fabric_cli.utils.fab_item_util as item_utils
from fabric_cli.client import fab_api_item as item_api
from fabric_cli.commands.fs.export import fab_fs_export_item as _export_item
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType, OneLakeItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item, OneLakeItem, Tenant, Workspace
from fabric_cli.utils.fab_cmd_import_utils import get_payload_for_item_type


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
        name="dashboard_name",
        id="dashboard_id",
        parent=workspace,
        item_type="Dashboard",
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


@pytest.mark.parametrize("export_format", [None, "DeploymentPlanFormat"])
def test_deployment_plan_export_import_success(
    tmp_path: Path, export_format: str | None
) -> None:
    tenant = Tenant(name="tenant_name", id="tenant_id")
    workspace = Workspace(
        name="workspace_name", id="workspace_id", parent=tenant, type="Workspace"
    )
    item = Item(
        name="deployment",
        id="item_id",
        parent=workspace,
        item_type="DeploymentPlan",
    )
    content = "version: '1.0'\ngroups: []\n"
    definition = {
        "parts": [
            {
                "path": "plan.yml",
                "payload": base64.b64encode(content.encode()).decode(),
                "payloadType": "InlineBase64",
            }
        ]
    }
    args = Namespace(force=True, format=export_format, output=str(tmp_path))

    for command in [Command.FS_EXPORT, Command.FS_IMPORT, Command.FS_CP, Command.FS_MV]:
        assert item.check_command_support(command)

    with (
        patch.object(
            item_api,
            "get_item_withdefinition",
            return_value={"definition": deepcopy(definition)},
        ) as get_definition,
        patch.object(
            _export_item.fab_storage,
            "get_export_path",
            return_value={"type": "local", "path": str(tmp_path)},
        ),
    ):
        _export_item.export_single_item(item, args)

    definition_args = get_definition.call_args.args[0]
    with patch.object(item_api.fabric_api, "do_request") as request:
        item_api.get_item_definition(definition_args)
    expected_uri = "workspaces/workspace_id/items/item_id/getDefinition"
    if export_format:
        expected_uri += "?format=DeploymentPlanFormat"
    assert request.call_args.args[0].uri == expected_uri

    export_path = tmp_path / item.name
    assert (export_path / "plan.yml").read_text() == content
    payload = get_payload_for_item_type(str(export_path), item, export_format)
    assert payload["type"] == "DeploymentPlan"
    parts = payload["definition"]["parts"]
    assert len(parts) == 1
    assert parts[0]["path"] == "plan.yml"
    assert parts[0]["payloadType"] == "InlineBase64"
    assert (
        base64.b64decode(parts[0]["payload"]).decode().splitlines()
        == content.splitlines()
    )
    if export_format:
        assert payload["definition"]["format"] == "DeploymentPlanFormat"
    else:
        assert "format" not in payload["definition"]


def test_deployment_plan_invalid_definition_format_failure() -> None:
    with pytest.raises(FabricCLIError) as error:
        item_utils.resolve_definition_format(ItemType.DEPLOYMENT_PLAN, ".txt")

    assert error.value.status_code == fab_constant.ERROR_INVALID_INPUT
    assert "DeploymentPlanFormat" in str(error.value)
