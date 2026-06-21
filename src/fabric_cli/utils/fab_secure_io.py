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

# Owner read/write only (rw-------); the permission we enforce on every
# file the CLI manages.
OWNER_ONLY_FILE_MODE = 0o600

# Owner read/write/execute only (rwx------); the permission we enforce on every
# directory the CLI manages.
OWNER_ONLY_DIR_MODE = 0o700


def chmod_if_posix(path: str, mode: int) -> None:
    """Best-effort chmod on POSIX; no-op on Windows.

    Logs at debug level on failure since the user cannot act on it.
    """
    if IS_POSIX:
        try:
            os.chmod(path, mode)
        except OSError as e:
            _logger.debug("Failed to set permissions %o on %s: %s", mode, path, e)


def restrict_existing_file(path: str) -> None:
    """Tighten an already-written file to owner-only access (0o600) on POSIX.

    No-op on Windows or when the file does not exist. Use this for files the
    CLI cannot create through :func:`write_restricted_file` (e.g. the MSAL
    token cache written by ``msal_extensions``).
    """
    if os.path.exists(path):
        chmod_if_posix(path, OWNER_ONLY_FILE_MODE)


def write_restricted_file(file_path: str, content: str) -> None:
    """Write content to a file with owner-only permissions (0o600).

    Permissions are tightened *before* truncation so existing content is never
    exposed through a world-readable file descriptor.
    """
    restrict_existing_file(file_path)
    fd = os.open(file_path, os.O_WRONLY | os.O_CREAT |
                 os.O_TRUNC, OWNER_ONLY_FILE_MODE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception:
        # Close the fd if os.fdopen failed before wrapping it (avoids a leak).
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def get_restricted_file_opener():
    """Return an ``open`` opener that creates files with 0o600 on POSIX, else None."""
    if IS_POSIX:
        return lambda path, flags: os.open(path, flags, OWNER_ONLY_FILE_MODE)
    return None


def create_restricted_dir(dir_path: str) -> None:
    """Create (or tighten) a directory with owner-only permissions (0o700)."""
    os.makedirs(dir_path, mode=OWNER_ONLY_DIR_MODE, exist_ok=True)
    # Enforce permissions on pre-existing directories from older versions
    chmod_if_posix(dir_path, OWNER_ONLY_DIR_MODE)
