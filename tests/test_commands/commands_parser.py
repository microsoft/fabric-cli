# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import platform
from prompt_toolkit import PromptSession
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.history import InMemoryHistory

from fabric_cli.core.fab_interactive import InteractiveCLI
from fabric_cli.main import CustomArgumentParser
from fabric_cli.parsers.fab_acls_parser import register_parser as register_acls_parser
from fabric_cli.parsers.fab_api_parser import register_parser as register_api_parser
from fabric_cli.parsers.fab_config_parser import (
    register_parser as register_config_parser,
)
from fabric_cli.parsers.fab_fs_parser import (
    register_assign_parser,
    register_cd_parser,
    register_cp_parser,
    register_exists_parser,
    register_export_parser,
    register_get_parser,
    register_import_parser,
    register_ln_parser,
    register_ls_parser,
    register_mkdir_parser,
    register_mv_parser,
    register_open_parser,
    register_rm_parser,
    register_set_parser,
    register_start_parser,
    register_stop_parser,
    register_unassign_parser,
)
from fabric_cli.parsers.fab_jobs_parser import register_parser as register_jobs_parser
from fabric_cli.parsers.fab_labels_parser import (
    register_parser as register_labels_parser,
)

parserHandlers = [
    register_labels_parser,
    register_config_parser,
    register_cd_parser,
    register_cp_parser,
    register_exists_parser,
    register_acls_parser,
    register_export_parser,
    register_import_parser,
    register_assign_parser,
    register_ln_parser,
    register_ls_parser,
    register_mv_parser,
    register_unassign_parser,
    register_api_parser,
    register_get_parser,
    register_stop_parser,
    register_start_parser,
    register_set_parser,
    register_open_parser,
    register_rm_parser,
    register_mkdir_parser,
    register_jobs_parser,
]


class TestInteractiveCLI(InteractiveCLI):
    def init_session(self, session_history: InMemoryHistory) -> PromptSession:
        if platform.system() == "Windows":
            # DummyInput and DummyOutput are test classes of prompt_toolkit to
            # solve the NoConsoleScreenBufferError issue
            return PromptSession(
                history=session_history, input=DummyInput(), output=DummyOutput()
            )

        return super().init_session(session_history)


class CLIExecutor:
    def __init__(self):
        customArgumentParser = CustomArgumentParser()
        self._parser = customArgumentParser.add_subparsers()
        for register_parser_handler in parserHandlers:
            register_parser_handler(self._parser)
        self._interactiveCLI = TestInteractiveCLI(customArgumentParser, self._parser)

    def exec_command(self, command: str) -> None:
        self._interactiveCLI.handle_command(command)
