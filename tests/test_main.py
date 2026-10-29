# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import site
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from fabric_cli.core import fab_constant


class TestMainModule:
    """Test suite for main module functionality."""

    def test_main_no_args_starts_interactive_mode_success(self):
        """Test that running 'fab' without arguments automatically enters interactive mode."""
        with patch(
            "fabric_cli.core.fab_interactive.start_interactive_mode"
        ) as mock_start_interactive:
            from fabric_cli.main import main

            with patch.object(sys, "argv", ["fab"]):
                with patch(
                    "fabric_cli.core.fab_parser_setup.get_global_parser_and_subparsers"
                ) as mock_get_parsers:
                    mock_parser = type(
                        "MockParser",
                        (),
                        {
                            "parse_args": lambda self: type(
                                "Args", (), {"command": None, "version": False}
                            )(),
                            "set_mode": lambda self, mode: None,
                        },
                    )()
                    mock_subparsers = object()
                    mock_get_parsers.return_value = (mock_parser, mock_subparsers)

                    with patch("fabric_cli.core.fab_state_config.init_defaults"):
                        main()

                    mock_start_interactive.assert_called_once()

    def test_start_interactive_mode_directly_success(self):
        """Test that start_interactive_mode can be called directly without infinite loops."""
        # Mock the InteractiveCLI to prevent actual interactive session
        with patch(
            "fabric_cli.core.fab_interactive.InteractiveCLI"
        ) as mock_interactive_cli:
            from unittest.mock import Mock

            mock_cli_instance = Mock()
            mock_cli_instance._is_running = False
            mock_cli_instance.start_interactive = (
                Mock()
            )  # Mock the start_interactive method
            mock_interactive_cli.return_value = mock_cli_instance

            from fabric_cli.core.fab_interactive import start_interactive_mode

            start_interactive_mode()

            mock_interactive_cli.assert_called_once()
            mock_cli_instance.start_interactive.assert_called_once()

    @pytest.mark.parametrize(
        "tokens",
        [
            ["job", "run", "--help", "--output_format=json"],
            ["--version"],
            ["version"],
        ],
    )
    def test_help_version_no_execution_dependencies_success(
        self,
        tokens: list[str],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from fabric_cli import main as main_module

        monkeypatch.setattr(sys, "argv", ["fab", *tokens])
        with (
            patch("argcomplete.autocomplete") as completion,
            patch("fabric_cli.core.fab_state_config.init_defaults") as init_config,
            patch("fabric_cli.core.fab_logger.print_log_file_path") as log,
            patch.object(main_module, "_execute_command") as execute,
            patch.object(
                socket.socket, "connect", side_effect=AssertionError("network")
            ),
        ):
            if "--help" in tokens:
                with pytest.raises(SystemExit) as exit_info:
                    main_module.main()
                assert exit_info.value.code == 0
            else:
                main_module.main()
            completion.assert_not_called()
            init_config.assert_not_called()
            log.assert_not_called()
            execute.assert_not_called()
        assert capsys.readouterr().err == ""


def _run_help(home: Path, tokens: list[str]) -> subprocess.CompletedProcess[str]:
    executable = os.environ.get("FAB_HELP_EXECUTABLE")
    command = (
        [executable]
        if executable
        else [sys.executable, "-B", "-c", "from fabric_cli.main import main; main()"]
    )
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("FAB_", "AZURE_", "_ARGCOMPLETE"))
    }
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "APPDATA": str(home),
            "LOCALAPPDATA": str(home),
            "XDG_CONFIG_HOME": str(home),
            "XDG_STATE_HOME": str(home),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUSERBASE": site.getuserbase(),
            "_ARGCOMPLETE": "1",
            "COMP_LINE": "fab --help",
            "COMP_POINT": "10",
        }
    )
    if executable:
        env.pop("PYTHONPATH", None)
    else:
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run(
        [*command, *tokens],
        cwd=home,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )


@pytest.mark.parametrize(
    ("tokens", "command"),
    [
        (["--help", "--output_format", "json"], "fab"),
        (["job", "-h", "--output_format=json"], "job"),
        (["job", "run", "--help", "--output_format", "json"], "job run"),
        (["--output_format", "json", "create", "-help"], "mkdir"),
        (["--output_format=json", "job", "run", "-h"], "job run"),
        (["import", "--help", "--output_format=json"], "import"),
        (["job", "run", "--timeout", "bad", "-h", "--output_format=json"], "job run"),
    ],
)
def test_offline_json_help_success(
    tmp_path: Path,
    tokens: list[str],
    command: str,
) -> None:
    result = _run_help(tmp_path, tokens)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload) == {"timestamp", "status", "command", "result"}
    assert payload["status"] == "Success"
    assert payload["command"] == command
    assert set(payload["result"]) == {"data"}
    assert len(payload["result"]["data"]) == 1
    assert result.stdout.endswith("\n") and not result.stdout.endswith("\n\n")
    assert "\x1b" not in result.stdout
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("config_kind", ["corrupt", "blocked", "missing", "readonly"])
def test_help_with_unusable_config_success(
    tmp_path: Path,
    config_kind: str,
) -> None:
    config = tmp_path / ".config"
    if config_kind == "blocked":
        config.write_text("not a directory", encoding="utf-8")
    elif config_kind in ("corrupt", "readonly"):
        directory = config / "fab"
        directory.mkdir(parents=True)
        (directory / "config.json").write_text(
            "{" if config_kind == "corrupt" else '{"output_format": "json"}',
            encoding="utf-8",
        )
        if config_kind == "readonly":
            directory.chmod(0o500)
    try:
        before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
        result = _run_help(tmp_path, ["mkdir", "-h", "--output_format=json"])
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["status"] == "Success"
        assert payload["command"] == "mkdir"
        assert len(payload["result"]["data"]) == 1
        assert result.stderr == ""
        assert (
            sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
            == before
        )
        result = _run_help(tmp_path, ["--version"])
        assert result.returncode == 0, result.stderr
        assert result.stdout.startswith("fab version ")
    finally:
        if config_kind == "readonly":
            (config / "fab").chmod(0o700)


@pytest.mark.parametrize(
    ("tokens", "command"),
    [
        (["unknown", "--help", "--output_format=json"], "fab"),
        (["job", "unknown", "-h", "--output_format=json"], "job"),
        (["mkdir", "--unknown=secret-value", "-h", "--output_format=json"], "mkdir"),
        (["mkdir", "-h", "--output_format=json", "--output_format=text"], "mkdir"),
        (["mkdir", "--output_format=json", "-h", "--output_format"], "mkdir"),
        (
            ["mkdir", "--output_format=json", "-h", "--output_format=invalid-secret"],
            "mkdir",
        ),
    ],
)
def test_invalid_json_help_failure(
    tmp_path: Path,
    tokens: list[str],
    command: str,
) -> None:
    result = _run_help(tmp_path, tokens)
    assert result.returncode == 2, result.stderr
    payload: dict[str, Any] = json.loads(result.stdout)
    assert set(payload) == {"timestamp", "status", "command", "result"}
    assert payload["status"] == "Failure"
    assert payload["command"] == command
    assert set(payload["result"]) == {"error_code", "message"}
    assert payload["result"]["error_code"] == fab_constant.ERROR_INVALID_INPUT
    assert payload["result"]["message"]
    assert "secret" not in result.stdout + result.stderr
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []
