# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class StartStopErrors:
    @staticmethod
    def invalid_state_stop_capacity(capacityName: str, state: str) -> str:
        return f"The capacity '{capacityName}' cannot be stopped because it is in state '{state}'. Please ensure the capacity is in a valid state for this operation"

    @staticmethod
    def invalid_state_start_capacity(capacityName: str, state: str) -> str:
        return f"The capacity '{capacityName}' cannot be started because it is in state '{state}'. Please ensure the capacity is in a valid state for this operation"
