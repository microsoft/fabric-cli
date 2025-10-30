# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

class User:
    def __init__(self, user_data: dict[str, str]):
        # Expecting keys: "id", "upn"
        self._id = user_data.get("id") or ""
        self._upn = user_data.get("upn") or ""

    @property
    def id(self) -> str:
        return self._id

    @property
    def upn(self) -> str:
        return self._upn


class ServicePrincipal:
    def __init__(self, sp_data: dict[str, str]):
        # Expecting key: "id"
        self._id = sp_data.get("id") or ""

    @property
    def id(self) -> str:
        return self._id


class Capacity:
    def __init__(self, capacity_data: dict[str, str]):
        self._id = capacity_data.get("id") or ""
        self._name = capacity_data.get("name") or ""

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name


class Label:
    def __init__(self, user_data: dict[str, str]):
        # Expecting keys: "id", "upn"
        self._id = user_data.get("id") or ""
        self._name = user_data.get("name") or ""

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name


class EntityMetadata:
    def __init__(self, display_name: str, name: str, full_path: str):
        self._display_name = display_name
        self._name = name
        self._full_path = full_path

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def full_path(self) -> str:
        return self._full_path

    # This setter is required for the mv command
    @full_path.setter
    def full_path(self, new_path):
        self._full_path = new_path


class SQLServer:
    def __init__(self, sql_server_data: dict[str, str]):
        # Expecting keys: "server", "database"
        self._server = sql_server_data.get("server") or ""
        self._database = sql_server_data.get("database") or ""

    @property
    def server(self) -> str:
        return self._server

    @property
    def database(self) -> str:
        return self._database


class VNet:
    def __init__(self, vnet_data: dict[str, str]):
        # Expecting keys: "name", "subnet"
        self._name = vnet_data.get("name") or ""
        self._subnet = vnet_data.get("subnet") or ""

    @property
    def name(self) -> str:
        return self._name

    @property
    def subnet(self) -> str:
        return self._subnet


class CredentialDetails:
    def __init__(self, credential_data: dict[str, str]):
        # Expecting keys: "username", "password"
        self._username = credential_data.get("username") or ""
        self._password = credential_data.get("password") or ""

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

class OnPremisesGatewayDetails:
    def __init__(self, gateway_data: dict[str, str]):
        # Expecting keys: "id", "encrypted_credentials"
        self._id = gateway_data.get("id") or ""
        self._encrypted_credentials = gateway_data.get("encrypted_credentials") or ""

    @property
    def id(self) -> str:
        return self._id

    @property
    def encrypted_credentials(self) -> str:
        return self._encrypted_credentials