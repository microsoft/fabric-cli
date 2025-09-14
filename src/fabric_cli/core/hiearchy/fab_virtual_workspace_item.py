# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core.fab_types import FabricElementType, VirtualWorkspaceItemType
from fabric_cli.core.hiearchy.fab_base_item import _BaseItem
from fabric_cli.core.hiearchy.fab_workspace import VirtualWorkspace


class VirtualWorkspaceItem(_BaseItem):
    @staticmethod
    def validate_name(name) -> tuple[str, VirtualWorkspaceItemType]:
        return _BaseItem._validate_name(name, VirtualWorkspaceItemType)

    def __init__(self, name, id, parent: VirtualWorkspace, item_type: str):
        (_, _type) = VirtualWorkspaceItem.validate_name(f"{name}.{item_type}")
        super().__init__(
            name, id, FabricElementType.VIRTUAL_WORKSPACE_ITEM, parent, _type
        )

    @property
    def item_type(self) -> VirtualWorkspaceItemType:
        _item_type = super().item_type
        assert isinstance(_item_type, VirtualWorkspaceItemType)
        return _item_type

    @property
    def parent(self) -> VirtualWorkspace:
        _parent = super().parent
        assert isinstance(_parent, VirtualWorkspace)
        return _parent

    @property
    def workspace(self) -> VirtualWorkspace:
        assert isinstance(self.parent, VirtualWorkspace)
        return self.parent
