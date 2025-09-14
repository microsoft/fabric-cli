# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from argparse import Namespace

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import OneLakeItemType
from fabric_cli.core.hiearchy.fab_hiearchy import LocalPath, OneLakeItem
from fabric_cli.utils import fab_cmd_cp_utils as cp_utils
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils
from fabric_cli.utils import fab_item_util as item_utils


def copy_onelake_2_onelake(
    from_context: OneLakeItem, to_context: OneLakeItem, args: Namespace
) -> None:
    cp_utils.check_onelake_destination(to_context)

    match from_context.nested_type:
        case OneLakeItemType.FILE:
            to_context = cp_utils.get_onelake_file_destination(
                to_context, from_context.name
            )

            from_path_id, from_path_name, to_path_id, to_path_name = (
                item_utils.obtain_id_names_for_onelake(from_context, to_context)
            )
            args.from_path, args.to_path = from_path_id, to_path_id

            utils_ui.print_grey(f"Copying '{from_path_name}' → '{to_path_name}'...")
            content = cp_utils.get_file_content_onelake(args)
            if content.get_content_length() == 0:
                raise FabricCLIError(
                    "Invalid copy, source is empty", fab_constant.ERROR_INVALID_INPUT
                )

            cp_utils.upload_file_onelake(args, content)

        case OneLakeItemType.FOLDER | OneLakeItemType.SHORTCUT | OneLakeItemType.TABLE:
            raise FabricCLIError(
                "Recursive copy not supported", fab_constant.ERROR_NOT_SUPPORTED
            )


def copy_local_2_onelake(
    from_context: LocalPath, to_context: OneLakeItem, args: Namespace
) -> None:
    cp_utils.check_onelake_destination(to_context)

    # Unsupported copy operations
    if from_context.is_directory():
        raise FabricCLIError(
            "Recursive copy not supported", fab_constant.ERROR_NOT_SUPPORTED
        )

    # Check if the source is a file
    if not from_context.is_file():
        raise FabricCLIError(
            "Invalid source, expected file",
            fab_constant.ERROR_INVALID_PATH,
        )

    to_context = cp_utils.get_onelake_file_destination(to_context, from_context.name)

    args.to_path = to_context.path_id

    utils_ui.print_grey(f"Copying '{from_context.path}' → '{to_context.path}'...")

    # Read the contents of the local file using the file path property
    try:
        with open(from_context.path, "rb") as file:
            content = file.read()
            if not content:
                raise FabricCLIError(
                    "Invalid copy, source is empty", fab_constant.ERROR_INVALID_INPUT
                )

            cp_utils.upload_file_onelake(args, content)
    except Exception as e:
        if not isinstance(e, FabricCLIError):
            raise FabricCLIError(
                f"Error reading file: {e}", fab_constant.ERROR_INVALID_PATH
            )
        raise e


def copy_onelake_2_local(
    from_context: OneLakeItem, to_context: LocalPath, args: Namespace
) -> None:
    match from_context.nested_type:
        case OneLakeItemType.FILE:
            # If the destination is a folder, update the context to a new file inside the folder with the same name as the source
            if to_context.is_directory():
                to_context = LocalPath(
                    path=os.path.join(to_context.path, from_context.name),
                )

            args.from_path = from_context.path_id
            utils_ui.print_grey(
                f"Copying '{from_context.path}' → '{to_context.path}'..."
            )
            file_content = cp_utils.get_file_content_onelake(args)
            content = file_content.get_content()
            if not content:
                raise FabricCLIError(
                    "Invalid copy, source is empty", fab_constant.ERROR_INVALID_INPUT
                )

            # Write the contents to a local file using the file path property
            try:
                # Write binary content directly without encoding
                with open(to_context.path, "wb") as file:
                    file.write(content)
            except Exception as e:
                raise FabricCLIError(
                    f"Error writing file: {e}", fab_constant.ERROR_INVALID_PATH
                )

            utils_ui.print_output_format(args, message="Done")

        case OneLakeItemType.FOLDER | OneLakeItemType.SHORTCUT | OneLakeItemType.TABLE:
            raise FabricCLIError(
                "Recursive copy not supported", fab_constant.ERROR_NOT_SUPPORTED
            )
