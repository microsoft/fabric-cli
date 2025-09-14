# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec_command(args: Namespace) -> None:
    utils_mem_store.clear_caches()
    utils_ui.print_output_format(args, message="Cleared the cache")
