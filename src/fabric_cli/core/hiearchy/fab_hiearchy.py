# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from fabric_cli.core.hiearchy.fab_base_item import _BaseItem
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.core.hiearchy.fab_local_path import LocalPath
from fabric_cli.core.hiearchy.fab_onelake_element import OneLakeItem
from fabric_cli.core.hiearchy.fab_tenant import Tenant
from fabric_cli.core.hiearchy.fab_virtual_item import (
    ExternalDataShareVirtualItem,
    VirtualItem,
)
from fabric_cli.core.hiearchy.fab_virtual_item_container import VirtualItemContainer
from fabric_cli.core.hiearchy.fab_virtual_workspace_item import VirtualWorkspaceItem
from fabric_cli.core.hiearchy.fab_workspace import VirtualWorkspace, Workspace

################################################################################
#                      Fabric Element Hiearchy Classes                         #
################################################################################
#
################################################################################
#                          Tenant                                              #
#           _________________|_________________                                #
#          |                                   |                               #
#  Virtual Workspace                        Workspace                          #
#          |                     ______________|________________               #
#          |                    |              |                |              #
#  Virtual Ws Item         -> Folder  ----->  Item     Virtual Item Container  #
#                          |____|              |                |              #
#                                        -> OneLake        Virtual Item        #
#                                        |_____|                               #
################################################################################
