# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Shared helpers for enforcing restrictive file and directory permissions.

On POSIX systems (Linux/macOS), these helpers ensure that sensitive files are
created with owner-only access (0o600 for files, 0o700 for directories) and
tighten permissions on pre-existing paths from older CLI versions.

On Windows, POSIX permission bits are a no-op — Windows uses ACLs instead,
and default user-profile ACLs already restrict access to the owner.
"""

import logging
import os

_logger = logging.getLogger(__name__)

# True on Linux/macOS; False on Windows where POSIX permission bits are a no-op.
IS_POSIX = os.name != "nt"


def chmod_if_posix(path: str, mode: int) -> None:
    """Best-effort chmod on POSIX; no-op on Windows.

    Logs at debug level when chmod fails (e.g. permission denied on
    restrictive filesystems) since the user cannot act on it.
    """
    if IS_POSIX:
        try:
            os.chmod(path, mode)
        except OSError as e:
            _logger.debug("Failed to set permissions %o on %s: %s", mode, path, e)


def write_restricted_file(file_path: str, content: str) -> None:
    """Write content to a file with owner-only permissions (0o600).

    Handles both new file creation and tightening permissions on
    pre-existing files from older CLI versions.  Permissions are
    tightened *before* truncation so that sensitive content is never
    written to a world-readable file descriptor.
    """
    # Tighten permissions on pre-existing files before writing, so
    # the truncate+write never exposes new content through a permissive fd.
    if os.path.exists(file_path):
        chmod_if_posix(file_path, 0o600)
    fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception:
        # os.fdopen may fail before wrapping fd; close to avoid leak.
        # If os.fdopen succeeded, fd is already closed by the with block.
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def get_restricted_file_opener():
    """Return a file opener that creates files with 0o600 on POSIX, or None on Windows.

    Intended for use as the ``opener`` argument to :func:`open`.  Returns
    ``None`` on Windows so that the default opener is used.
    """
    if IS_POSIX:
        return lambda path, flags: os.open(path, flags, 0o600)
    return None


def create_restricted_dir(dir_path: str) -> None:
    """Create a directory with owner-only permissions (0o700).

    Uses exist_ok=True to avoid TOCTOU races and tightens permissions
    on pre-existing directories from older CLI versions.
    """
    os.makedirs(dir_path, mode=0o700, exist_ok=True)
    # Enforce permissions on pre-existing directories from older versions
    chmod_if_posix(dir_path, 0o700)
