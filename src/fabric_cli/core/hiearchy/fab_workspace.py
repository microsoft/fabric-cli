# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import re

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    FabricElementType,
    VirtualWorkspaceItemType,
    VirtualWorkspaceType,
    VWIMap,
    WorkspaceType,
)
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_tenant import Tenant


class _BaseWorkspace(FabricElement):

    def __init__(self, name, id, element_type, parent: Tenant):
        super().__init__(name, id, element_type, parent)

    @property
    def parent(self) -> Tenant:
        _parent = super().parent
        assert isinstance(_parent, Tenant)
        return _parent

    @property
    def path(self) -> str:
        name_scaped = self.name.replace("/", r"\/")
        return f"{self.parent.path.rstrip('/')}/{name_scaped}"

    @property
    def tenant(self) -> Tenant:
        assert isinstance(self.parent, Tenant)
        return self.parent


class Workspace(_BaseWorkspace):
    @staticmethod
    def validate_name(name) -> tuple[str, WorkspaceType]:
        # Workspace name should be in the format <name>.Workspace or <name>.Personal
        pattern = r"^(.+)\.(\w+)$"
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            # Capitalize the first letter of the workspace type
            _name = match.group(1)
            _type = WorkspaceType.from_string(match.group(2))
            return (_name, _type)
        else:
            raise FabricCLIError(
                f"Invalid workspace name '{name}'",
                fab_constant.WARNING_INVALID_WORKSPACE_NAME,
            )

    def __init__(self, name, id, parent: Tenant, type: str):
        super().__init__(name, id, FabricElementType.WORKSPACE, parent)
        # Old workspaces do not comply with the new naming convention
        if id is None:
            (_, _type) = Workspace.validate_name(f"{name}.{type}")
        else:
            _type = WorkspaceType.from_string(str(type))
        self._ws_type = _type

    def __eq__(self, value) -> bool:
        if not isinstance(value, Workspace):
            return False
        _eq_ws_type = self.ws_type == value.ws_type
        return super().__eq__(value) and _eq_ws_type

    @property
    def full_name(self) -> str:
        return f"{super().short_name}.{self.ws_type}"

    @property
    def ws_type(self) -> WorkspaceType:
        return self._ws_type


class VirtualWorkspace(_BaseWorkspace):
    @staticmethod
    def validate_name(name) -> tuple[str, VirtualWorkspaceType]:
        """Normalize the virtual workspace name."""
        try:
            vws_type = VirtualWorkspaceType.from_string(name)
        except FabricCLIError:
            raise FabricCLIError(
                f"Invalid type '{name}'",
                fab_constant.ERROR_INVALID_WORKSPACE_TYPE,
            )
        return (str(vws_type), vws_type)

    def __init__(self, name, id, parent: Tenant):
        super().__init__(name, id, FabricElementType.VIRTUAL_WORKSPACE, parent)
        (_, _type) = VirtualWorkspace.validate_name(f"{name}")
        self._vws_type = _type
        self._item_type = VWIMap[_type]

    def __eq__(self, value) -> bool:
        if not isinstance(value, VirtualWorkspace):
            return False
        _eq_vws_type = self.vws_type == value.vws_type
        _eq_item_type = self.item_type == value.item_type
        return super().__eq__(value) and _eq_vws_type and _eq_item_type

    @property
    def parent(self) -> Tenant:
        _parent = super().parent
        assert isinstance(_parent, Tenant)
        return _parent

    @property
    def full_name(self) -> str:
        return super().short_name

    @property
    def vws_type(self) -> VirtualWorkspaceType:
        return self._vws_type

    @property
    def item_type(self) -> VirtualWorkspaceItemType:
        return self._item_type
