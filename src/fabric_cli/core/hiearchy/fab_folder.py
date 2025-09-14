# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import re
from typing import Union

from fabric_cli.core.fab_types import FabricElementType
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_tenant import Tenant
from fabric_cli.core.hiearchy.fab_workspace import Workspace


class Folder(FabricElement):
    @staticmethod
    def validate_name(name) -> tuple[str, FabricElementType]:
        """Normalize the folder name."""
        # if the name is in the format <name>.Folder, return the name and the type
        # else assume the name is in the format <name> and return the name and the type
        pattern = r"^(.*)\.Folder$"
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            return (match.group(1), FabricElementType.FOLDER)
        else:
            return (name, FabricElementType.FOLDER)

    # The parent of a folder is either a workspace or another folder
    def __init__(self, name, id, parent: Union[Workspace, "Folder"]):
        super().__init__(name, id, FabricElementType.FOLDER, parent)

    def __eq__(self, value) -> bool:
        if not isinstance(value, Folder):
            return False
        return super().__eq__(value)

    @property
    def parent(self) -> Union[Workspace, "Folder"]:
        _parent = super().parent
        assert isinstance(_parent, Workspace) or isinstance(_parent, Folder)
        return _parent

    @property
    def path(self) -> str:
        return self.parent.path + "/" + self.name

    @property
    def path_id(self) -> str:
        return self.parent.path_id

    @property
    def tenant(self) -> Tenant:
        return self.parent.tenant

    @property
    def workspace(self) -> Workspace:
        if isinstance(self.parent, Workspace):
            return self.parent
        elif isinstance(self.parent, Folder):
            return self.parent.workspace
