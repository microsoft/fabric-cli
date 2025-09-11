# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.client import fab_api_onelake as onelake_api
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    ItemOnelakeWritableFoldersMap,
    ItemType,
    OneLakeItemType,
)
from fabric_cli.core.hiearchy.fab_hiearchy import OneLakeItem
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui


class OneLakeFileContent:
    def __init__(self, properties: dict, content: bytes) -> None:
        self.properties = properties
        self.content = content

    def get_properties(self) -> dict:
        return self.properties

    def get_content(self) -> bytes:
        return self.content

    def get_content_length(self) -> int:
        return int(self.properties.get("Content-Length", 0))

    def get_content_type(self) -> str:
        return self.properties.get("Content-Type", "")

    def get_content_encoding(self) -> str:
        return self.properties.get("Content-Encoding", "")


def upload_file_onelake(
    args: Namespace, file_content: bytes | OneLakeFileContent
) -> None:
    response = onelake_api.touch_file(args)
    if response.status_code == 201:
        content: bytes = b""
        # Infer the content type from the file extension
        if isinstance(file_content, bytes):
            content = file_content
            content_type = _infer_content_type(args.to_path)
        elif isinstance(file_content, OneLakeFileContent):
            content = file_content.get_content()
            content_type = file_content.get_content_type()

        content_length = len(content)

        onelake_api.append_file(args, content, 0, content_type, content_length)
        onelake_api.flush_file(args, content_length, content_type)
        utils_ui.print_output_format(args, message="Done")


def get_file_content_onelake(args: Namespace) -> OneLakeFileContent:
    response = onelake_api.get(args)
    # Transform the headers into a dictionary
    properties = dict(response.headers)
    return OneLakeFileContent(properties, response.content)


def get_onelake_file_destination(
    to_context: OneLakeItem, sourceFileName: str
) -> OneLakeItem:
    # If the destination is a folder or shortcut, update the context to a new file inside the folder with the same name as the source
    if to_context.nested_type in [
        OneLakeItemType.SHORTCUT,
        OneLakeItemType.FOLDER,
    ]:
        to_context = OneLakeItem(
            sourceFileName,
            to_context.id,
            to_context,
            OneLakeItemType.FILE,
        )
        return to_context
    elif to_context.nested_type == OneLakeItemType.FILE or (
        to_context.nested_type == OneLakeItemType.UNDEFINED and to_context.id is None
    ):
        return to_context

    raise FabricCLIError(
        ErrorMessages.Common.invalid_destination_expected_file_or_folder(),
        fab_constant.ERROR_INVALID_PATH,
    )


def check_onelake_destination(to_context: OneLakeItem) -> None:
    item_type: ItemType = to_context.item.item_type
    root_folder = to_context.root_folder
    supported_folders = ItemOnelakeWritableFoldersMap[item_type]

    if root_folder not in supported_folders:
        raise FabricCLIError(
            ErrorMessages.Common.cannot_write_in_folder(root_folder, str(item_type), str(supported_folders)),
            fab_constant.ERROR_NOT_SUPPORTED,
        )


# Utils
def _infer_content_type(file_path: str) -> str:
    """Infer the content type from the file extension."""
    if file_path.endswith(".json"):
        return "application/json"
    elif file_path.endswith(".csv"):
        return "text/csv"
    elif file_path.endswith(".txt"):
        return "text/plain"
    else:
        return "application/octet-stream"
