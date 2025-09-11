# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Optional


class AuthErrors:
    @staticmethod
    def spn_auth_missing_tenant_id() -> str:
        return "Tenant ID is required for Service Principal authentication"

    @staticmethod
    def spn_auth_missing_client_id() -> str:
        return "Client ID is required for Service Principal authentication"

    @staticmethod
    def spn_auth_missing_client_secret() -> str:
        return (
            "Client secret is required for Service Principal authentication with secret"
        )

    @staticmethod
    def spn_auth_missing_cert_path() -> str:
        return "Certificate path is required for Service Principal authentication with certificate"

    @staticmethod
    def spn_auth_missing_federated_token() -> str:
        return "Federated token is required for Service Principal authentication with federated credential"

    @staticmethod
    def managed_identity_incompatible_vars() -> str:
        return "FAB_MANAGED_IDENTITY enabled is incompatible with FAB_SPN_CLIENT_SECRET, FAB_SPN_CERT_PATH, or FAB_SPN_FEDERATED_TOKEN"

    @staticmethod
    def spn_auth_missing_credential() -> str:
        return "Authentication credential is missing. Either FAB_SPN_CLIENT_SECRET, FAB_SPN_CERT_PATH or FAB_SPN_FEDERATED_TOKEN must be set"

    @staticmethod
    def encrypted_cache_error() -> str:
        return "An error occurred with the encrypted cache. Enable plaintext auth token fallback with 'config set encryption_fallback_enabled true'"

    @staticmethod
    def azure_token_required() -> str:
        return "Azure authentication token is required. You must set FAB_TOKEN_AZURE for operations against Azure APIs"

    @staticmethod
    def tenant_id_env_var_required() -> str:
        return "FAB_TENANT_ID must be set for SPN authentication"

    @staticmethod
    def public_key_not_found() -> str:
        return "Public key not found in JWKS"

    @staticmethod
    def invalid_scope(scope: str) -> str:
        return f"Invalid scope '{scope}'"

    @staticmethod
    def both_fab_and_onelake_tokens_required() -> str:
        return "Both FAB_TOKEN and FAB_TOKEN_ONELAKE are required"

    @staticmethod
    def invalid_identity_type(identity_type: str, allowed_values: list) -> str:
        return f"The identity type '{identity_type}' is invalid. Allowed values are: {allowed_values}"

    @staticmethod
    def managed_identity_connection_failed() -> str:
        return "Failed to connect to the managed identity service"

    @staticmethod
    def managed_identity_token_failed() -> str:
        return "Failed to acquire token for managed identity"

    @staticmethod
    def access_token_error(error_description: Optional[str] = None) -> str:
        return (
            f"Failed to get access token: {error_description}"
            if error_description
            else "Failed to get access token"
        )

    @staticmethod
    def access_token_failed() -> str:
        return "Failed to obtain access token"

    @staticmethod
    def jwt_decode_failed() -> str:
        return "Failed to decode JWT token"

    @staticmethod
    def invalid_cert_path(parameter_name: str) -> str:
        return f"The parameter '{parameter_name}' must be a valid path to a certificate file"

    @staticmethod
    def invalid_cert_format(parameter_name: str) -> str:
        return f"The parameter '{parameter_name}' must be a valid path to a PEM or PKCS12 certificate file"

    @staticmethod
    def invalid_jwt_token() -> str:
        return "Invalid JWT token"

    @staticmethod
    def invalid_cert_file_format() -> str:
        return "The certificate file format is invalid. It must be in PEM (.pem) or PKCS12 (.pfx or .p12) format"

    @staticmethod
    def cert_read_failed(error: str) -> str:
        return f"Failed to read certificate file: {error}"

    @staticmethod
    def only_supported_with_user_authentication() -> str:
        return "This operation is only supported with user authentication"
