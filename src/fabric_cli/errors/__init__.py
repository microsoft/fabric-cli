# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .auth import AuthErrors
from .client import ClientErrors
from .common import CommonErrors
from .config import ConfigErrors
from .context import ContextErrors
from .hierarchy import HierarchyErrors
from .labels import LabelsErrors
from .mkdir import MkdirErrors
from .mv import MvErrors
from .start_stop import StartStopErrors
from .table import TableErrors


class ErrorMessages:
    Auth = AuthErrors
    Client = ClientErrors
    Common = CommonErrors
    Config = ConfigErrors
    Context = ContextErrors
    Hierarchy = HierarchyErrors
    Labels = LabelsErrors
    Mkdir = MkdirErrors
    Mv = MvErrors
    StartStop = StartStopErrors
    Table = TableErrors
    # Add more error classes as needed
