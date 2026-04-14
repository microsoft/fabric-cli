# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


def setup_delete_request_params(args) -> None:
    """Set up request parameters for delete operations with hard support.

    Args:
        args: Namespace object to modify with request_params

    This helper centralizes the logic for merging hard flags into request parameters,
    avoiding duplication across delete operation handlers.
    """
    params = args.__dict__.setdefault("request_params", {})
    params.pop("hardDelete", None)
    if getattr(args, "hard", False):
        params["hardDelete"] = "true"
