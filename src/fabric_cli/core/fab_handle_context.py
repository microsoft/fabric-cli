# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import re
from argparse import Namespace
from collections import deque
from typing import Optional

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.client.fab_api_types import ApiResponse
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    FabricElementType,
    LakehouseFolders,
    OneLakeItemType,
    VirtualItemContainerType,
    VirtualItemType,
    VirtualWorkspaceItemType,
    VirtualWorkspaceType,
    WorkspaceType,
)
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import (
    FabricElement,
    Item,
    LocalPath,
    OneLakeItem,
    Tenant,
    VirtualItem,
    VirtualItemContainer,
    VirtualWorkspace,
    VirtualWorkspaceItem,
    Workspace,
)
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_mem_store as mem_store
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def get_command_context(
    local_path, raise_error=True, supports_local_path=False
) -> FabricElement:
    """Get the context of the command based on the path and the context.
    Args:
        local_path (str): The path provided in the command.
    Returns:
        dict: The context of the command.
    """
    # Check if the path is an array, and if true join it using whitespace
    if isinstance(local_path, list):
        local_path = " ".join(local_path).strip("\"'")

    path_type = "absolute"

    if local_path.startswith("/"):
        # Handle absolute path
        path = local_path
    elif local_path == "~" or local_path.startswith("~/"):
        # Handle relative path (from home directory)
        path = local_path.replace("~", f"/{get_personal_workspace_name()}", 1)
    else:
        # Handle relative path (from current context)
        path = local_path
        path_type = "relative"

    # Strip the / at the end of the path
    if len(path) > 1:
        path = path.rstrip("/")

    try:
        # Special cases for root and parent are handled here to avoid unnecessary API calls
        if path == "/" or path == "/..":
            from fabric_cli.core.fab_context import Context
            local_context: FabricElement = Context().get_tenant()
        elif path_type == "relative":
            from fabric_cli.core.fab_context import Context
            local_context = process_relative_path(Context().context, path, raise_error)
        else:
            local_context = process_absolute_path(path, raise_error)

        if isinstance(local_context, VirtualItemContainer) or isinstance(
            local_context, VirtualItem
        ):
            if local_context.item_type == VirtualItemType.EXTERNAL_DATA_SHARE:
                fab_logger.log_warning(
                    "Ensure tenant setting is enabled for External data sharing"
                )

        return local_context

    except FabricCLIError as e:
        if supports_local_path and e.status_code in [
            fab_constant.ERROR_NOT_FOUND,
            fab_constant.ERROR_INVALID_PATH,
            fab_constant.ERROR_NOT_SUPPORTED,
        ]:
            utils_ui.print_grey(
                f"{local_path} not found in Fabric, checking local file system"
            )
            # If the local path exists in the local file system, return the local path
            if os.path.exists(local_path) and os.access(local_path, os.R_OK):
                return LocalPath(local_path)
            # IF the parent directory of the local path exists in the local file system, return the local path
            elif not raise_error and os.path.exists(
                os.path.dirname(local_path)
                and os.access(os.path.dirname(local_path), os.W_OK)
            ):
                return LocalPath(local_path)

        raise e


def process_path_part(
    path_parts: deque[str], context: deque[FabricElement], raise_error: bool = True
) -> FabricElement:
    """Process the path parts and determine the context"""

    if not path_parts:
        return context.pop()

    path_part = path_parts.popleft()
    cur_ctxt = context[-1]

    match path_part:
        case "..":
            # Return to parent context (tenant is the root context)
            if cur_ctxt.type != FabricElementType.TENANT:
                context.pop()
            return process_path_part(path_parts, context, raise_error)
        case "." | "":
            # Return to the same context
            return process_path_part(path_parts, context, raise_error)
        case x if re.match("\\.\\.\\.+", x):
            # Invalid path
            raise FabricCLIError(
                ErrorMessages.Common.invalid_path(), fab_constant.ERROR_INVALID_PATH
            )
        case _:
            # Process the part of the path depending on the context
            return process_context_path(
                path_part, path_parts, context, cur_ctxt, raise_error
            )


