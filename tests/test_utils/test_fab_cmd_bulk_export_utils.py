# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from fabric_cli.utils.fab_cmd_bulk_export_utils import (
    create_bulk_export_payload,
    export_definition_parts_to_storage,
    print_bulk_export_summary,
)


class TestCreateBulkExportPayload:
    def test_empty_list_returns_all_mode(self):
        result = json.loads(create_bulk_export_payload([]))
        assert result == {"items": [], "mode": "All"}

    def test_single_item_id(self):
        result = json.loads(create_bulk_export_payload(["id-1"]))
        assert result == {
            "items": [{"id": "id-1"}],
            "mode": "Selective",
        }

    def test_multiple_item_ids(self):
        ids = ["id-1", "id-2", "id-3"]
        result = json.loads(create_bulk_export_payload(ids))
        assert result["mode"] == "Selective"
        assert len(result["items"]) == 3
        assert result["items"] == [{"id": "id-1"}, {"id": "id-2"}, {"id": "id-3"}]

    def test_returns_valid_json_string(self):
        payload = create_bulk_export_payload(["abc"])
        assert isinstance(payload, str)
        parsed = json.loads(payload)
        assert "items" in parsed
        assert "mode" in parsed

    def test_preserves_item_id_values(self):
        guid = "00000000-0000-0000-0000-000000000000"
        result = json.loads(create_bulk_export_payload([guid]))
        assert result["items"][0]["id"] == guid


def _make_mock_item(item_type_str: str) -> Mock:
    item = Mock()
    item.item_type = item_type_str
    return item


class TestPrintBulkExportSummary:
    @pytest.fixture
    def base_args(self):
        return Namespace(output="/tmp/export")

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_output_format")
    def test_all_supported_no_unsupported(self, mock_print, base_args):
        items_support = {
            "supported_items": [
                _make_mock_item("Notebook"),
                _make_mock_item("Notebook"),
            ],
            "unsupported_items": [],
        }

        print_bulk_export_summary(base_args, items_support)

        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args
        assert call_kwargs.kwargs["args"] is base_args
        data = call_kwargs.kwargs["data"][0]
        assert data["exported"] == 2
        assert data["skipped"] == 0
        assert data["output"] == "/tmp/export"
        assert "Skipped" not in call_kwargs.kwargs["message"]

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_output_format")
    def test_with_unsupported_items_includes_skip_message(self, mock_print, base_args):
        items_support = {
            "supported_items": [_make_mock_item("Notebook")],
            "unsupported_items": [
                _make_mock_item("Dashboard"),
                _make_mock_item("Dashboard"),
                _make_mock_item("KQLDatabase"),
            ],
        }

        print_bulk_export_summary(base_args, items_support)

        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args
        message = call_kwargs.kwargs["message"]
        assert "Skipped 3 items" in message
        assert "Dashboard (2)" in message
        assert "KQLDatabase (1)" in message
        data = call_kwargs.kwargs["data"][0]
        assert data["exported"] == 1
        assert data["skipped"] == 3

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_output_format")
    def test_empty_supported_and_unsupported(self, mock_print, base_args):
        items_support = {
            "supported_items": [],
            "unsupported_items": [],
        }

        print_bulk_export_summary(base_args, items_support)

        mock_print.assert_called_once()
        data = mock_print.call_args.kwargs["data"][0]
        assert data["exported"] == 0
        assert data["skipped"] == 0

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_output_format")
    def test_exported_types_grouped_correctly(self, mock_print, base_args):
        items_support = {
            "supported_items": [
                _make_mock_item("Notebook"),
                _make_mock_item("Report"),
                _make_mock_item("Notebook"),
            ],
            "unsupported_items": [],
        }

        print_bulk_export_summary(base_args, items_support)

        data = mock_print.call_args.kwargs["data"][0]
        assert data["exported_types"] == {"Notebook": 2, "Report": 1}
        assert data["skipped_types"] == {}

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_output_format")
    def test_message_includes_output_path(self, mock_print, base_args):
        items_support = {
            "supported_items": [_make_mock_item("Notebook")],
            "unsupported_items": [],
        }

        print_bulk_export_summary(base_args, items_support)

        message = mock_print.call_args.kwargs["message"]
        assert "Exported 1 items to '/tmp/export'" in message


