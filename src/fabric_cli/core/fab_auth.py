# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import uuid
from binascii import hexlify
from typing import Any, NamedTuple, Optional

import jwt
import msal
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from msal_extensions import (
    FilePersistence,
    PersistedTokenCache,
    build_encrypted_persistence,
)

from fabric_cli.core import fab_constant as con
from fabric_cli.core import fab_logger
from fabric_cli.core import fab_state_config as config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.hiearchy.fab_tenant import Tenant
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class FabAuth:
    def __init__(self):
        # Auth file path
        self.auth_file = os.path.join(config.config_location(), "auth.json")
        self.cache_file = os.path.join(config.config_location(), "cache.bin")

        self.aad_public_key = None
        # Reset the auth info
        self.app: msal.ClientApplication = None
        self._auth_info = {}

        # Load the auth info and environment variables
        self._load_auth()
        self._load_env()

    def _save_auth(self):
        with open(self.auth_file, "w") as file:
            file.write(json.dumps(self._get_auth_info()))

    def _load_auth(self):
        if os.path.exists(self.auth_file) and os.stat(self.auth_file).st_size != 0:
            with open(self.auth_file, "r") as file:
                self._auth_info = json.load(file)
            # Migrate FAB_AUTH_MODE to IDENTITY_TYPE if it exists
            if con.FAB_AUTH_MODE in self._auth_info:
                self._auth_info[con.IDENTITY_TYPE] = self._auth_info[con.FAB_AUTH_MODE]
                del self._auth_info[con.FAB_AUTH_MODE]
                self._save_auth()

            # remove legacy fab authority key from auth.json as it is no longer used
            if con.FAB_AUTHORITY in self._auth_info:
                del self._auth_info[con.FAB_AUTHORITY]
                self._save_auth()  # Save changes after migration
        else:
            self._auth_info = {}

    def _validate_environment_variables(self):
        # We ignore the FAB_TENANT_ID since it can be used for a user to login in a different tenant through interactive login
        # and we don't want to block that.
        auth_env_vars = [
            "FAB_SPN_CLIENT_ID",
            "FAB_SPN_CLIENT_SECRET",
            "FAB_SPN_CERT_PATH",
            "FAB_SPN_FEDERATED_TOKEN",
            "FAB_SPN_CERT_PASSWORD",
            "FAB_MANAGED_IDENTITY",
        ]

        # Start the check if any of the auth env vars are set
        if any(var in os.environ for var in auth_env_vars):
            if "FAB_MANAGED_IDENTITY" in os.environ and os.environ[
                "FAB_MANAGED_IDENTITY"
            ].lower() in ["true", "1"]:
                # Managed Identity is set, password or cert path should not be set
                if any(
                    var in os.environ
                    for var in [
                        "FAB_SPN_CLIENT_SECRET",
                        "FAB_SPN_CERT_PATH",
                        "FAB_SPN_FEDERATED_TOKEN",
                    ]
                ):
                    raise FabricCLIError(
                        ErrorMessages.Auth.managed_identity_incompatible_vars(),
                        con.ERROR_AUTHENTICATION_FAILED,
                    )
            elif "FAB_SPN_CLIENT_ID" in os.environ:
                if "FAB_TENANT_ID" not in os.environ:
                    raise FabricCLIError(
                        ErrorMessages.Auth.tenant_id_env_var_required(),
                        con.ERROR_AUTHENTICATION_FAILED,
                    )
                # Xor check for FAB_SPN_CLIENT_SECRET and FAB_SPN_CERT_PATH and FAB_SPN_FEDERATED_TOKEN

                if (
                    ("FAB_SPN_CLIENT_SECRET" in os.environ)
                    == ("FAB_SPN_CERT_PATH" in os.environ)
                    == ("FAB_SPN_FEDERATED_TOKEN" in os.environ)
                ):
                    raise FabricCLIError(
                        ErrorMessages.Auth.spn_auth_missing_credential(),
                        con.ERROR_AUTHENTICATION_FAILED,
                    )

    def _load_env(self):
        # Validate the environment variables
        self._validate_environment_variables()

        # Check if the environment variables are set
        # Removed usage of user tokens, need to see if this is still needed and if so, how to implement it
        if "FAB_TENANT_ID" in os.environ:
            tenant_id = os.environ["FAB_TENANT_ID"]
            self._verify_valid_guid_parameter(tenant_id, "FAB_TENANT_ID")
            self.set_tenant(tenant_id)

        if "FAB_SPN_CLIENT_ID" in os.environ and "FAB_SPN_CLIENT_SECRET" in os.environ:
            client_id = os.environ["FAB_SPN_CLIENT_ID"]
            self._verify_valid_guid_parameter(client_id, "FAB_SPN_CLIENT_ID")
            self.set_spn(
                os.environ["FAB_SPN_CLIENT_ID"],
                os.environ["FAB_SPN_CLIENT_SECRET"],
            )
        elif "FAB_SPN_CLIENT_ID" in os.environ and "FAB_SPN_CERT_PATH" in os.environ:
            client_id = os.environ["FAB_SPN_CLIENT_ID"]
            self._verify_valid_guid_parameter(client_id, "FAB_SPN_CLIENT_ID")
            cert_path = os.environ["FAB_SPN_CERT_PATH"]
            self._verify_valid_cert_parameter(cert_path, "FAB_SPN_CERT_PATH")
            cert_password = os.environ.get("FAB_SPN_CERT_PASSWORD", None)
            self.set_spn(
                client_id,
                cert_path=cert_path,
                password=cert_password,
            )
        elif (
            "FAB_SPN_CLIENT_ID" in os.environ
            and "FAB_SPN_FEDERATED_TOKEN" in os.environ
        ):
            client_id = os.environ["FAB_SPN_CLIENT_ID"]
            self._verify_valid_guid_parameter(client_id, "FAB_SPN_CLIENT_ID")
            federated_token = os.environ["FAB_SPN_FEDERATED_TOKEN"]
            self.set_spn(client_id, client_assertion=federated_token)
        elif "FAB_MANAGED_IDENTITY" in os.environ and os.environ[
            "FAB_MANAGED_IDENTITY"
        ].lower() in ["true", "1"]:
            client_id = os.environ.get("FAB_SPN_CLIENT_ID", None)
            if client_id:
                self._verify_valid_guid_parameter(client_id, "FAB_SPN_CLIENT_ID")
            self.set_managed_identity(client_id)

    def _get_auth_property(self, key):
        return self._auth_info.get(key, None)

    def _get_auth_info(self):
        return self._auth_info

    def _set_auth_property(self, key, value):
        self._auth_info[key] = value
        self._save_auth()

    def _set_auth_properties(self, properties: dict):
        # Translate any dict values from binary to string
        decoded_properties = self._decode_dict_recursively(properties)
        # Update the auth info with the decoded properties
        self._auth_info.update(decoded_properties)
        self._save_auth()

    def _decode_dict_recursively(self, d: dict) -> dict:
        decoded_dict = {}
        for key, value in d.items():
            if isinstance(value, bytes):
                decoded_dict[key] = value.decode()
            elif isinstance(value, dict):
                decoded_dict[key] = json.dumps(self._decode_dict_recursively(value))
            else:
                decoded_dict[key] = value
        return decoded_dict

    def _get_persistence(self):
        persistence = None
        try:
            persistence = build_encrypted_persistence(self.cache_file)
        except Exception as e:
            fab_logger.log_debug(f"Error using encrypted cache: {e}")

            if config.get_config(con.FAB_ENCRYPTION_FALLBACK_ENABLED) == "true":
                persistence = FilePersistence(self.cache_file)
            else:
                raise FabricCLIError(
                    ErrorMessages.Auth.encrypted_cache_error(),
                    con.ERROR_ENCRYPTION_FAILED,
                )

        return persistence

    def _get_app(self) -> msal.ClientApplication:
        if self.app is None:
            persistence = self._get_persistence()
            self.cache = PersistedTokenCache(persistence)

            if self.get_identity_type() == "managed_identity":
                client_id = self._get_auth_property(con.FAB_SPN_CLIENT_ID)
                if client_id:
                    managed_identity = msal.UserAssignedManagedIdentity(
                        client_id=client_id
                    )
                else:
                    managed_identity = msal.SystemAssignedManagedIdentity()

                self.app = msal.ManagedIdentityClient(
                    managed_identity,
                    http_client=requests.Session(),
                    token_cache=self.cache,
                )
                self._set_auth_properties(
                    {
                        con.IDENTITY_TYPE: "managed_identity",
                    }
                )
            elif self.get_identity_type() == "service_principal":
                self.app = msal.ConfidentialClientApplication(
                    client_id=self._get_auth_property(con.FAB_SPN_CLIENT_ID),
                    authority=self._get_authority_url(),
                    token_cache=self.cache,
                )
                self._set_auth_properties(
                    {
                        con.IDENTITY_TYPE: "service_principal",
                    }
                )
            elif self.get_identity_type() == "user":
                # Load the cache into the MSAL application
                self.app = msal.PublicClientApplication(
                    client_id=con.AUTH_DEFAULT_CLIENT_ID,
                    authority=self._get_authority_url(),
                    token_cache=self.cache,
                    enable_broker_on_windows=True,
                )
                self._set_auth_properties(
                    {
                        con.IDENTITY_TYPE: "user",
                    }
                )
        return self.app

    def _get_access_token_from_env_vars_if_exist(self, scope):
        if "FAB_TOKEN" in os.environ and "FAB_TOKEN_ONELAKE" in os.environ:
            match scope:
                case con.SCOPE_FABRIC_DEFAULT:
                    # this call will validate the token we got from the env var
                    self._decode_jwt_token(
                        os.environ["FAB_TOKEN"], con.FABRIC_TOKEN_AUDIENCE
                    )
                    return os.environ["FAB_TOKEN"]
                case con.SCOPE_ONELAKE_DEFAULT:
                    # this call will validate the token we got from the env var
                    self._decode_jwt_token(
                        os.environ["FAB_TOKEN_ONELAKE"], con.ONELAKE_TOKEN_AUDIENCE
                    )
                    return os.environ["FAB_TOKEN_ONELAKE"]
                case con.SCOPE_AZURE_DEFAULT:
                    # this call will validate the token we got from the env var
                    self._decode_jwt_token(
                        os.environ["FAB_TOKEN_AZURE"], con.AZURE_TOKEN_AUDIENCE
                    )
                    if "FAB_TOKEN_AZURE" in os.environ:
                        return os.environ["FAB_TOKEN_AZURE"]
                    else:
                        raise FabricCLIError(
                            ErrorMessages.Auth.azure_token_required(),
                            con.ERROR_AUTHENTICATION_FAILED,
                        )
                case _:
                    raise FabricCLIError(
                        ErrorMessages.Auth.invalid_scope(scope),
                        status_code=con.ERROR_AUTHENTICATION_FAILED,
                    )

        elif "FAB_TOKEN" in os.environ or "FAB_TOKEN_ONELAKE" in os.environ:
            raise FabricCLIError(
                ErrorMessages.Auth.both_fab_and_onelake_tokens_required(),
                status_code=con.ERROR_AUTHENTICATION_FAILED,
            )

        return None

    def get_tenant(self):
        return Tenant(
            name=self.get_tenant_name(),
            id=self.get_tenant_id(),
        )

    def get_tenant_name(self):
        return "Unknown"

    def get_tenant_id(self):
        return self._get_auth_property(con.FAB_TENANT_ID)

    def get_identity_type(self):
        return self._get_auth_property(con.IDENTITY_TYPE)

    def set_access_mode(self, mode, tenant_id=None):
        if mode not in con.AUTH_KEYS[con.IDENTITY_TYPE]:
            raise FabricCLIError(
                ErrorMessages.Auth.invalid_identity_type(
                    mode, con.AUTH_KEYS[con.IDENTITY_TYPE]
                ),
                status_code=con.ERROR_INVALID_ACCESS_MODE,
            )
        if mode != self.get_identity_type():
            self.logout()
        if tenant_id and self.get_tenant_id() != tenant_id:
            self.set_tenant(tenant_id)
        self._set_auth_property(con.IDENTITY_TYPE, mode)

    def set_tenant(self, tenant_id):
        if tenant_id is not None:
            current_tenant_id = self.get_tenant_id()
            if current_tenant_id is not None and current_tenant_id != tenant_id:
                fab_logger.log_warning(
                    f"Tenant ID already set to {current_tenant_id}."
                    + f" Logout done and Tenant ID set to {tenant_id}."
                )
                self.logout()

            self._set_auth_properties(
                {
                    con.FAB_TENANT_ID: tenant_id,
                }
            )

    def set_spn(self, client_id, password=None, cert_path=None, client_assertion=None):
        persistence = self._get_persistence()
        self.cache = PersistedTokenCache(persistence)

        if cert_path:
            credential = self._parse_certificate(cert_path, password)
        elif client_assertion:
            credential = {
                "client_assertion": client_assertion,
            }
        else:
            credential = password

        self.app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=credential,
            authority=self._get_authority_url(),
            token_cache=self.cache,
        )
        # if the client ID and secret are set and are different, then clear the existing tokens
        if (
            self._get_auth_property(con.FAB_SPN_CLIENT_ID) is not None
            and self._get_auth_property(con.FAB_SPN_CLIENT_ID) != client_id
        ):
            fab_logger.log_warning(
                f"Client ID already set to {self._get_auth_property(con.FAB_SPN_CLIENT_ID)}. Overwriting with {client_id} and clearing the existing auth tokens"
            )
            self.logout()

        auth_properties = {
            con.FAB_SPN_CLIENT_ID: client_id,
            con.IDENTITY_TYPE: "service_principal",
        }
        self._set_auth_properties(auth_properties)

    def set_managed_identity(self, client_id=None):
        persistence = self._get_persistence()
        self.cache = PersistedTokenCache(persistence)
        if client_id:
            managed_identity = msal.UserAssignedManagedIdentity(client_id=client_id)
        else:
            managed_identity = msal.SystemAssignedManagedIdentity()

        self.app = self.app = msal.ManagedIdentityClient(
            managed_identity, http_client=requests.Session(), token_cache=self.cache
        )
        # if the client ID and secret are set and are different, then clear the existing tokens
        if (
            self._get_auth_property(con.FAB_SPN_CLIENT_ID) is not None
            and self._get_auth_property(con.FAB_SPN_CLIENT_ID) != client_id
        ):
            fab_logger.log_warning(
                f"Client ID already set to {self._get_auth_property(con.FAB_SPN_CLIENT_ID)}. Overwriting with {client_id} and clearing the existing auth tokens"
            )
            self.logout()
        self._set_auth_properties(
            {
                con.FAB_SPN_CLIENT_ID: client_id,
                con.IDENTITY_TYPE: "managed_identity",
            }
        )

    def print_auth_info(self):
        utils_ui.print_grey(json.dumps(self._get_auth_info(), indent=2))

    def _is_token_defined(self, scope):
        match scope:
            case con.SCOPE_FABRIC_DEFAULT:
                return con.FAB_TOKEN in self._get_auth_info()
            case con.SCOPE_ONELAKE_DEFAULT:
                return con.FAB_TOKEN_ONELAKE in self._get_auth_info()
            case con.SCOPE_AZURE_DEFAULT:
                return con.FAB_TOKEN_AZURE in self._get_auth_info()
            case _:
                raise FabricCLIError(
                    ErrorMessages.Auth.invalid_scope(scope),
                    status_code=con.ERROR_AUTHENTICATION_FAILED,
                )

    def get_access_token(self, scope: list[str], interactive_renew=True) -> str:
        token = None
        env_var_token = self._get_access_token_from_env_vars_if_exist(scope)

        identity_type = self.get_identity_type()

        if identity_type == "service_principal":
            token = self._get_app().acquire_token_for_client(scopes=scope)

        elif identity_type == "managed_identity":
            # remove the .default from the scope
            resource = scope[0].replace("/.default", "")
            try:
                token = self._get_app().acquire_token_for_client(resource=resource)

            except ConnectionError:
                raise FabricCLIError(
                    ErrorMessages.Auth.managed_identity_connection_failed(),
                    status_code=con.ERROR_AUTHENTICATION_FAILED,
                )
            except Exception:
                raise FabricCLIError(
                    ErrorMessages.Auth.managed_identity_token_failed(),
                    status_code=con.ERROR_AUTHENTICATION_FAILED,
                )
        elif env_var_token:
            token = {
                "access_token": env_var_token,
            }
        elif identity_type == "user":
            # Use the cache to get the token
            accounts = self._get_app().get_accounts()
            account = None
            if accounts:
                account = accounts[0]
            token = self._get_app().acquire_token_silent(scopes=scope, account=account)

            if token is None and interactive_renew and identity_type == "user":
                token = self._get_app().acquire_token_interactive(
                    scopes=scope,
                    prompt="select_account",
                    parent_window_handle=msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE,
                )
                if token is not None and "id_token_claims" in token:
                    self.set_tenant(token.get("id_token_claims")["tid"])

        if token and token.get("error"):
            raise FabricCLIError(
                ErrorMessages.Auth.access_token_error(token.get("error_description")),
                status_code=con.ERROR_AUTHENTICATION_FAILED,
            )
        if token is None or not token.get("access_token"):
            raise FabricCLIError(
                ErrorMessages.Auth.access_token_error(),
                status_code=con.ERROR_AUTHENTICATION_FAILED,
            )

        return token.get("access_token", None)

    def logout(self):
        self._auth_info = {}

        self.app = None

        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

        self._save_auth()

        # Reset to default values
        config.set_config(
            con.FAB_CACHE_ENABLED, con.CONFIG_DEFAULT_VALUES[con.FAB_CACHE_ENABLED]
        )
        config.set_config(
            con.FAB_DEBUG_ENABLED, con.CONFIG_DEFAULT_VALUES[con.FAB_DEBUG_ENABLED]
        )
        config.set_config(
            con.FAB_SHOW_HIDDEN, con.CONFIG_DEFAULT_VALUES[con.FAB_SHOW_HIDDEN]
        )
        config.set_config(
            con.FAB_JOB_CANCEL_ONTIMEOUT,
            con.CONFIG_DEFAULT_VALUES[con.FAB_JOB_CANCEL_ONTIMEOUT],
        )
        config.set_config(
            con.FAB_DEFAULT_OPEN_EXPERIENCE,
            con.CONFIG_DEFAULT_VALUES[con.FAB_DEFAULT_OPEN_EXPERIENCE],
        )

        # Reset settings
        config.set_config(con.FAB_LOCAL_DEFINITION_LABELS, "")
        config.set_config(con.FAB_DEFAULT_CAPACITY, "")
        config.set_config(con.FAB_DEFAULT_CAPACITY_ID, "")

        # Reset Azure settings
        config.set_config(con.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, "")
        config.set_config(con.FAB_DEFAULT_AZ_ADMIN, "")
        config.set_config(con.FAB_DEFAULT_AZ_RESOURCE_GROUP, "")
        config.set_config(con.FAB_DEFAULT_AZ_LOCATION, "")

    def get_token_claims(
        self, scope: list[str], claim_names: list[str]
    ) -> Optional[dict[str, str]]:
        token = self.get_access_token(scope, interactive_renew=False)
        return self._get_claims_from_token(token, claim_names)

    def _fetch_public_key_from_aad(self, token):
        jwks_url = f"{self._get_authority_url()}/discovery/v2.0/keys"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        public_keys = {}
        for jwk in jwks["keys"]:
            kid = jwk["kid"]
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        key = public_keys.get(unverified_header["kid"])
        if key is None:
            raise FabricCLIError(
                ErrorMessages.Auth.public_key_not_found(),
                con.ERROR_AUTHENTICATION_FAILED,
            )
        return key

    def _decode_jwt_token(self, token, expected_audience=None):
        decode_options = {"verify_aud": expected_audience is not None}
        # Try using the cached public key if available
        if self.aad_public_key is not None:
            try:
                payload = jwt.decode(
                    token,
                    key=self.aad_public_key,
                    algorithms=["RS256"],
                    audience=expected_audience,
                    options=decode_options,
                )
                return payload
            except Exception as e:
                fab_logger.log_debug(
                    f"JWT decode error with cached key: {e}. Fetching new key..."
                )
        try:
            key = self._fetch_public_key_from_aad(token)
            payload = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=expected_audience,
                options=decode_options,
            )
        except Exception as e:
            fab_logger.log_debug(f"JWT decode error: {e}")
            raise FabricCLIError(
                ErrorMessages.Auth.jwt_decode_failed(),
                con.ERROR_AUTHENTICATION_FAILED,
            )
        # Cache the new key for future use
        self.aad_public_key = key
        return payload

    def _get_claims_from_token(self, token, claim_names) -> Optional[dict[str, str]]:
        """Get multiple claims from the token with a single decode operation"""
        payload = self._decode_jwt_token(token)
        claims = {
            claim_name: payload.get(claim_name)
            for claim_name in claim_names
            if payload.get(claim_name) is not None
        }
        return claims or None

    @staticmethod
    def _verify_valid_guid_parameter(parameter_value, parameter_name):
        try:
            uuid.UUID(parameter_value)
        except ValueError:
            raise FabricCLIError(
                ErrorMessages.Common.invalid_guid(parameter_name),
                status_code=con.ERROR_INVALID_GUID,
            )

    @staticmethod
    def _verify_valid_cert_parameter(parameter_value, parameter_name):
        if not os.path.exists(parameter_value):
            raise FabricCLIError(
                ErrorMessages.Auth.invalid_cert_path(parameter_name),
                status_code=con.ERROR_INVALID_CERTIFICATE_PATH,
            )
        if not os.path.isfile(parameter_value):
            raise FabricCLIError(
                ErrorMessages.Auth.invalid_cert_path(parameter_name),
                status_code=con.ERROR_INVALID_CERTIFICATE_PATH,
            )
        if (
            not parameter_value.endswith(".pem")
            and not parameter_value.endswith(".pfx")
            and not parameter_value.endswith(".p12")
        ):
            raise FabricCLIError(
                ErrorMessages.Auth.invalid_cert_format(parameter_name),
                status_code=con.ERROR_INVALID_CERTIFICATE,
            )

    @staticmethod
    def _verify_jwt_token(token: str, verify_signature: bool = False) -> None:
        try:
            jwt.decode(
                token,
                options={"verify_signature": verify_signature},
            )
        except jwt.InvalidTokenError:
            raise FabricCLIError(
                ErrorMessages.Auth.invalid_jwt_token(),
                status_code=con.ERROR_AUTHENTICATION_FAILED,
            )

    def _parse_certificate(
        self, cert_file_path: str, password: str | None = None
    ) -> dict:
        """
        Parses a certificate file and returns its content as a json with three properties: private_key, thumbprint, passphrase.
        Ref: https://learn.microsoft.com/en-us/python/api/msal/msal.application.confidentialclientapplication?view=msal-py-latest
        :param cert_file_path: Path to the certificate file.
        :return: Content of the certificate file as a dict.
        """
        try:
            with open(cert_file_path, "rb") as cert_file:
                cert_content = cert_file.read()
                if cert_file_path.endswith(".pfx") or cert_file_path.endswith(".p12"):
                    # PKCS12 format
                    cert = self._load_pkcs12_certificate(
                        cert_content, password.encode() if password else None
                    )
                elif cert_file_path.endswith(".pem"):
                    # PEM format
                    cert = self._load_pem_certificate(
                        cert_content, password.encode() if password else None
                    )
                else:
                    raise FabricCLIError(
                        ErrorMessages.Auth.invalid_cert_file_format(),
                        con.ERROR_INVALID_CERTIFICATE,
                    )
                client_credential = {
                    "private_key": cert.pem_bytes,
                    "thumbprint": hexlify(cert.fingerprint).decode("utf-8"),
                }
                return client_credential
        except Exception as e:
            raise FabricCLIError(
                ErrorMessages.Auth.cert_read_failed(str(e)),
                con.ERROR_INVALID_CERTIFICATE,
            )

    _Cert = NamedTuple(
        "_Cert", [("pem_bytes", bytes), ("private_key", "Any"), ("fingerprint", bytes)]
    )

    def _load_pem_certificate(
        self, certificate_data: bytes, password: Optional[bytes] = None
    ) -> _Cert:
        private_key = serialization.load_pem_private_key(
            certificate_data, password, backend=default_backend()
        )
        cert = x509.load_pem_x509_certificate(certificate_data, default_backend())
        fingerprint = cert.fingerprint(hashes.SHA256())
        return self._Cert(certificate_data, private_key, fingerprint)

    def _load_pkcs12_certificate(
        self, certificate_data: bytes, password: Optional[bytes] = None
    ) -> _Cert:
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            pkcs12,
        )

        try:
            private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
                certificate_data, password, backend=default_backend()
            )
        except ValueError as ex:
            # mentioning PEM here because we raise this error when certificate_data is garbage
            raise ValueError(
                "Failed to deserialize certificate in PEM or PKCS12 format"
            ) from ex
        if not private_key:
            raise ValueError("The certificate must include its private key")
        if not cert:
            raise ValueError(
                "Failed to deserialize certificate in PEM or PKCS12 format"
            )

        # This serializes the private key without any encryption it may have had. Doing so doesn't violate security
        # boundaries because this representation of the key is kept in memory. We already have the key and its
        # password, if any, in memory.
        key_bytes = private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        )
        pem_sections = [key_bytes] + [
            c.public_bytes(Encoding.PEM) for c in [cert] + additional_certs
        ]
        pem_bytes = b"".join(pem_sections)

        fingerprint = cert.fingerprint(hashes.SHA256())

        return self._Cert(pem_bytes, private_key, fingerprint)

    def _get_authority_url(self):
        tenant_id = self.get_tenant_id()
        if tenant_id is None:
            return con.AUTH_DEFAULT_AUTHORITY
        return f"{con.AUTH_TENANT_AUTHORITY}{tenant_id}"
