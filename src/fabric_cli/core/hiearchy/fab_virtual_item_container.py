# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    FabricElementType,
    VICMap,
    VirtualItemContainerType,
    VirtualItemType,
)
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_tenant import Tenant
from fabric_cli.core.hiearchy.fab_workspace import Workspace
from fabric_cli.errors import ErrorMessages


class VirtualItemContainer(FabricElement):
    @staticmethod
    def validate_name(name) -> tuple[str, VirtualItemContainerType]:
        """Normalize the virtual item container name."""
        try:
            vic_type = VirtualItemContainerType.from_string(name)
        except FabricCLIError:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.invalid_type(name),
                fab_constant.ERROR_INVALID_ITEM_TYPE,
            )
        return (str(vic_type), vic_type)

    def __init__(self, name, id, parent: Workspace):
        super().__init__(name, id, FabricElementType.VIRTUAL_ITEM_CONTAINER, parent)
        (_, _type) = VirtualItemContainer.validate_name(f"{name}")
        self._vic_type = _type
        self._item_type = VICMap[_type]

    def __eq__(self, value) -> bool:
        if not isinstance(value, VirtualItemContainer):
            return False
        _eq_vit_type = self.vic_type == value.vic_type
        _eq_item_type = self.item_type == value.item_type
        return super().__eq__(value) and _eq_vit_type and _eq_item_type

    @property
    def parent(self) -> Workspace:
        _parent = super().parent
        assert isinstance(_parent, Workspace)
        return _parent

    @property
    def tenant(self) -> Tenant:
        return self.parent.tenant

    @property
    def workspace(self) -> Workspace:
        return self.parent

    @property
    def full_name(self) -> str:
        return super().short_name

    @property
    def vic_type(self) -> VirtualItemContainerType:
        return self._vic_type

    @property
    def item_type(self) -> VirtualItemType:
        return self._item_type

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.full_name}"

    @property
    def path_id(self) -> str:
        return self.parent.path_id
