# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from argparse import Namespace
from unittest.mock import patch

import pytest

from fabric_cli.client.fab_api_client import do_request
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core import fab_logger as logger
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_decorators import set_command_context
from fabric_cli.core.fab_parser_setup import create_parser_and_subparsers
from fabric_cli.parsers import fab_global_params

pytestmark = pytest.mark.usefixtures("reset_context")


class DummyResponse:
    status_code = 200
    text = "{}"
    content = b"{}"
    headers: dict[str, str] = {}


def test_skill_argument_is_hidden():
    parser = argparse.ArgumentParser()
    fab_global_params.add_global_flags(parser)

    skill_flag = next(
        action for action in parser._actions if "--skill" in action.option_strings
    )

    assert skill_flag.help == argparse.SUPPRESS
    assert "--skill" not in parser.format_help()


@pytest.mark.parametrize(
    "command",
    [
        ["--skill", "semantic-model-authoring", "export", "ws.Workspace", "-o", "out"],
        ["export", "--skill", "semantic-model-authoring", "ws.Workspace", "-o", "out"],
        ["export", "ws.Workspace", "-o", "out", "--skill", "semantic-model-authoring"],
        ["--skill", "semantic-model-authoring", "job", "run", "ws.Notebook"],
        ["job", "run", "ws.Notebook", "--skill", "semantic-model-authoring"],
    ],
)
def test_skill_argument_is_preserved_across_command_tree(command):
    parser, _ = create_parser_and_subparsers()

    args = parser.parse_args(command)

    assert args.skill == "semantic-model-authoring"


def test_command_context_uses_skill_argument():
    @set_command_context()
    def command(args: Namespace) -> None:
        assert Context().fabric_skill == "argument-skill"

    command(Namespace(command_path="export", skill="argument-skill"))


def test_command_context_clears_previous_skill():
    Context().fabric_skill = "previous-skill"

    @set_command_context()
    def command(args: Namespace) -> None:
        assert Context().fabric_skill is None

    command(Namespace(command_path="export", skill=None))


@pytest.mark.parametrize(
    "skill_name",
    ["", "-invalid", "invalid skill", "invalid\nheader", "a" * 129],
)
def test_invalid_skill_name_is_ignored(skill_name):
    Context().fabric_skill = skill_name

    assert Context().fabric_skill is None


@patch.object(FabAuth(), "get_access_token", return_value="dummy-token")
@pytest.mark.parametrize(
    "audience, expects_skill_header",
    [
        (None, True),
        ("fabric", True),
        ("storage", False),
        ("azure", False),
        ("powerbi", False),
    ],
)
def test_skill_header_is_scoped_to_fabric_api(
    mock_get_token, audience, expects_skill_header
):
    Context().fabric_skill = "semantic-model-authoring"
    args = Namespace(uri="items", method="get", audience=audience)

    with patch(
        "requests.Session.request", return_value=DummyResponse()
    ) as mock_request:
        do_request(args)

    request_headers = mock_request.call_args.kwargs["headers"]
    if expects_skill_header:
        assert (
            request_headers[fab_constant.FABRIC_SKILL_HEADER]
            == "semantic-model-authoring"
        )
    else:
        assert fab_constant.FABRIC_SKILL_HEADER not in request_headers


@patch.object(FabAuth(), "get_access_token", return_value="dummy-token")
def test_skill_argument_overrides_custom_header(mock_get_token):
    Context().fabric_skill = "semantic-model-authoring"
    args = Namespace(
        uri="items",
        method="get",
        audience=None,
        headers={"X-MS-FABRIC-SKILL": "other-skill"},
    )

    with patch(
        "requests.Session.request", return_value=DummyResponse()
    ) as mock_request:
        do_request(args)

    request_headers = mock_request.call_args.kwargs["headers"]
    assert (
        request_headers[fab_constant.FABRIC_SKILL_HEADER] == "semantic-model-authoring"
    )
    assert "X-MS-FABRIC-SKILL" not in request_headers


def test_skill_header_is_not_logged(monkeypatch):
    monkeypatch.setattr(fab_state_config, "get_config", lambda key: "true")

    with patch.object(logger, "get_logger") as mock_get_logger:
        logger.log_debug_http_request(
            "GET",
            "http://example.com",
            {fab_constant.FABRIC_SKILL_HEADER: "semantic-model-authoring"},
            10,
        )

    logged_messages = [
        call.args[0] for call in mock_get_logger.return_value.debug.call_args_list
    ]
    assert not any("semantic-model-authoring" in message for message in logged_messages)
