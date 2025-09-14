# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import re
from typing import Any, Optional

from fabric_cli.core import fab_commands as cmd
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    FabricElementType,
    ItemType,
    VirtualItemType,
    VirtualWorkspaceItemType,
)
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_virtual_item_container import VirtualItemContainer
from fabric_cli.core.hiearchy.fab_workspace import VirtualWorkspace, Workspace
from fabric_cli.errors import ErrorMessages


class _BaseItem(FabricElement):
    @staticmethod
    def _validate_name(name, sub_class_type) -> tuple[str, Any]:
        """Normalize the item name."""
        # Item name should be in the format <name>.<type>
        # Item name can only contain alphanumeric characters, spaces, underscores, and hyphens
        # Item name should not end with a space
        pattern = r"^(.*)\.([a-zA-Z0-9_-]+)$"
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            item_type = sub_class_type.from_string(match.group(2))
            strict_name_pattern = r"[^a-zA-Z0-9_]"
            unsupported_types = {
                ItemType.LAKEHOUSE,
                ItemType.ML_EXPERIMENT,
                ItemType.ML_MODEL,
                ItemType.EVENTSTREAM,
            }
            if (
                re.search(strict_name_pattern, match.group(1))
                and item_type in unsupported_types
            ):
                raise FabricCLIError(
                    ErrorMessages.Hierarchy.item_name_contains_unsupported_characters(
                        str(item_type), match.group(1)
                    ),
                    fab_constant.WARNING_INVALID_SPECIAL_CHARACTERS,
                )
            return (match.group(1), item_type)
        else:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.invalid_item_name(name),
                fab_constant.WARNING_INVALID_ITEM_NAME,
            )

    def __init__(
        self,
        name: str,
        id: Optional[str],
        element_type: FabricElementType,
        parent: Optional[Workspace | VirtualWorkspace | VirtualItemContainer | Folder],
        item_type: Optional[
            ItemType | VirtualItemType | VirtualWorkspaceItemType
        ] = None,
    ):
        super().__init__(name, id, element_type, parent)
        self._item_type = item_type

    def __eq__(self, value) -> bool:
        if not isinstance(value, _BaseItem):
            return False
        _eq_item_type = self.item_type == value.item_type
        return super().__eq__(value) and _eq_item_type

    @property
    def tenant(self) -> Any:
        return self.parent.tenant

    @property
    def full_name(self) -> str:
        return f"{super().short_name}.{self.item_type}"

    @property
    def item_type(
        self,
    ) -> Optional[ItemType | VirtualItemType | VirtualWorkspaceItemType]:
        return self._item_type

    @property
    def path(self) -> str:
        return f"{self.parent.path}/{self.full_name}"

    def check_command_support(self, commmand: Command) -> bool:
        """Check if the element type supports the command."""
        is_unsupported = self.item_type in cmd.get_unsupported_items(commmand)
        is_supported = self.item_type in cmd.get_supported_items(commmand)
        if is_unsupported:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.command_not_supported(commmand.value),
                fab_constant.ERROR_UNSUPPORTED_COMMAND,
            )
        if is_supported:
            return True
        try:
            super().check_command_support(commmand)
        except FabricCLIError:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.command_not_supported(commmand.value),
                fab_constant.ERROR_UNSUPPORTED_COMMAND,
            )
        return True
