# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    FabricElementType,
    FabricJobType,
    ItemFoldersMap,
    ItemType,
    ITJobMap,
    ITMutablePropMap,
)
from fabric_cli.core.hiearchy.fab_base_item import _BaseItem
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_workspace import Workspace
from fabric_cli.errors import ErrorMessages


class Item(_BaseItem):
    @staticmethod
    def validate_name(name) -> tuple[str, ItemType]:
        return _BaseItem._validate_name(name, ItemType)

    def __init__(self, name, id, parent: Workspace | Folder, item_type: str):
        if id is None:
            (_, _type) = Item.validate_name(f"{name}.{item_type}")
        else:
            _type = ItemType.from_string(str(item_type))

        super().__init__(name, id, FabricElementType.ITEM, parent, _type)

    @property
    def item_type(self) -> ItemType:
        _item_type = super().item_type
        if isinstance(_item_type, ItemType):
            return _item_type
        else:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.item_type_not_valid(str(super().item_type)),
                fab_constant.ERROR_INVALID_ITEM_TYPE,
            )

    @property
    def job_type(self) -> FabricJobType:
        return ITJobMap[self.item_type]

    @property
    def folder_id(self) -> str | None:
        return self.parent.id if isinstance(self.parent, Folder) else None

    def extract_friendly_name_path_or_default(self, key: str) -> str:
        item_type = self.item_type

        if item_type in ITMutablePropMap:
            for prop in ITMutablePropMap[item_type]:
                if key in prop:
                    return prop[key]
        return key

    @property
    def parent(self) -> Workspace | Folder:
        _parent = super().parent
        assert isinstance(_parent, Workspace) or isinstance(_parent, Folder)
        return _parent

    @property
    def workspace(self) -> Workspace:
        if isinstance(self.parent, Workspace):
            return self.parent
        else:
            assert isinstance(self.parent, Folder)
            return self.parent.workspace

    def get_folders(self) -> List[str]:
        return ItemFoldersMap.get(self.item_type, [])