def process_context_path(
    path_part,
    path_parts: deque[str],
    context: deque[FabricElement],
    cur_ctxt: FabricElement,
    raise_error: bool = True,
) -> FabricElement:
    if isinstance(cur_ctxt, Tenant):
        return _handle_path_in_tenant(
            path_part, path_parts, cur_ctxt, context, raise_error
        )
    elif isinstance(cur_ctxt, Workspace):
        return _handle_path_in_ws(path_part, path_parts, cur_ctxt, context, raise_error)
    elif isinstance(cur_ctxt, Folder):
        return _handle_path_in_folder(
            path_part, path_parts, cur_ctxt, context, raise_error
        )
    elif isinstance(cur_ctxt, VirtualWorkspace):
        return _handle_path_in_vws(
            path_part, path_parts, cur_ctxt, context, raise_error
        )
    elif isinstance(cur_ctxt, Item):
        return _handle_path_in_item(
            path_part, path_parts, cur_ctxt, context, raise_error
        )
    elif isinstance(cur_ctxt, VirtualItemContainer):
        return _handle_path_in_vic(
            path_part, path_parts, cur_ctxt, context, raise_error
        )
    elif isinstance(cur_ctxt, OneLakeItem):
        return _handle_path_in_onelake(
            path_part, path_parts, cur_ctxt, context, raise_error
        )
    else:
        raise FabricCLIError(
            ErrorMessages.Common.traversing_not_supported(cur_ctxt.path),
            fab_constant.ERROR_INVALID_PATH,
        )


def process_absolute_path(path: str, raise_error=True) -> FabricElement:
    """Process absolute path and return the corresponding context."""
    # Split the path into parts. The path separator is "/", but should be ignored if it is part of the name of the element, in which case it should be escaped with "\".
    path_parts = deque(x.replace("\\", "").strip() for x in re.split(r"(?<!\\)/", path))
    context_stack: deque[FabricElement] = deque(maxlen=len(path_parts))
    from fabric_cli.core.fab_context import Context
    context_stack.append(Context().get_tenant())

    local_context = process_path_part(path_parts, context_stack, raise_error)

    return local_context


def process_relative_path(
    context: FabricElement, path: str, raise_error=True
) -> FabricElement:
    """Process relative path and return the corresponding context."""

    # Get the size of the context stack
    _ctxt_size = 1
    _ctxt = context
    while _ctxt.type != FabricElementType.TENANT:
        _ctxt = _ctxt.parent
        _ctxt_size += 1

    # Split the path into parts. The path separator is "/", but should be ignored if it is part of the name of the element, in which case it should be escaped with "\"".
    path_parts = deque(x.replace("\\", "").strip() for x in re.split(r"(?<!\\)/", path))

    # Create a context stack with the correct siz
    context_stack: deque[FabricElement] = deque(maxlen=_ctxt_size + len(path_parts))

    # Build an array of all the fabric elements in the context, navigating the parents until the tenant
    # Use append left to add the elements to the front of the array
    while context.type != FabricElementType.TENANT:
        context_stack.appendleft(context)
        context = context.parent
    # Add the tenant to the context stack
    context_stack.appendleft(context)

    local_context = process_path_part(path_parts, context_stack, raise_error)

    return local_context


def get_personal_workspace_name() -> str:
    """Get the personal workspace name."""
    # Personal workspace name is only available in interactive mode
    from fabric_cli.core.fab_auth import FabAuth
    if FabAuth().get_identity_type() == "user":
        # Personal workspace is the only workspace that is not in the format <name>.Workspace but <name>.Personal
        from fabric_cli.core.fab_context import Context
        _workspaces = mem_store.get_workspaces(Context().get_tenant())
        for ws in _workspaces:
            if ws.ws_type == WorkspaceType.PERSONAL:
                return ws.name
        raise FabricCLIError(
            ErrorMessages.Common.personal_workspace_not_found(),
            fab_constant.ERROR_NOT_FOUND,
        )
    else:
        raise FabricCLIError(
            ErrorMessages.Common.personal_workspace_user_auth_only(),
            fab_constant.ERROR_INVALID_OPERATION,
        )


