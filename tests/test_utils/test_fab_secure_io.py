# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import stat
import tempfile

import pytest

from fabric_cli.utils import fab_secure_io
from fabric_cli.utils.fab_secure_io import (
    OWNER_ONLY_FILE_MODE,
    restrict_existing_file,
    write_restricted_file,
)

# These permission assertions only make sense on POSIX, where chmod bits are
# enforced. On Windows the helpers are intentional no-ops (ACL-based).
posix_only = pytest.mark.skipif(
    not fab_secure_io.IS_POSIX, reason="POSIX permission bits are a no-op on Windows"
)


def _mode(path: str) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


# ---------------------------------------------------------------------------
# restrict_existing_file
# ---------------------------------------------------------------------------


@posix_only
def test_restrict_existing_file_tightens_world_readable_file_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "auth.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("secret")
        os.chmod(path, 0o644)

        restrict_existing_file(path)

        assert _mode(path) == OWNER_ONLY_FILE_MODE


@posix_only
def test_restrict_existing_file_keeps_owner_read_write_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "auth.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("secret")
        os.chmod(path, 0o644)

        restrict_existing_file(path)

        mode = _mode(path)
        # Owner can still read and write (so MSAL can reopen it)...
        assert mode & stat.S_IRUSR
        assert mode & stat.S_IWUSR
        # ...but group and others have no access.
        assert not mode & (stat.S_IRWXG | stat.S_IRWXO)


def test_restrict_existing_file_missing_file_is_noop_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "does-not-exist.json")
        # Should not raise.
        restrict_existing_file(path)
        assert not os.path.exists(path)


# ---------------------------------------------------------------------------
# write_restricted_file
# ---------------------------------------------------------------------------


@posix_only
def test_write_restricted_file_creates_owner_only_file_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        write_restricted_file(path, '{"key": "value"}')

        assert _mode(path) == OWNER_ONLY_FILE_MODE
        with open(path, "r", encoding="utf-8") as handle:
            assert handle.read() == '{"key": "value"}'


@posix_only
def test_write_restricted_file_tightens_preexisting_file_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("old")
        os.chmod(path, 0o644)

        write_restricted_file(path, "new")

        assert _mode(path) == OWNER_ONLY_FILE_MODE
        with open(path, "r", encoding="utf-8") as handle:
            assert handle.read() == "new"