class TestExportDefinitionPartsToStorage:
    @pytest.fixture
    def base_args(self, tmp_path):
        output_dir = str(tmp_path / "export_output")
        return Namespace(output=output_dir, from_path="myws.Workspace")

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.utils_export.export_json_parts")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_storage.get_export_path")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.utils_export.decode_payload")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_grey")
    def test_workspace_export_no_parent_folders(
        self, mock_print, mock_decode, mock_get_path, mock_export, base_args, tmp_path
    ):
        export_path = str(tmp_path / "export_output")
        mock_get_path.return_value = {"type": "local", "path": export_path}
        mock_decode.return_value = {
            "definitionParts": [
                {"path": "/n1.Notebook/notebook-content.py", "payload": "content"}
            ]
        }
        response = {
            "definitionParts": [
                {"path": "/n1.Notebook/notebook-content.py", "payload": "encoded"}
            ]
        }

        export_definition_parts_to_storage(base_args, "ws1.Workspace", response)

        mock_decode.assert_called_once_with(response)
        mock_get_path.assert_called_once_with(base_args.output)
        mock_export.assert_called_once_with(
            base_args,
            mock_decode.return_value,
            {"type": "local", "path": export_path},
            definition_parts="definitionParts",
        )

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.utils_export.export_json_parts")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_storage.get_export_path")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.utils_export.decode_payload")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_grey")
    def test_nested_folder_strips_parent_prefix(
        self, mock_print, mock_decode, mock_get_path, mock_export, tmp_path
    ):
        args = Namespace(
            output=str(tmp_path / "out"),
            from_path="myws.Workspace/f1.Folder/f2.Folder",
        )
        export_path = str(tmp_path / "out")
        mock_get_path.return_value = {"type": "local", "path": export_path}
        mock_decode.return_value = {
            "definitionParts": [
                {
                    "path": "/f1/f2/n1.Notebook/notebook-content.py",
                    "payload": "data",
                },
                {"path": "/f1/f2/n1.Notebook/.platform", "payload": "{}"},
            ]
        }
        response = {
            "definitionParts": [
                {
                    "path": "/f1/f2/n1.Notebook/notebook-content.py",
                    "payload": "enc1",
                },
                {
                    "path": "/f1/f2/n1.Notebook/.platform",
                    "payload": "enc2",
                },
            ]
        }

        export_definition_parts_to_storage(args, "f2.Folder", response)

        # After stripping, paths should have the /f1 prefix removed
        exported_def = mock_export.call_args.args[1]
        for part in exported_def["definitionParts"]:
            assert not part["path"].startswith("/f1/")
            assert part["path"].startswith("/f2/")

    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.utils_export.export_json_parts")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_storage.get_export_path")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.utils_export.decode_payload")
    @patch("fabric_cli.utils.fab_cmd_bulk_export_utils.fab_ui.print_grey")
    def test_deeply_nested_folders_strips_all_parent_segments(
        self, mock_print, mock_decode, mock_get_path, mock_export, tmp_path
    ):
        args = Namespace(
            output=str(tmp_path / "out"),
            from_path="myws.Workspace/f1.Folder/f2.Folder/f3.Folder",
        )
        export_path = str(tmp_path / "out")
        mock_get_path.return_value = {"type": "local", "path": export_path}
        mock_decode.return_value = {
            "definitionParts": [
                {
                    "path": "/f1/f2/f3/n1.Notebook/content.json",
                    "payload": "{}",
                },
            ]
        }
        response = {
            "definitionParts": [
                {
                    "path": "/f1/f2/f3/n1.Notebook/content.json",
                    "payload": "enc",
                },
            ]
        }

        export_definition_parts_to_storage(args, "f3.Folder", response)

        exported_def = mock_export.call_args.args[1]
        assert (
            exported_def["definitionParts"][0]["path"] == "/f3/n1.Notebook/content.json"
        )