def _get_workspace_id(
    tenant: Tenant, ws_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        workspace_id = mem_store.get_workspace_id(tenant, ws_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            workspace_id = None
        else:
            raise e

    return workspace_id


def _get_capacity_id(
    tenant: Tenant, capacity_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        capacity_id = mem_store.get_capacity_id(tenant, capacity_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            capacity_id = None
        else:
            raise e

    return capacity_id


def _get_domain_id(
    tenant: Tenant, domain_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        domain_id = mem_store.get_domain_id(tenant, domain_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            domain_id = None
        else:
            raise e

    return domain_id


def _get_connection_id(
    tenant: Tenant, connection_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        connection_id = mem_store.get_connection_id(tenant, connection_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            connection_id = None
        else:
            raise e

    return connection_id


def _get_folder_id(
    workspace: Workspace, folder_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        folder_id = mem_store.get_folder_id(workspace, folder_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            folder_id = None
        else:
            raise e

    return folder_id


def _get_nested_folder_id(
    folder: Folder, nested_folder_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        nested_folder_id = mem_store.get_nested_folder_id(folder, nested_folder_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            nested_folder_id = None
        else:
            raise e

    return nested_folder_id


def _get_gateway_id(
    tenant: Tenant, gateway_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        gateway_id = mem_store.get_gateway_id(tenant, gateway_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            gateway_id = None
        else:
            raise e

    return gateway_id


def _get_item_id(
    workspace: Workspace, item_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        item_id = mem_store.get_item_id(workspace, item_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            item_id = None
        else:
            raise e

    return item_id


def _get_spark_pool_id(
    container: VirtualItemContainer, spark_pool_name: str, raise_error: bool = True
) -> Optional[str]:
    try:
        spark_pool_id = mem_store.get_spark_pool_id(container, spark_pool_name)
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            spark_pool_id = None
        else:
            raise e

    return spark_pool_id


def _get_managed_identity_id(
    container: VirtualItemContainer,
    managed_identity_name: str,
    raise_error: bool = True,
) -> Optional[str]:
    try:
        managed_identity_id = mem_store.get_managed_identity_id(
            container, managed_identity_name
        )
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            managed_identity_id = None
        else:
            raise e

    return managed_identity_id


def _get_managed_private_endpoint_id(
    container: VirtualItemContainer,
    managed_private_endpoint_name: str,
    raise_error: bool = True,
) -> Optional[str]:
    try:
        managed_private_endpoint_id = mem_store.get_managed_private_endpoint_id(
            container, managed_private_endpoint_name
        )
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            managed_private_endpoint_id = None
        else:
            raise e

    return managed_private_endpoint_id


def _get_external_data_share_id(
    container: VirtualItemContainer,
    external_data_share_name: str,
    raise_error: bool = True,
) -> Optional[str]:
    try:
        external_data_share_id = mem_store.get_external_data_share_id(
            container, external_data_share_name
        )
    except FabricCLIError as e:
        if not (raise_error) and e.status_code == fab_constant.ERROR_NOT_FOUND:
            external_data_share_id = None
        else:
            raise e

    return external_data_share_id


def _handle_path_in_tenant(
    path_part: str,
    path_parts,
    tenant: Tenant,
    context: deque[FabricElement],
    raise_error,
) -> FabricElement:
    elem_type_str = path_part
    if not path_part.startswith("."):
        elem_type_str = path_part.split(".")[-1]
    try:
        elem = FabricElementType.from_string(elem_type_str)
    except FabricCLIError:
        elem = None
    match elem:
        case FabricElementType.WORKSPACE:
            (ws_name, ws_type) = Workspace.validate_name(path_part)
            full_ws_name = f"{ws_name}.{ws_type.value}"
            ws_id = _get_workspace_id(tenant, full_ws_name, raise_error)
            workspace = Workspace(ws_name, ws_id, tenant, ws_type.value)
            context.append(workspace)
            return process_path_part(path_parts, context, raise_error)
        case FabricElementType.VIRTUAL_WORKSPACE:
            (vws_name, type) = VirtualWorkspace.validate_name(path_part)
            if type not in [
                VirtualWorkspaceType.CAPACITY,
                VirtualWorkspaceType.CONNECTION,
                VirtualWorkspaceType.GATEWAY,
                VirtualWorkspaceType.DOMAIN,
            ]:
                raise FabricCLIError(
                    ErrorMessages.Common.type_not_supported(str(type)),
                    fab_constant.ERROR_INVALID_OPERATION,
                )
            vws = VirtualWorkspace(vws_name, None, tenant)
            context.append(vws)
            return process_path_part(path_parts, context, raise_error)

        case _:
            _path = f"/{path_part}"
            raise FabricCLIError(
                ErrorMessages.Common.invalid_path(_path),
                fab_constant.ERROR_INVALID_PATH,
            )


def _handle_path_in_ws(
    path_part,
    path_parts,
    workspace: Workspace,
    context: deque[FabricElement],
    raise_error,
) -> FabricElement:
    ws_id = workspace.id
    if ws_id is None:
        raise FabricCLIError(
            ErrorMessages.Common.resource_not_found(
                {"type": "Workspace", "name": workspace.name}
            ),
            fab_constant.ERROR_NOT_FOUND,
        )
    elem_type_str = path_part
    if not path_part.startswith("."):
        elem_type_str = path_part.split(".")[-1]
    try:
        elem = FabricElementType.from_string(elem_type_str)
    except FabricCLIError:
        elem = None
    match elem:
        case FabricElementType.ITEM:
            (item_name, item_type) = Item.validate_name(path_part)
            item_full_name = f"{item_name}.{item_type.value}"
            _item_id = _get_item_id(workspace, item_full_name, raise_error)
            item = Item(item_name, _item_id, workspace, str(item_type))
            context.append(item)
            return process_path_part(path_parts, context, raise_error)
        case FabricElementType.VIRTUAL_ITEM_CONTAINER:
            (vic_name, vic_type) = VirtualItemContainer.validate_name(path_part)
            if vic_type not in [
                VirtualItemContainerType.SPARK_POOL,
                VirtualItemContainerType.MANAGED_IDENTITY,
                VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT,
                VirtualItemContainerType.EXTERNAL_DATA_SHARE,
            ]:
                raise FabricCLIError(
                    ErrorMessages.Common.type_not_supported(str(vic_type)),
                    fab_constant.ERROR_INVALID_OPERATION,
                )
            vic = VirtualItemContainer(vic_name, None, workspace)
            context.append(vic)

            return process_path_part(path_parts, context, raise_error)
        case FabricElementType.FOLDER:
            (folder_name, folder_type) = Folder.validate_name(path_part)
            folder_full_name = f"{folder_name}.{folder_type}"
            _folder_id = _get_folder_id(workspace, folder_full_name, raise_error)
            folder = Folder(folder_name, _folder_id, workspace)
            context.append(folder)
            return process_path_part(path_parts, context, raise_error)
        case _:
            _path = f"{workspace.path}/{path_part}"
            raise FabricCLIError(
                ErrorMessages.Common.invalid_path(_path),
                fab_constant.ERROR_INVALID_PATH,
            )


def _handle_path_in_folder(
    path_part, path_parts, folder: Folder, context: deque[FabricElement], raise_error
) -> FabricElement:
    folder_id = folder.id
    if folder_id is None:
        raise FabricCLIError(
            ErrorMessages.Common.folder_not_found(folder.name),
            fab_constant.ERROR_NOT_FOUND,
        )
    elem_type_str = path_part.split(".")[-1]
    try:
        elem = FabricElementType.from_string(elem_type_str)
    except FabricCLIError:
        elem = None
    match elem:
        case FabricElementType.ITEM:
            (item_name, item_type) = Item.validate_name(path_part)
            item_full_name = f"{item_name}.{item_type.value}"
            _item_id = _get_item_id(folder.workspace, item_full_name, raise_error)
            item = Item(item_name, _item_id, folder, str(item_type))
            context.append(item)
            return process_path_part(path_parts, context, raise_error)
        case FabricElementType.FOLDER:
            (folder_name, folder_type) = Folder.validate_name(path_part)
            folder_full_name = f"{folder_name}.{folder_type}"
            _folder_id = _get_nested_folder_id(folder, folder_full_name, raise_error)
            folder = Folder(folder_name, _folder_id, folder)
            context.append(folder)
            return process_path_part(path_parts, context, raise_error)
        case _:
            _path = f"{folder.path}/{path_part}"
            raise FabricCLIError(
                ErrorMessages.Common.invalid_path(_path),
                fab_constant.ERROR_INVALID_PATH,
            )


def _handle_path_in_item(
    path_part, path_parts, item: Item, context: deque[FabricElement], raise_error
) -> FabricElement:
    # Only support traversing into onelake items.
    # Onelake items are items which support the FS_LS command

    item.check_command_support(Command.FS_LS)
    item_id = item.id
    if item_id is None:
        raise FabricCLIError(
            ErrorMessages.Common.resource_not_found(
                {"type": "Item", "name": item.name}
            ),
            fab_constant.ERROR_NOT_FOUND,
        )
    # Get the folders of the item
    item_folders = item.get_folders()
    folder = next(
        (folder for folder in item_folders if folder.lower() == path_part.lower()),
        None,
    )
    if folder is None:
        raise FabricCLIError(
            ErrorMessages.Common.folder_not_found_in_item(
                path_part, item.name, ", ".join(item_folders)
            ),
            fab_constant.ERROR_NOT_SUPPORTED,
        )

    onelake_folder = OneLakeItem(folder, "0000", item, OneLakeItemType.FOLDER)
    context.append(onelake_folder)

    return process_path_part(path_parts, context, raise_error)


def _handle_path_in_onelake(
    path_part,
    path_parts,
    onelake_resource: OneLakeItem,
    context: deque[FabricElement],
    raise_error,
) -> FabricElement:
    _path_part = utils.remove_dot_suffix(path_part)
    _path = f"{onelake_resource.path_id}/{_path_part}".lstrip("/")
    response = _get_onelake_details(_path)
    if response is None:
        _path_part = path_part
        _path = f"{onelake_resource.path_id}/{_path_part}".lstrip("/")
        response = _get_onelake_details(_path)
    if response is None:
        if not raise_error and len(path_parts) == 0:
            # A path that does not exists is undefined and has no id
            return OneLakeItem(
                _path_part, None, onelake_resource, OneLakeItemType.UNDEFINED
            )
        else:
            raise FabricCLIError(
                ErrorMessages.Common.path_not_found(_path),
                fab_constant.ERROR_NOT_FOUND,
            )
    assert response.status_code == 200
    match response.headers.get("x-ms-resource-type", "undefined"):
        case "directory":
            if response.headers.get("x-ms-onelake-shortcut-path", "false") == "true":
                type = OneLakeItemType.SHORTCUT
            elif onelake_resource.local_path == LakehouseFolders.TABLES.value:
                type = OneLakeItemType.TABLE
            else:
                type = OneLakeItemType.FOLDER
        case "file":
            type = OneLakeItemType.FILE
        case _:
            type = OneLakeItemType.UNDEFINED

    elem = OneLakeItem(_path_part, "0000", onelake_resource, type)
    context.append(elem)
    return process_path_part(path_parts, context, raise_error)


def _get_onelake_details(path: str) -> Optional[ApiResponse]:

    args = Namespace()
    args.from_path = path
    try:
        response = onelake_api.get_properties(args)
        return response
    except FabricCLIError as e:
        if e.status_code == fab_constant.ERROR_NOT_FOUND:
            return None
        else:
            raise e


def _handle_path_in_vws(
    path_part,
    path_parts,
    cur_ctxt: VirtualWorkspace,
    context: deque[FabricElement],
    raise_error,
) -> FabricElement:
    (item_name, item_type) = VirtualWorkspaceItem.validate_name(path_part)

    if cur_ctxt.item_type != item_type:
        raise FabricCLIError(
            ErrorMessages.Common.item_not_supported_in_context(
                str(item_type), str(cur_ctxt.type)
            ),
            fab_constant.ERROR_INVALID_PATH,
        )

    match item_type:
        case VirtualWorkspaceItemType.CAPACITY:
            _capacity_id = _get_capacity_id(
                cur_ctxt.tenant, f"{item_name}.{str(item_type)}", raise_error
            )
            capacity = VirtualWorkspaceItem(
                item_name, _capacity_id, cur_ctxt, str(item_type)
            )
            context.append(capacity)
            return process_path_part(path_parts, context, raise_error)
        case VirtualWorkspaceItemType.DOMAIN:
            _domain_id = _get_domain_id(
                cur_ctxt.tenant, f"{item_name}.{str(item_type)}", raise_error
            )
            domain = VirtualWorkspaceItem(
                item_name, _domain_id, cur_ctxt, str(item_type)
            )
            context.append(domain)
            return process_path_part(path_parts, context, raise_error)
        case VirtualWorkspaceItemType.CONNECTION:
            _connection_id = _get_connection_id(
                cur_ctxt.tenant, f"{item_name}.{str(item_type)}", raise_error
            )
            connection = VirtualWorkspaceItem(
                item_name, _connection_id, cur_ctxt, str(item_type)
            )
            context.append(connection)
            return process_path_part(path_parts, context, raise_error)
        case VirtualWorkspaceItemType.GATEWAY:
            _gateway_id = _get_gateway_id(
                cur_ctxt.tenant, f"{item_name}.{str(item_type)}", raise_error
            )
            gateway = VirtualWorkspaceItem(
                item_name, _gateway_id, cur_ctxt, str(item_type)
            )
            context.append(gateway)
            return process_path_part(path_parts, context, raise_error)
        case _:
            raise FabricCLIError(
                ErrorMessages.Common.item_not_supported(str(item_type)),
                fab_constant.ERROR_INVALID_PATH,
            )


def _handle_path_in_vic(
    path_part,
    path_parts,
    cur_ctxt: VirtualItemContainer,
    context: deque[FabricElement],
    raise_error,
) -> FabricElement:
    (item_name, item_type) = VirtualItem.validate_name(path_part)

    if cur_ctxt.item_type != item_type:
        raise FabricCLIError(
            ErrorMessages.Common.item_not_supported_in_context(
                str(item_type), str(cur_ctxt.type)
            ),
            fab_constant.ERROR_INVALID_PATH,
        )

    match item_type:
        case VirtualItemType.SPARK_POOL:
            _spark_pool_id = _get_spark_pool_id(
                cur_ctxt, f"{item_name}.{str(item_type)}", raise_error
            )
            spark_pool = VirtualItem(
                item_name, _spark_pool_id, cur_ctxt, str(item_type)
            )
            context.append(spark_pool)
            return process_path_part(path_parts, context, raise_error)

        case VirtualItemType.MANAGED_IDENTITY:
            _managed_identity_id = _get_managed_identity_id(
                cur_ctxt, f"{item_name}.{str(item_type)}", raise_error
            )
            managed_identity = VirtualItem(
                item_name, _managed_identity_id, cur_ctxt, str(item_type)
            )
            context.append(managed_identity)
            return process_path_part(path_parts, context, raise_error)

        case VirtualItemType.MANAGED_PRIVATE_ENDPOINT:
            _managed_private_endpoint_id = _get_managed_private_endpoint_id(
                cur_ctxt, f"{item_name}.{str(item_type)}", raise_error
            )
            managed_private_endpoint = VirtualItem(
                item_name, _managed_private_endpoint_id, cur_ctxt, str(item_type)
            )
            context.append(managed_private_endpoint)
            return process_path_part(path_parts, context, raise_error)

        case VirtualItemType.EXTERNAL_DATA_SHARE:
            _external_data_share_id = _get_external_data_share_id(
                cur_ctxt, f"{item_name}.{str(item_type)}", raise_error
            )
            external_data_share = VirtualItem(
                item_name, _external_data_share_id, cur_ctxt, str(item_type)
            )
            context.append(external_data_share)
            return process_path_part(path_parts, context, raise_error)
