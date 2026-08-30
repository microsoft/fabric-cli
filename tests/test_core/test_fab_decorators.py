# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

import pytest

from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_decorators import set_command_context

pytestmark = pytest.mark.usefixtures("reset_context")


def test_set_command_context_uses_skill_argument():
    @set_command_context()
    def command(args: Namespace) -> None:
        assert Context().fabric_skill == "argument-skill"

    command(Namespace(command_path="export", skill="argument-skill"))


def test_set_command_context_clears_previous_skill():
    Context().fabric_skill = "previous-skill"

    @set_command_context()
    def command(args: Namespace) -> None:
        assert Context().fabric_skill is None

    command(Namespace(command_path="export", skill=None))


def test_set_command_context_ignores_empty_argument():
    @set_command_context()
    def command(args: Namespace) -> None:
        assert Context().fabric_skill is None

    command(Namespace(command_path="export", skill=""))
