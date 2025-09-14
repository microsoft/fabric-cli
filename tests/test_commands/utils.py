# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from pathlib import PurePosixPath
from typing import Literal

VCR_MODE_ENV_VAR = "FABRIC_CLI_TEST_VCR_MODE"


def cli_path_join(*args) -> str:
    """
    Fabric CLI uses POSIX path. This util build the Fabric CLI path from list of path parts
    Args:
        args: The path parts.
    Returns:
        str: The POSIX path string.
    """
    return PurePosixPath(*args).as_posix()


def get_vcr_mode_env() -> Literal["record", "playback"]:
    """
    Get the VCR mode environment variable.
    Returns:
        Literal["record", "playback"]: The VCR mode, either "record" or "playback".
    """
    return "record" if os.getenv(VCR_MODE_ENV_VAR, None) == "record" else "playback"


def set_vcr_mode_env(vcr_mode: str) -> None:
    """
    Set the VCR mode environment variable.
    Args:
        vcr_mode (str): The VCR mode input, "all" or "none.
    """
    mode = "record" if vcr_mode == "all" else "playback"
    os.environ[VCR_MODE_ENV_VAR] = mode


def is_record_mode() -> bool:
    """
    Check if the VCR mode is in record mode.
    Returns:
        bool: True if the VCR mode is in record mode, False otherwise.
    """
    return get_vcr_mode_env() == "record"
