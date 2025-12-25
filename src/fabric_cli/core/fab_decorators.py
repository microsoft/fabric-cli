# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from functools import wraps

import fabric_cli.core.fab_logger as fab_logger
from fabric_cli.core.fab_constant import (
    ERROR_UNAUTHORIZED,
    EXIT_CODE_AUTHORIZATION_REQUIRED,
    EXIT_CODE_ERROR,
)
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.utils import fab_ui


def singleton(class_):
    """Singleton decorator that ensures only one instance of a class exists."""
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    
    return getinstance


def handle_exceptions():
    """
    Decorator that catches FabricCLIError, logs the error, and returns
    an appropriate exit code based on error type.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FabricCLIError as e:
                fab_ui.print_output_error(
                    e,
                    args[0].command_path,
                    output_format_type=args[0].output_format,
                )
                # If the error is an unauthorized error, return 4
                if e.status_code == ERROR_UNAUTHORIZED:
                    return EXIT_CODE_AUTHORIZATION_REQUIRED
                # Return a generic error code
                return EXIT_CODE_ERROR

        return wrapper

    return decorator


def set_command_context():
    """
    Decorator that captures the command path from the first argument
    and sets it in the Context before calling the function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Import Context locally to avoid circular import
            from fabric_cli.core.fab_context import Context
            Context().command = args[0].command_path
            return func(*args, **kwargs)

        return wrapper

    return decorator
