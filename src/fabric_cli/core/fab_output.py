# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, cast

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError

class TextFormatStyle(Enum):
    UNIX = "unix"
    KEY_VALUE = "key-value"

class OutputStatus(str, Enum):
    Success = "Success"
    Failure = "Failure"

class OutputResult:

    def __init__(
        self,
        data: Optional[Any],
        hidden_data: Optional[List[Any]],
        message: Optional[str],
        error_code: Optional[str] = None,
    ):
        self._data = data if isinstance(data, list) else ([data] if data else None)
        self._hidden_data = (
            self._create_hidden_data(hidden_data) if hidden_data is not None else None
        )
        self._error_code = error_code
        self._message = message

    @property
    def data(self) -> Optional[List[Dict[str, Any]]]:
        return self._data

    @property
    def hidden_data(self) -> Optional[List[str]]:
        return self._hidden_data

    @property
    def message(self) -> Optional[str]:
        return self._message

    def to_dict(self) -> Dict[str, Any]:
        return {
            key[1:]: value for key, value in self.__dict__.items() if value is not None
        }

    def get_data_keys(self) -> List[str]:
        if not self._data or not isinstance(self._data[0], dict):
            return []
        return list(self._data[0].keys())

    def _create_hidden_data(self, items: Any) -> List[str]:
        if not items:
            return []
        # If items are already strings, sort them directly
        if all(isinstance(item, str) for item in items):
            return sorted(items)
        # Otherwise handle items with value attribute (backward compatibility)
        sorted_items = sorted(items, key=lambda item: item.value)
        return [item.value for item in sorted_items]


class FabricCLIOutput:

    def __init__(
        self,
        command=None,
        subcommand=None,
        output_format_type=None,
        text_style: TextFormatStyle=None,
        status: OutputStatus = OutputStatus.Success,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        data: Optional[Any] = None,
        hidden_data: Optional[Any] = None,
    ):
        """Initialize a new FabricCLIOutput instance.

        Args:
            command: The command that generated this output
            output_format_type: The type of output format to be used (json / text)
            text_style: The text style to be used for text output (unix, key-value)
            status: The operation status (Success/Failed). Defaults to Success.
            message: Optional message to include in the output
            error_code: Optional error code. Only included when status is Failed.
            data: The main output data to be displayed
            hidden_data: Additional data shown only when --all flag or FAB_SHOW_HIDDEN is true

        Note:
            The data parameter is always converted to a list format internally.
            Error codes are only included in the output when status is Failed.
        """
        self._timestamp = datetime.utcnow().isoformat() + "Z"
        self._status = status
        self._command = command
        self._subcommand = subcommand
        self._output_format_type = output_format_type
        self._text_style = text_style

        self._result = OutputResult(
            data=data,
            hidden_data=hidden_data,
            message=message,
            error_code=(
                error_code or fab_constant.ERROR_UNEXPECTED_ERROR
                if status == OutputStatus.Failure
                else None
            ),
        )

    @property
    def output_format_type(self) -> Optional[str]:
        return self._output_format_type

    @property
    def result(self) -> OutputResult:
        return self._result

    @property
    def text_style(self) -> Optional[TextFormatStyle]:
        return self._text_style

    def to_json(self, indent: int = 4) -> str:
        try:
            from fabric_cli.utils.fab_util import dumps
            return dumps(self._to_dict(), indent=indent)
        except (RuntimeError, AttributeError, Exception) as e:
            raise (
                FabricCLIError(
                    fab_constant.WARNING_INVALID_JSON_FORMAT,
                    fab_constant.ERROR_INVALID_JSON,
                )
            )

    def _to_dict(self) -> Dict[str, Any]:
        # Explicitly build JSON structure
        json_dict: Dict[str, Any] = {
            "timestamp": self._timestamp,
            "status": self._status,
        }

        if self._command is not None:
            json_dict["command"] = self._command + " " + self._subcommand if self._subcommand else self._command

        # Add result as the last key
        json_dict["result"] = self._result.to_dict()

        return json_dict
