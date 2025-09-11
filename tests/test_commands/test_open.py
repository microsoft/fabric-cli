# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
from unittest.mock import patch

import pytest

import fabric_cli.commands.fs.fab_fs_get as fab_get
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, uri_mapping


class TestOpen:

    mocked_upn = "my.upn@example.com"
    mocked_ctid = "my.tid"
    # region Workspace

    @pytest.mark.token_claims({"upn": mocked_upn, "tid": mocked_ctid})
    def test_open_workspace_success(
        self, workspace, cli_executor, mock_webbrowser_open_new, mock_questionary_print
    ):
        # Setup
        get(workspace.full_path, query="id")
        workspace_id = mock_questionary_print.call_args[0][0]

        # Execute command
        cli_executor.exec_command(f"open {workspace.full_path}")

        # Assert
        mock_webbrowser_open_new.assert_called_once_with(
            f"{constant.WEB_URI}/{workspace_id}/list?experience={constant.FAB_DEFAULT_OPEN_EXPERIENCE_FABRIC}&upn={self.mocked_upn}&ctid={self.mocked_ctid}"
        )

    @pytest.mark.token_claims({"upn": mocked_upn, "email": "mocked_email"})
    def test_open_workspace_without_query_param_rename_success(
        self, workspace, cli_executor, mock_webbrowser_open_new, mock_questionary_print
    ):
        # Setup
        get(workspace.full_path, query="id")
        workspace_id = mock_questionary_print.call_args[0][0]

        # Execute command
        cli_executor.exec_command(f"open {workspace.full_path}")

        # Assert
        mock_webbrowser_open_new.assert_called_once_with(
            f"{constant.WEB_URI}/{workspace_id}/list?experience={constant.FAB_DEFAULT_OPEN_EXPERIENCE_FABRIC}&upn={self.mocked_upn}&email=mocked_email"
        )

    @pytest.mark.token_claims({})
    def test_open_workspace_when_claims_none_success(
        self, workspace, cli_executor, mock_webbrowser_open_new, mock_questionary_print
    ):
        # Setup
        get(workspace.full_path, query="id")
        workspace_id = mock_questionary_print.call_args[0][0]

        # Execute command
        cli_executor.exec_command(f"open {workspace.full_path}")

        # Assert
        mock_webbrowser_open_new.assert_called_once_with(
            f"{constant.WEB_URI}/{workspace_id}/list?experience={constant.FAB_DEFAULT_OPEN_EXPERIENCE_FABRIC}"
        )

    # endregion

    # region Item
    @pytest.mark.token_claims({"upn": mocked_upn, "tid": mocked_ctid})
    def test_open_notebook_success(
        self,
        item_factory,
        cli_executor,
        mock_webbrowser_open_new,
        mock_questionary_print,
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        get(notebook.full_path, query=".")
        data = json.loads(mock_questionary_print.call_args[0][0])
        item_id = data["id"]
        workspace_id = data["workspaceId"]

        # Execute command
        cli_executor.exec_command(f"open {notebook.full_path}")

        # Assert
        mock_webbrowser_open_new.assert_called_once_with(
            f"{constant.WEB_URI}/{workspace_id}/{uri_mapping.get(ItemType.NOTEBOOK)}/{item_id}/?experience={constant.FAB_DEFAULT_OPEN_EXPERIENCE_FABRIC}&upn={self.mocked_upn}&ctid={self.mocked_ctid}"
        )

    # endregion


@pytest.fixture(autouse=True, scope="class")
def mock_fab_auth_for_class(vcr_mode):
    """Open command only supported with user authentication"""
    from fabric_cli.core.fab_auth import FabAuth

    if vcr_mode == "none":
        fab_auth_instance = FabAuth()  # Singleton
        with patch.object(
            fab_auth_instance, "_get_auth_property", return_value="user"
        ) as mock:
            yield mock
    else:
        yield


# region Helper Methods


def get(path, output=None, query=None, deep_traversal=False):
    args = _build_get_args(path, output, query, deep_traversal)
    context = handle_context.get_command_context(args.path)
    fab_get.exec_command(args, context)


def _build_get_args(path, output=None, query=None, deep_traversal=False):
    return argparse.Namespace(
        command="get",
        acl_subcommand="get",
        command_path="get",
        path=path,
        output=output,
        query=[query] if query else None,
        deep_traversal=deep_traversal,
        force=True,
    )


@pytest.fixture()
def mock_webbrowser_open_new():
    with patch("webbrowser.open_new") as mock:
        yield mock


# endregion
