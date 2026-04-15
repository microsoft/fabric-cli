# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class ConfigErrors:
    @staticmethod
    def invalid_capacity(capacityName: str) -> str:
        return f"'{capacityName}' is not a valid capacity. Please provide a valid capacity name"

    @staticmethod
    def invalid_configuration_value(
        invalidValue: str, configurationKey: str, allowedValues: list[str]
    ) -> str:
        return f"'{invalidValue}' is not a valid value for '{configurationKey}'. Allowed values are: {allowedValues}"

    @staticmethod
    def unknown_configuration_key(configurationKey: str) -> str:
        return f"'{configurationKey}' is not a recognized configuration key. Please check the available configuration keys"

    @staticmethod
    def mode_deprecated(runtime_mode: str, interactive_mode: str) -> str:
        msg = "The 'mode' setting is deprecated. "
        if runtime_mode == interactive_mode:
            msg += "Run 'exit' to leave the REPL, then use 'fab <command>' for command-line mode."
        else:
            msg += (
                "Run 'fab' without arguments to enter REPL mode, "
                "or use 'fab <command>' for command-line mode."
            )
        return msg

    @staticmethod
    def invalid_parameter_format(params: str) -> str:
        return f"Invalid parameter format: {params}"

    @staticmethod
    def config_not_set(config_name: str, message: str) -> str:
        return f"{config_name} is not set. {message}"

    @staticmethod
    def azure_subscription_id_not_set() -> str:
        return ConfigErrors.config_not_set(
            "Azure subscription ID",
            "Pass it with -P subscriptionId=<subscription_id> or set it with 'config set default_az_subscription_id <subscription_id>'"
        )

    @staticmethod
    def azure_resource_group_not_set() -> str:
        return ConfigErrors.config_not_set(
            "Azure resource group",
            "Pass it with -P resourceGroup=<resource_group> or set it with 'config set default_az_resource_group <resource_group>'"
        )

    @staticmethod
    def azure_location_not_set() -> str:
        return ConfigErrors.config_not_set(
            "Azure default location",
            "Pass it with -P location=<location> or set it with 'config set default_az_location <location>'"
        )

    @staticmethod
    def azure_admin_not_set() -> str:
        return ConfigErrors.config_not_set(
            "Azure default admin",
            "Pass it with -P admin=<admin> or set it with 'config set default_az_admin <admin>'"
        )
