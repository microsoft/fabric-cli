# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os

from fabric_cli.core.fab_types import FabricElementType
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_tenant import Tenant


class LocalPath(FabricElement):
    def __init__(self, path):
        # Get the node id from the path
        _id = str(hash(path))
        _name = os.path.basename(path)
        super().__init__(_name, _id, FabricElementType.LOCAL_PATH)
        self._path = path

    def __eq__(self, value) -> bool:
        if not isinstance(value, LocalPath):
            return False
        return os.path.samefile(self.path, value.path)

    @property
    def tenant(self) -> Tenant:
        raise AttributeError("LocalPath does not have a tenant")

    @property
    def name(self) -> str:
        return os.path.basename(self._path)

    @property
    def path(self) -> str:
        return self._path

    def is_file(self) -> bool:
        return os.path.isfile(self._path)

    def is_directory(self) -> bool:
        return os.path.isdir(self._path)
