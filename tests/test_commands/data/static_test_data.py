# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import uuid

from tests.test_commands.data.models import (
    Capacity,
    CredentialDetails,
    Label,
    ServicePrincipal,
    SQLServer,
    User,
    VNet,
)

LABEL_NON_BUSINESS = "Non-Business"
LABEL_PROTECTED = "Protected"

_static_data = None
_mock_data = None


class StaticTestData:
    """
    A class that holds test data.
    By default it will load the test data values from environment variables specified in authoring_tests.md.
    If load_static_values is False, mock values are loaded
    """

    def __init__(self, load_static_values: bool = True):
        if load_static_values:
            self._load_static_data()
        else:
            # Initialize mock objects
            self._admin = User(
                {
                    "upn": "mocked@admin_test_user",
                    "id": "00000000-0000-0000-0000-000000000001",
                }
            )

            self._user = User(
                {
                    "upn": "mocked@helper_test_user",
                    "id": "00000000-0000-0000-0000-000000000002",
                }
            )

            self._service_principal = ServicePrincipal(
                {"id": "00000000-0000-0000-0000-000000000003"}
            )

            self._capacity = Capacity(
                {
                    "id": "00000000-0000-0000-0000-000000000004",
                    "name": "mocked_fabriccli_capacity_name",
                }
            )

            self._labels = [
                Label(
                    {
                        "name": LABEL_NON_BUSINESS,
                        "id": "00000000-0000-0000-0000-000000000005",
                    }
                ),
                Label(
                    {
                        "name": LABEL_PROTECTED,
                        "id": "00000000-0000-0000-0000-000000000006",
                    }
                ),
            ]
            self._azure_subscription_id = "00000000-0000-0000-0000-000000000000"
            self._azure_resource_group = "mocked_fabriccli_resource_group"
            self._azure_location = "mocked_fabriccli_azure_location"

            self._sql_server = SQLServer(
                {
                    "server": "mocked_sql_server_server",
                    "database": "mocked_sql_server_database",
                }
            )

            self._vnet = VNet(
                {
                    "name": "mocked_fabriccli_vnet_name",
                    "subnet": "mocked_fabriccli_vnet_subnet",
                }
            )

            self._credential_details = CredentialDetails(
                {
                    "username": "mocked_fabriccli_username",
                    "password": "mocked_fabriccli_password",
                }
            )

    def _load_static_data(self):
        self._admin = User(
            {
                "upn": get_env_with_default("FABRIC_CLI_TEST_ADMIN_UPN"),
                "id": get_env_with_default("FABRIC_CLI_TEST_ADMIN_ID"),
            }
        )

        self._user = User(
            {
                "upn": get_env_with_default("FABRIC_CLI_TEST_USER_UPN"),
                "id": get_env_with_default("FABRIC_CLI_TEST_USER_ID"),
            }
        )

        self._service_principal = ServicePrincipal(
            {"id": get_env_with_default("FABRIC_CLI_TEST_SERVICE_PRINCIPAL_ID")}
        )

        self._capacity = Capacity(
            {
                "id": get_env_with_default("FABRIC_CLI_TEST_CAPACITY_ID"),
                "name": get_env_with_default("FABRIC_CLI_TEST_CAPACITY_NAME"),
            }
        )

        self._labels = [
            Label(
                {
                    "name": LABEL_NON_BUSINESS,
                    "id": get_env_with_default("FABRIC_CLI_TEST_NON_BUSINESS_LABEL_ID"),
                }
            ),
            Label(
                {
                    "name": LABEL_PROTECTED,
                    "id": get_env_with_default("FABRIC_CLI_TEST_PROTECTED_LABEL_ID"),
                }
            ),
        ]

        self._sql_server = SQLServer(
            {
                "server": get_env_with_default("FABRIC_CLI_TEST_SQL_SERVER"),
                "database": get_env_with_default("FABRIC_CLI_TEST_SQL_DATABASE"),
            }
        )

        self._vnet = VNet(
            {
                "name": get_env_with_default("FABRIC_CLI_TEST_VNET_NAME"),
                "subnet": get_env_with_default("FABRIC_CLI_TEST_VNET_SUBNET"),
            }
        )

        self._azure_location = get_env_with_default("FABRIC_CLI_TEST_AZURE_LOCATION")
        self._azure_resource_group = get_env_with_default(
            "FABRIC_CLI_TEST_AZURE_RESOURCE_GROUP"
        )
        self._azure_subscription_id = get_env_with_default(
            "FABRIC_CLI_TEST_AZURE_SUBSCRIPTION_ID"
        )

        # Load credential details from environment variables
        self._credential_details = CredentialDetails(
            {
                "username": get_env_with_default(
                    "FABRIC_CLI_TEST_CREDENTIAL_DETAILS_USERNAME"
                ),
                "password": get_env_with_default(
                    "FABRIC_CLI_TEST_CREDENTIAL_DETAILS_PASSWORD"
                ),
            }
        )

    @property
    def admin(self):
        return self._admin

    @property
    def user(self):
        return self._user

    @property
    def service_principal(self):
        return self._service_principal

    @property
    def capacity(self):
        return self._capacity

    @property
    def labels(self):
        return self._labels

    @property
    def azure_subscription_id(self):
        return self._azure_subscription_id

    @property
    def azure_resource_group(self):
        return self._azure_resource_group

    @property
    def azure_location(self):
        return self._azure_location

    @property
    def sql_server(self):
        return self._sql_server

    @property
    def vnet(self):
        return self._vnet

    @property
    def credential_details(self):
        return self._credential_details


def get_static_data() -> StaticTestData:
    """
    Returns test data when executing tests in live mode
    """
    global _static_data
    if _static_data is None:
        _static_data = StaticTestData()
    return _static_data


def get_mock_data() -> StaticTestData:
    """
    Returns mock values of test data.
    Used for mocking values when recording tests and for tests assertions when executing tests in playback mode
    """
    global _mock_data
    if _mock_data is None:
        _mock_data = StaticTestData(False)
    return _mock_data


def get_env_with_default(var_name: str) -> str:
    """
    Try to read environment variable value or return a default message if missing/empty.

    Args:
        var_name (str): The name of the environment variable to retrieve.

    Returns:
        str: Environment variable value or "<Missing {var_name} value>".
    """
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        return f"<Missing {var_name} value>"
    return value
