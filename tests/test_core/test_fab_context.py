# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os

import fabric_cli.core.fab_auth as auth
from fabric_cli.core.fab_context import Context
from fabric_cli.core.hiearchy import fab_hiearchy as hierarchy


def test_context_tenant(monkeypatch):
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")

    def mock_get_tenant():
        return _tenant

    monkeypatch.setattr(auth.FabAuth(), "get_tenant", mock_get_tenant)

    Context().context = _tenant
    ctxt = Context()
    # Picks up the tenant id from the auth module
    assert ctxt.get_tenant() == _tenant

    assert ctxt.get_tenant_id() == _tenant.id

    assert ctxt.context.type == _tenant.type

    ctxt.print_context()

    Context().reset_context()


def test_context_workspace():
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")
    _workspace = hierarchy.Workspace(
        name="workspace_name", id="workspace_id", parent=_tenant, type="Workspace"
    )

    Context().context = _workspace

    ctxt = Context()
    assert ctxt.context == _workspace

    Context().reset_context()


def test_context_virtual_workspace():
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")
    _workspace = hierarchy.VirtualWorkspace(name=".capacities", id=None, parent=_tenant)

    Context().context = _workspace

    ctxt = Context()
    assert ctxt.context == _workspace

    Context().reset_context()


def test_context_item():
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")
    _workspace = hierarchy.Workspace(
        name="workspace_name", id="workspace_id", parent=_tenant, type="Workspace"
    )
    _item = hierarchy.Item(
        name="item_name", id="item_id", parent=_workspace, item_type="Lakehouse"
    )

    Context().context = _item

    ctxt = Context()
    assert ctxt.context == _item

    Context().reset_context()


def test_context_folder():
    _tenant = hierarchy.Tenant(name="tenant_name", id="0000")
    _workspace = hierarchy.Workspace(
        name="workspace_name", id="workspace_id", parent=_tenant, type="Workspace"
    )
    _folder = hierarchy.Folder(name="folder_name", id="folder_id", parent=_workspace)

    Context().context = _folder

    ctxt = Context()
    assert ctxt.context == _folder

    Context().reset_context()


def test_context_file_name(monkeypatch):
    def mock_config_location():
        return "/tmp"

    monkeypatch.setattr(
        "fabric_cli.core.fab_context.fab_state_config.config_location",
        mock_config_location,
    )

    test_context = Context()
    session_id = test_context._get_context_session_id()

    expected_file = os.path.join("/tmp", f"context-{session_id}.json")
    expected_file = os.path.normpath(expected_file).replace("\\", "/")
    assert expected_file == f"/tmp/context-{session_id}.json"


def test_get_context_session_id(monkeypatch):
    grandparent_process = MockProcess(pid=1234, parent=None)
    parent_process = MockProcess(pid=5678, parent=grandparent_process)
    current_process = MockProcess(pid=9999, parent=parent_process)

    def mock_process():
        return current_process

    monkeypatch.setattr("fabric_cli.core.fab_context.psutil.Process", mock_process)

    context = Context()
    session_id = context._get_context_session_id()

    assert session_id == 1234


def test_get_context_session_id_no_grandparent_process(monkeypatch):
    parent_process = MockProcess(pid=1234, parent=None)
    current_process = MockProcess(pid=9999, parent=parent_process)

    def mock_process():
        return current_process

    monkeypatch.setattr("fabric_cli.core.fab_context.psutil.Process", mock_process)

    context = Context()
    session_id = context._get_context_session_id()

    assert session_id == 1234


def test_get_context_session_id_no_parent_process(monkeypatch):
    current_process = MockProcess(pid=9999, parent=None)

    def mock_process():
        return current_process

    def mock_getpid():
        return 9999

    log_calls = []

    def mock_log_debug(message):
        log_calls.append(message)

    monkeypatch.setattr("fabric_cli.core.fab_context.psutil.Process", mock_process)
    monkeypatch.setattr("fabric_cli.core.fab_context.os.getpid", mock_getpid)
    monkeypatch.setattr(
        "fabric_cli.core.fab_context.fab_logger.log_debug", mock_log_debug
    )

    context = Context()
    session_id = context._get_context_session_id()

    assert session_id == 9999
    assert len(log_calls) == 1
    assert "No parent process was found" in log_calls[0]
    assert "Falling back to the current process for session ID resolution" in log_calls[0]


def test_get_context_session_id_parent_process_exception(monkeypatch):
    def mock_process():
        raise Exception("failed to get parent process")

    def mock_getpid():
        return 8888

    log_calls = []

    def mock_log_debug(message):
        log_calls.append(message)

    monkeypatch.setattr("fabric_cli.core.fab_context.psutil.Process", mock_process)
    monkeypatch.setattr("fabric_cli.core.fab_context.os.getpid", mock_getpid)
    monkeypatch.setattr(
        "fabric_cli.core.fab_context.fab_logger.log_debug", mock_log_debug
    )

    context = Context()
    session_id = context._get_context_session_id()

    assert session_id == 8888
    assert len(log_calls) == 1
    assert "Failed to get parent process:" in log_calls[0]
    assert "Falling back to current process for session ID resolution" in log_calls[0]


def test_get_context_session_id_grandparent_process_exception(monkeypatch):
    parent_process = MockProcessWithException(pid=5678, exception_on_parent_call=True)
    current_process = MockProcess(pid=9999, parent=parent_process)

    def mock_process():
        return current_process

    log_calls = []

    def mock_log_debug(message):
        log_calls.append(message)

    monkeypatch.setattr("fabric_cli.core.fab_context.psutil.Process", mock_process)
    monkeypatch.setattr(
        "fabric_cli.core.fab_context.fab_logger.log_debug", mock_log_debug
    )

    context = Context()
    session_id = context._get_context_session_id()

    assert session_id == 5678  # Falls back to parent process PID
    assert len(log_calls) == 1
    assert "Failed to get grandparent process:" in log_calls[0]
    assert "Falling back to parent process for session ID resolution" in log_calls[0]


def test_get_context_session_id_grandparent_process_none(monkeypatch):
    parent_process = MockProcess(pid=5678, parent=None)
    current_process = MockProcess(pid=9999, parent=parent_process)

    def mock_process():
        return current_process

    log_calls = []

    def mock_log_debug(message):
        log_calls.append(message)

    monkeypatch.setattr("fabric_cli.core.fab_context.psutil.Process", mock_process)
    monkeypatch.setattr(
        "fabric_cli.core.fab_context.fab_logger.log_debug", mock_log_debug
    )

    context = Context()
    session_id = context._get_context_session_id()

    assert session_id == 5678  # Falls back to parent process PID
    assert len(log_calls) == 1
    assert "No grandparent process was found" in log_calls[0]
    assert "Falling back to parent process for session ID resolution" in log_calls[0]


class MockProcess:
    def __init__(self, pid, parent):
        self.pid = pid
        self._parent = parent

    def parent(self):
        return self._parent


class MockProcessWithException:
    def __init__(self, pid, exception_on_parent_call=False):
        self.pid = pid
        self.exception_on_parent_call = exception_on_parent_call

    def parent(self):
        if self.exception_on_parent_call:
            raise Exception("failed to get parent process")
        return None
