# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod

from fabric_cli.core import fab_commands as cmd
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import FabricElementType
from fabric_cli.errors import ErrorMessages


class FabricElement(ABC):
    """
    Base class for all Fabric Elements.
    """

    def __init__(self, name, id, element_type: FabricElementType, parent=None):
        self._name = name
        self._id = id
        self._type = element_type
        self._parent = parent

    def __str__(self) -> str:
        return f"[{self._type}] ({self._name}, {self._id})"

    @abstractmethod
    def __eq__(self, value) -> bool:
        if not isinstance(value, FabricElement):
            return False
        _eq_id = self.id == value.id
        _eq_name = self.name == value.name
        _eq_type = self.type == value.type
        _eq_parent = self.parent == value.parent
        return _eq_id and _eq_name and _eq_type and _eq_parent

    @property
    def id(self) -> str:
        return self._id

    @property
    def short_name(self) -> str:
        return self._name

    @property
    def full_name(self) -> str:
        return f"{self._name}.{self._type}"

    @property
    def name(self) -> str:
        return self.full_name

    @property
    def type(self) -> FabricElementType:
        return self._type

    @property
    def parent(self) -> "FabricElement":
        return self._parent

    @property
    @abstractmethod
    def path(self) -> str:
        """Return the full path of the element."""
        pass

    @property
    def path_id(self) -> str:
        if self.parent is None:
            return "/"
        return f"{self.parent.path_id.rstrip('/')}/{self.id}"

    @property
    @abstractmethod
    def tenant(self) -> "FabricElement":
        """Return the tenant of the element."""
        pass

    def check_command_support(self, commmand: Command) -> bool:
        """Check if the element type supports the command."""
        is_supported = self.type in cmd.get_supported_elements(commmand)
        if not is_supported:
            raise FabricCLIError(
                ErrorMessages.Hierarchy.command_not_supported(commmand.value),
                fab_constant.ERROR_UNSUPPORTED_COMMAND,
            )
        return True

    def is_ascendent(self, element) -> bool:
        """Check if the element is part of the hiearchy of the current element."""
        if not isinstance(element, FabricElement):
            return False
        if self == element:
            return True
        if self.parent is None:
            return False
        return self.parent.is_ascendent(element)
