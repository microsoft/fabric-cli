# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Union

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import FabricElementType, OneLakeItemType
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.core.hiearchy.fab_tenant import Tenant
from fabric_cli.core.hiearchy.fab_workspace import Workspace
from fabric_cli.errors import ErrorMessages


class OneLakeItem(FabricElement):
    def __init__(
        self,
        name: str,
        id: Optional[str],
        parent: Union[Item, "OneLakeItem"],
        nested_type: OneLakeItemType,
    ):
        super().__init__(name, id, FabricElementType.ONELAKE, parent)
        self._nested_type = nested_type
        if isinstance(parent, Item):
            self._root_folder = name
        else:
            self._root_folder = parent.root_folder

    def __eq__(self, value):
        if not isinstance(value, OneLakeItem):
            return False
        _eq_nested_type = self.nested_type == value.nested_type
        _eq_local_path = self.path.rstrip("/") == value.path.rstrip("/")
        return super().__eq__(value) and _eq_nested_type and _eq_local_path

    @property
    def tenant(self) -> Tenant:
        assert isinstance(self.parent.tenant, Tenant)
        return self.parent.tenant

    @property
    def parent(self) -> Union[Item, "OneLakeItem"]:
        _parent = super().parent
        assert isinstance(_parent, Item) or isinstance(_parent, OneLakeItem)
        return _parent

    @property
    def workspace(self) -> Workspace:
        assert isinstance(self.parent.workspace, Workspace)
        return self.parent.workspace

    @property
    def item(self) -> Item:
        if isinstance(self.parent, Item):
            return self.parent
        elif isinstance(self.parent, OneLakeItem):
            return self.parent.item
        else:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.invalid_parent_type(str(type(self.parent))),
                fab_constant.ERROR_INVALID_ELEMENT_TYPE,
            )

    @property
    def full_name(self):
        if self.nested_type == OneLakeItemType.SHORTCUT:
            return f"{self.short_name}.Shortcut"
        else:
            return self.short_name

    @property
    def nested_type(self) -> OneLakeItemType:
        return self._nested_type

    @property
    def local_path(self) -> str:
        if isinstance(self.parent, Item):
            return f"{self.short_name}"
        elif isinstance(self.parent, OneLakeItem):
            return f"{self.parent.local_path}/{self.short_name}"

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.full_name}"

    @property
    def path_id(self) -> str:
        return f"{self.parent.path_id}/{self.short_name}"

    @property
    def root_folder(self) -> str:
        if isinstance(self.parent, Item):
            return self._root_folder
        elif isinstance(self.parent, OneLakeItem):
            return self.parent.root_folder

    def is_shortcut_path(self) -> bool:
        if isinstance(self.parent, Item):
            return self.nested_type == OneLakeItemType.SHORTCUT
        elif isinstance(self.parent, OneLakeItem):
            return (
                self.nested_type == OneLakeItemType.SHORTCUT
                or self.parent.is_shortcut_path()
            )
