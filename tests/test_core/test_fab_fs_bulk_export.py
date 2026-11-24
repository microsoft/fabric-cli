# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import os
from argparse import Namespace
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from fabric_cli.commands.fs import fab_fs_bulk_export
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import FabricElement, Tenant, Workspace
from fabric_cli.errors import ErrorMessages
from fabric_cli.errors.bulk_export import BulkExportErrors
from fabric_cli.utils.fab_cmd_bulk_export_utils import (
    export_definition_parts_to_storage,
)


@pytest.fixture
def bulk_export_workspace() -> Workspace:
    return Workspace("ws", "workspace-id", Tenant("tenant", "tenant-id"), "Workspace")


@pytest.fixture
def mock_bulk_exporters() -> Iterator[tuple[MagicMock, MagicMock]]:
    with (
        patch.object(fab_fs_bulk_export, "bulk_export_workspace") as workspace,
        patch.object(fab_fs_bulk_export, "bulk_export_folder") as folder,
    ):
        yield workspace, folder


@pytest.mark.parametrize("target", ["workspace", "folder"])
@pytest.mark.parametrize(
    "output",
    [
        ".",
        "./",
        pytest.param(
            ".\\", marks=pytest.mark.skipif(os.name != "nt", reason="Windows path")
        ),
        "./export output",
        "absolute",
        "~/export",
        "ws.Workspace/lake.Lakehouse/Files",
    ],
)
def test_bulk_export_writes_to_local_directory(
    target: str,
    output: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bulk_export_workspace: Workspace,
    mock_bulk_exporters: tuple[MagicMock, MagicMock],
    mock_print_warning: MagicMock,
) -> None:
    monkeypatch.chdir(tmp_path)
    if output.startswith("~"):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
    if output == "absolute":
        output = str(tmp_path / "absolute")
    output_dir = Path(os.path.expanduser(output))
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = bulk_export_workspace
    context = (
        workspace if target == "workspace" else Folder("folder", "folder-id", workspace)
    )
    args = Namespace(
        output=[output],
        recursive=True,
        force=True,
        from_path=(
            "ws.Workspace" if target == "workspace" else "ws.Workspace/folder.Folder"
        ),
    )
    content = b"print('exported')\n"

    def export(_context: FabricElement, export_args: Namespace) -> None:
        export_definition_parts_to_storage(
            export_args,
            context.full_name,
            {
                "definitionParts": [
                    {
                        "path": "/notebook.Notebook/notebook-content.py",
                        "payload": base64.b64encode(content).decode("ascii"),
                        "payloadType": "InlineBase64",
                    }
                ]
            },
        )

    export_workspace, export_folder = mock_bulk_exporters
    export_workspace.side_effect = export
    export_folder.side_effect = export
    with (
        patch(
            "fabric_cli.utils.fab_storage.handle_context.get_command_context",
            return_value=context,
        ) as fabric_resolver,
        patch("fabric_cli.utils.fab_ui.print_grey"),
    ):
        fab_fs_bulk_export.exec_command(args, context)
        fabric_resolver.assert_not_called()
        (
            export_workspace if target == "workspace" else export_folder
        ).assert_called_once()
        (
            export_folder if target == "workspace" else export_workspace
        ).assert_not_called()

    assert (
        output_dir / "notebook.Notebook/notebook-content.py"
    ).read_bytes() == content


@pytest.mark.parametrize(
    "output", ["missing", "file.txt", "ws.Workspace/lake.Lakehouse/Files"]
)
def test_bulk_export_rejects_invalid_local_destination_before_export(
    output: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bulk_export_workspace: Workspace,
    mock_bulk_exporters: tuple[MagicMock, MagicMock],
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").touch()
    workspace = bulk_export_workspace
    args = Namespace(output=[output], recursive=True, force=True)
    expected_code = (
        fab_constant.ERROR_INVALID_OPERATION
        if output == "file.txt"
        else fab_constant.ERROR_INVALID_PATH
    )
    expected_message = (
        BulkExportErrors.invalid_export_path(output)
        if output == "file.txt"
        else ErrorMessages.Common.no_such_file_or_directory()
    )

    export_workspace, export_folder = mock_bulk_exporters
    with pytest.raises(FabricCLIError) as exc:
        fab_fs_bulk_export.exec_command(args, workspace)

    assert exc.value.status_code == expected_code
    assert expected_message in str(exc.value)
    export_workspace.assert_not_called()
    export_folder.assert_not_called()


@pytest.mark.parametrize(
    "force,answers,confirmed",
    [
        (False, [False], False),
        (False, [True, False], False),
        (False, [True, True], True),
        (True, [], True),
    ],
)
def test_bulk_export_current_directory_preserves_nonempty_confirmation(
    force: bool,
    answers: list[bool],
    confirmed: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mock_questionary_confirm: MagicMock,
    mock_print_warning: MagicMock,
) -> None:
    monkeypatch.chdir(tmp_path)
    existing_file = tmp_path / "existing.txt"
    existing_file.write_text("keep", encoding="utf-8")
    args = Namespace(output=".", force=force)
    mock_questionary_confirm.return_value.ask.side_effect = answers
    assert fab_fs_bulk_export._confirm_export_preconditions(args) is confirmed
    assert mock_questionary_confirm.call_count == len(answers)
    assert mock_questionary_confirm.return_value.ask.call_count == len(answers)
    if force:
        assert mock_print_warning.call_args_list == [
            call("Item definitions are exported without their sensitivity labels"),
            call("Exporting to a non-empty output folder"),
        ]
    else:
        mock_print_warning.assert_not_called()
        assert "not empty" in mock_questionary_confirm.call_args_list[0].args[0]
        if len(answers) == 2:
            assert (
                "sensitivity labels"
                in mock_questionary_confirm.call_args_list[1].args[0]
            )
    assert existing_file.read_text(encoding="utf-8") == "keep"
