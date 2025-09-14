# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from fabric_cli.core.fab_types import FabricElementType
from fabric_cli.core.hiearchy.fab_element import FabricElement


class Tenant(FabricElement):
    def __init__(self, name, id):
        super().__init__(name, id, FabricElementType.TENANT)

    def __eq__(self, value) -> bool:
        if not isinstance(value, Tenant):
            return False
        return super().__eq__(value)

    @property
    def path(self) -> str:
        return "/"

    @property
    def tenant(self) -> "Tenant":
        return self
