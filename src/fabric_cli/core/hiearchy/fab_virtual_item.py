# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core.fab_types import FabricElementType, VirtualItemType
from fabric_cli.core.hiearchy.fab_base_item import _BaseItem
from fabric_cli.core.hiearchy.fab_virtual_item_container import VirtualItemContainer
from fabric_cli.core.hiearchy.fab_workspace import Workspace


class VirtualItem(_BaseItem):
    @staticmethod
    def validate_name(name) -> tuple[str, VirtualItemType]:
        return _BaseItem._validate_name(name, VirtualItemType)

    def __init__(self, name, id, parent: VirtualItemContainer, item_type: str):
        (_, _type) = VirtualItem.validate_name(f"{name}.{item_type}")
        super().__init__(name, id, FabricElementType.VIRTUAL_ITEM, parent, _type)

    @property
    def item_type(self) -> VirtualItemType:
        _item_type = super().item_type
        assert isinstance(_item_type, VirtualItemType)
        return _item_type

    @property
    def parent(self) -> VirtualItemContainer:
        _parent = super().parent
        assert isinstance(_parent, VirtualItemContainer)
        return _parent

    @property
    def workspace(self) -> Workspace:
        return self.parent.workspace


class ExternalDataShareVirtualItem(VirtualItem):
    def __init__(
        self,
        name,
        id,
        parent: VirtualItemContainer,
        item_type: str,
        status: str,
        item_id: str,
    ):
        super().__init__(name, id, parent, item_type)
        self._status = status
        self._item_id = item_id

    @property
    def status(self) -> str:
        return self._status

    @property
    def item_id(self) -> str:
        return self._item_id
