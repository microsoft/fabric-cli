# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import datetime
import json
import os
import tempfile
import uuid
from unittest.mock import patch

import jwt
import pytest
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from fabric_cli.core import fab_constant as con
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError


@pytest.fixture(autouse=True)
def temp_dir_fixture(monkeypatch, tmp_path):
    """Create a temporary directory and configure FabAuth to use it"""
    monkeypatch.setattr(
        "fabric_cli.core.fab_state_config.config_location", lambda: str(tmp_path)
    )
    return str(tmp_path)


DUMMY_TOKEN = "dummy.token.value"
DUMMY_PAYLOAD = {"sub": "123", "aud": "test_audience"}
DUMMY_KEY_VALID = "dummy_key_valid"
DUMMY_KEY_INVALID = "dummy_key_invalid"


def _clear_environment_variables(monkeypatch):
    monkeypatch.delenv("FAB_TENANT_ID", raising=False)
    monkeypatch.delenv("FAB_SPN_CLIENT_ID", raising=False)
    monkeypatch.delenv("FAB_SPN_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("FAB_SPN_CERT_PATH", raising=False)
    monkeypatch.delenv("FAB_SPN_CERT_PASSWORD", raising=False)
    monkeypatch.delenv("FAB_TOKEN", raising=False)
    monkeypatch.delenv("FAB_TOKEN_ONELAKE", raising=False)
    monkeypatch.delenv("FAB_TOKEN_AZURE", raising=False)
    monkeypatch.delenv("FAB_MANAGED_IDENTITY", raising=False)


def _generate_test_certificate(format_type="pem", password=None):
    """Generate a test certificate and private key for testing purposes

    Args:
        format_type (str): Certificate format - "pem" or "pfx"/"pkcs12"
        password (str, optional): Password to encrypt the private key

    Returns:
        bytes: Certificate data in the specified format
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "TestState"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "TestCity"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TestOrg"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )

    # Determine encryption algorithm
    if password:
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
    else:
        encryption_algorithm = serialization.NoEncryption()

    # Serialize based on requested format
    if format_type.lower() == "pem":
        # PEM format: combine private key and certificate
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm,
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        return private_key_pem + cert_pem

    elif format_type.lower() in ["pfx", "pkcs12"]:
        # PKCS12/PFX format
        return pkcs12.serialize_key_and_certificates(
            name=b"test-cert",
            key=private_key,
            cert=cert,
            cas=None,
            encryption_algorithm=encryption_algorithm,
        )
    else:
        raise ValueError(f"Unsupported certificate format: {format_type}")


def test_load_pem_certificate(monkeypatch):
    # This test is to check if the function loads the certificate correctly
    # Generate test certificate programmatically
    cert_data = _generate_test_certificate()

    # Create a temporary file with the certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".pem", delete=False
    ) as temp_file:
        temp_file.write(cert_data)
        cert_path = temp_file.name

    try:
        cert_password = None
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        cert = auth._parse_certificate(cert_path, cert_password)
        assert "private_key" in cert
        assert "thumbprint" in cert
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_load_pem_certificate_invalid(monkeypatch):
    # This test is to check if the function raises an error when loading an invalid certificate
    # Create an invalid certificate file (just a private key without certificate part)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Only include private key, no certificate part (this makes it invalid)
    invalid_cert_data = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Create a temporary file with the invalid certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".pem", delete=False
    ) as temp_file:
        temp_file.write(invalid_cert_data)
        cert_path = temp_file.name

    try:
        cert_password = None
        expected_exception = FabricCLIError(
            status_code=con.ERROR_INVALID_CERTIFICATE,
            message="Failed to read certificate file: Valid PEM but no BEGIN CERTIFICATE/END CERTIFICATE delimiters. Are you sure this is a certificate?",
        )
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        with pytest.raises(FabricCLIError) as e:
            auth._parse_certificate(cert_path, cert_password)
        assert e.value.status_code == expected_exception.status_code
        assert e.value.message == expected_exception.message
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_load_pem_certificate_with_password(monkeypatch):
    # This test is to check if the function loads the certificate correctly with password
    # Generate test certificate with password programmatically
    cert_password = "abcd"
    cert_data = _generate_test_certificate(password=cert_password)

    # Create a temporary file with the certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".pem", delete=False
    ) as temp_file:
        temp_file.write(cert_data)
        cert_path = temp_file.name

    try:
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        cert = auth._parse_certificate(cert_path, cert_password)
        assert "private_key" in cert
        assert "thumbprint" in cert
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_load_pem_certificate_with_invalid_password(monkeypatch):
    # This test is to check if the function raises an error when loading the certificate with an invalid password
    # Generate test certificate without password programmatically
    cert_data = _generate_test_certificate()  # No password

    # Create a temporary file with the certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".pem", delete=False
    ) as temp_file:
        temp_file.write(cert_data)
        cert_path = temp_file.name

    try:
        cert_password = "invalid_password"
        expected_exception = FabricCLIError(
            status_code=con.ERROR_INVALID_CERTIFICATE,
            message="Failed to read certificate file: Password was given but private key is not encrypted.",
        )
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        with pytest.raises(FabricCLIError) as e:
            auth._parse_certificate(cert_path, cert_password)
        assert e.value.status_code == expected_exception.status_code
        assert e.value.message == expected_exception.message
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_load_pem_certificate_with_invalid_path(monkeypatch):
    # This test is to check if the function raises an error when loading the certificate with an invalid path
    cert_path = "invalid_path/sample_cert.pem"
    cert_password = None
    excepted_exception = FabricCLIError(
        status_code=con.ERROR_INVALID_CERTIFICATE,
        message="Failed to read certificate file: [Errno 2] No such file or directory: 'invalid_path/sample_cert.pem'",
    )
    # Clear environment variables
    _clear_environment_variables(monkeypatch)
    auth = FabAuth()
    with pytest.raises(FabricCLIError) as e:
        auth._parse_certificate(cert_path, cert_password)
    assert str(e.value.status_code) == excepted_exception.status_code
    assert e.value.message == excepted_exception.message


def test_load_pfx_certificate(monkeypatch):
    # This test is to check if the function loads the certificate correctly
    # Generate test PFX certificate programmatically
    cert_data = _generate_test_certificate(format_type="pfx")

    # Create a temporary file with the certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".pfx", delete=False
    ) as temp_file:
        temp_file.write(cert_data)
        cert_path = temp_file.name

    try:
        cert_password = None
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        cert = auth._parse_certificate(cert_path, cert_password)
        assert "private_key" in cert
        assert "thumbprint" in cert
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_load_pfx_certificate_with_password(monkeypatch):
    # This test is to check if the function loads the certificate correctly with password
    # Generate test PFX certificate with password programmatically
    cert_password = "abcd"
    cert_data = _generate_test_certificate(format_type="pfx", password=cert_password)

    # Create a temporary file with the certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".p12", delete=False
    ) as temp_file:
        temp_file.write(cert_data)
        cert_path = temp_file.name

    try:
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        cert = auth._parse_certificate(cert_path, cert_password)
        assert "private_key" in cert
        assert "thumbprint" in cert
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_load_pfx_certificate_with_invalid_password(monkeypatch):
    # This test is to check if the function raises an error when loading the certificate with an invalid password
    # Generate test PFX certificate with a specific password programmatically
    correct_password = "correct_password"
    cert_data = _generate_test_certificate(format_type="pfx", password=correct_password)

    # Create a temporary file with the certificate
    with tempfile.NamedTemporaryFile(
        mode="w+b", suffix=".pfx", delete=False
    ) as temp_file:
        temp_file.write(cert_data)
        cert_path = temp_file.name

    try:
        cert_password = "invalid_password"  # Wrong password
        expected_exception = FabricCLIError(
            status_code=con.ERROR_INVALID_CERTIFICATE,
            message="Failed to read certificate file: Failed to deserialize certificate in PEM or PKCS12 format",
        )
        # Clear environment variables
        _clear_environment_variables(monkeypatch)
        auth = FabAuth()
        with pytest.raises(FabricCLIError) as e:
            auth._parse_certificate(cert_path, cert_password)
        assert e.value.status_code == expected_exception.status_code
        assert e.value.message == expected_exception.message
    finally:
        # Clean up temporary file
        os.remove(cert_path)


def test_get_access_token_user_silent_success():
    auth = FabAuth()
    auth._auth_info = {con.IDENTITY_TYPE: "user"}
    expected_token = "silent_token"

    with (
        patch.object(auth, "set_tenant", wraps=auth.set_tenant) as set_tenant_spy,
        patch.object(auth, "app", wraps=auth.app) as mock_app,
    ):

        mock_app.acquire_token_silent.return_value = {"access_token": expected_token}
        token = auth.get_access_token([con.SCOPE_FABRIC_DEFAULT])
        assert token == expected_token
        set_tenant_spy.assert_not_called()


def test_get_access_token_user_interactive_error_response_failure():
    auth = FabAuth()
    auth._auth_info = {con.IDENTITY_TYPE: "user"}

    with (
        patch.object(auth, "set_tenant", wraps=auth.set_tenant) as set_tenant_spy,
        patch.object(auth, "app", wraps=auth.app) as mock_app,
    ):

        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_interactive.return_value = {
            "error": "token acquisition failed"
        }

        with pytest.raises(FabricCLIError) as context:
            auth.get_access_token([con.SCOPE_FABRIC_DEFAULT])
        set_tenant_spy.assert_not_called()
        mock_app.acquire_token_interactive.assert_called()


def test_get_access_token_user_interactive_success():
    auth = FabAuth()
    auth._auth_info = {con.IDENTITY_TYPE: "user"}
    expected_tenant = "tenant_id"
    expected_token = "interactive_token"

    with (
        patch.object(auth, "set_tenant", wraps=auth.set_tenant) as set_tenant_spy,
        patch.object(auth, "app", wraps=auth.app) as mock_app,
    ):

        set_tenant_spy.configure_mock(**{"return_value": None})

        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_interactive.return_value = {
            "access_token": expected_token,
            "id_token_claims": {"tid": expected_tenant},
        }

        token = auth.get_access_token([con.SCOPE_FABRIC_DEFAULT])
        assert token == expected_token
        set_tenant_spy.assert_called_with(expected_tenant)


def test_validate_jwt_token_success():
    # Build a valid JWT token
    # This is a mock token for testing purposes
    payload = {
        "aud": "https://example.com",
        "iss": "https://example.com",
        "exp": 1700000000,
        "nbf": 1600000000,
        "iat": 1600000000,
        "sub": "1234567890",
    }
    key = "mykey"
    token = jwt.encode(payload, key)
    # Decode the token
    auth = FabAuth()
    auth._verify_jwt_token(token)


def test_validate_jwt_token_invalid():
    # Build an invalid JWT token
    token = "InvalidToken"
    # Decode the token
    with pytest.raises(FabricCLIError) as e:
        auth = FabAuth()
        auth._verify_jwt_token(token)

    assert e.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert e.value.message == "Invalid JWT token"


def test_validate_jwt_token_empty():
    # Build an invalid JWT token
    token = ""
    # Decode the token
    with pytest.raises(FabricCLIError) as e:
        auth = FabAuth()
        auth._verify_jwt_token(token)

    assert e.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert e.value.message == "Invalid JWT token"


def test_decode_jwt_token_with_cached_key_success(monkeypatch):
    auth = FabAuth()
    # Set a valid cached key
    auth.aad_public_key = DUMMY_KEY_VALID

    # Patch jwt.decode to simulate successful decoding with cached key
    def fake_jwt_decode(token, key, algorithms, audience, options):
        assert token == DUMMY_TOKEN
        assert key == DUMMY_KEY_VALID
        assert algorithms == ["RS256"]
        assert audience == "test_audience"
        return DUMMY_PAYLOAD

    monkeypatch.setattr(jwt, "decode", fake_jwt_decode)

    payload = auth._decode_jwt_token(DUMMY_TOKEN, expected_audience="test_audience")
    assert payload == DUMMY_PAYLOAD


def test_decode_jwt_token_with_cached_key_failure_then_fetch(monkeypatch):
    auth = FabAuth()
    # Set an invalid cached key so that the first attempt fails
    auth.aad_public_key = DUMMY_KEY_INVALID

    call_history = {"decode_calls": []}

    # Create a fake jwt.decode which raises an exception when called with the invalid key,
    # but succeeds when called with the valid key.
    def fake_jwt_decode(token, key, algorithms, audience, options):
        call_history["decode_calls"].append(key)
        if key == DUMMY_KEY_INVALID:
            raise Exception("Invalid cached key")
        elif key == DUMMY_KEY_VALID:
            return DUMMY_PAYLOAD
        else:
            raise Exception("Unexpected key used")

    monkeypatch.setattr(jwt, "decode", fake_jwt_decode)

    # Patch _fetch_public_key_from_aad to return a new valid key
    def fake_fetch_public_key(token):
        assert token == DUMMY_TOKEN
        return DUMMY_KEY_VALID

    monkeypatch.setattr(auth, "_fetch_public_key_from_aad", fake_fetch_public_key)

    payload = auth._decode_jwt_token(DUMMY_TOKEN, expected_audience="test_audience")
    # Verify that the cached key was replaced with the new valid key
    assert auth.aad_public_key == DUMMY_KEY_VALID
    assert payload == DUMMY_PAYLOAD
    # Ensure that jwt.decode was first called with the invalid key, then with the fetched key
    assert call_history["decode_calls"] == [DUMMY_KEY_INVALID, DUMMY_KEY_VALID]


def test_decode_jwt_token_failure_after_fetch(monkeypatch):
    auth = FabAuth()
    auth.aad_public_key = None  # No cached key

    # Patch _fetch_public_key_from_aad to return a valid key
    def fake_fetch_public_key(token):
        return DUMMY_KEY_VALID

    monkeypatch.setattr(auth, "_fetch_public_key_from_aad", fake_fetch_public_key)

    # Patch jwt.decode to always raise an Exception even with the fetched key
    def fake_jwt_decode(token, key, algorithms, audience, options):
        raise Exception("Decoding failed with new key")

    monkeypatch.setattr(jwt, "decode", fake_jwt_decode)

    with pytest.raises(FabricCLIError) as exc_info:
        auth._decode_jwt_token(DUMMY_TOKEN, expected_audience="test_audience")
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Failed to decode JWT token" in str(exc_info.value)


def fake_response_success(jwks):
    class FakeResponse:
        def json(self):
            return jwks

    return FakeResponse()


def test_fetch_public_key_success(monkeypatch):
    auth = FabAuth()
    # Setup a fake JWKS response with one key
    fake_kid = "kid1"
    fake_jwk = {
        "kid": fake_kid,
        "kty": "RSA",
        "n": "dummy_n",
        "e": "dummy_e",
        "alg": "RS256",
        "use": "sig",
    }
    jwks = {"keys": [fake_jwk]}

    # Patch requests.get to return our fake JWKS
    monkeypatch.setattr(requests, "get", lambda url: fake_response_success(jwks))
    # Patch jwt.get_unverified_header to return a header with our fake kid
    monkeypatch.setattr(jwt, "get_unverified_header", lambda token: {"kid": fake_kid})
    # Patch jwt.algorithms.RSAAlgorithm.from_jwk to simply return the JSON string of the jwk for testing
    monkeypatch.setattr(
        jwt.algorithms.RSAAlgorithm, "from_jwk", lambda jwk_str: json.loads(jwk_str)
    )

    key = auth._fetch_public_key_from_aad(DUMMY_TOKEN)
    # The returned key should be equal to the fake_jwk dictionary
    assert key == fake_jwk


def test_fetch_public_key_not_found(monkeypatch):
    auth = FabAuth()
    # Setup a fake JWKS response with a key that doesn't match
    fake_kid = "expected_kid"
    fake_jwk = {
        "kid": "other_kid",
        "kty": "RSA",
        "n": "dummy_n",
        "e": "dummy_e",
        "alg": "RS256",
        "use": "sig",
    }
    jwks = {"keys": [fake_jwk]}

    # Patch requests.get to return our fake JWKS
    monkeypatch.setattr(requests, "get", lambda url: fake_response_success(jwks))
    # Patch jwt.get_unverified_header to return a header with a kid that is not available in JWKS
    monkeypatch.setattr(jwt, "get_unverified_header", lambda token: {"kid": fake_kid})
    # Patch jwt.algorithms.RSAAlgorithm as before
    monkeypatch.setattr(
        jwt.algorithms.RSAAlgorithm, "from_jwk", lambda jwk_str: json.loads(jwk_str)
    )

    with pytest.raises(FabricCLIError) as exc_info:
        auth._fetch_public_key_from_aad(DUMMY_TOKEN)
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Public key not found in JWKS" in str(exc_info.value.message)


def test_get_token_claim_success(monkeypatch):
    dummy_scope = ["dummy_scope"]
    dummy_claim_name = "sub"
    dummy_token = "dummy_token_for_claim"
    dummy_payload = {"sub": "expected_claim", "aud": "dummy_aud"}

    _clear_environment_variables(monkeypatch)
    auth = FabAuth()

    # Patch get_access_token to return a dummy token.
    monkeypatch.setattr(
        auth, "get_access_token", lambda scope, interactive_renew=False: dummy_token
    )
    # Patch _decode_jwt_token to return our dummy payload.
    monkeypatch.setattr(
        auth,
        "_decode_jwt_token",
        lambda token, expected_audience=None: (
            dummy_payload if token == dummy_token else {}
        ),
    )

    result = auth.get_token_claims(dummy_scope, [dummy_claim_name])
    assert result == {"sub": "expected_claim"}


def test_get_token_claim_missing_claim(monkeypatch):
    dummy_scope = ["dummy_scope"]
    dummy_claim_name = "nonexistent"
    dummy_token = "dummy_token"
    dummy_payload = {"sub": "someone", "aud": "dummy_aud"}

    _clear_environment_variables(monkeypatch)
    auth = FabAuth()

    monkeypatch.setattr(
        auth, "get_access_token", lambda scope, interactive_renew=False: dummy_token
    )
    monkeypatch.setattr(
        auth, "_decode_jwt_token", lambda token, expected_audience=None: dummy_payload
    )

    result = auth.get_token_claims(dummy_scope, [dummy_claim_name])
    assert result is None


# -----------------------------
# Service Principal Mode Tests
# -----------------------------
def test_get_access_token_service_principal(monkeypatch):
    auth = FabAuth()
    # Force auth mode to service_principal
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: (
            "service_principal" if key == con.IDENTITY_TYPE else "dummy_authority"
        ),
    )

    # Fake app with acquire_token_for_client method returning valid token
    class FakeApp:
        def acquire_token_for_client(self, *, scopes):
            return {"access_token": "sp_token"}

    monkeypatch.setattr(auth, "_get_app", lambda: FakeApp())
    token = auth.get_access_token(["dummy_scope"])
    assert token == "sp_token"


# -----------------------------
# Managed Identity Mode Tests
# -----------------------------
def test_get_access_token_managed_identity_success(monkeypatch):
    auth = FabAuth()
    # Force auth mode to managed_identity
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: (
            "managed_identity" if key == con.IDENTITY_TYPE else "dummy_authority"
        ),
    )

    # Fake app with acquire_token_for_client method returning valid token
    class FakeMIApp:
        def acquire_token_for_client(self, *, resource):
            return {"access_token": "mi_token"}

    monkeypatch.setattr(auth, "_get_app", lambda: FakeMIApp())
    # Pass a scope with '/.default' which will have it removed
    token = auth.get_access_token(["dummy_scope/.default"])
    assert token == "mi_token"


def test_get_access_token_managed_identity_connection_error(monkeypatch):
    auth = FabAuth()
    # Force auth mode to managed_identity
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: (
            "managed_identity" if key == con.IDENTITY_TYPE else "dummy_authority"
        ),
    )

    # Fake app that raises ConnectionError when trying to acquire token
    class FakeMIApp:
        def acquire_token_for_client(self, *, resource):
            raise ConnectionError("Connection failed")

    monkeypatch.setattr(auth, "_get_app", lambda: FakeMIApp())
    with pytest.raises(FabricCLIError) as exc_info:
        auth.get_access_token(["dummy_scope/.default"])
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Failed to connect to the managed identity service" in str(exc_info.value)


def test_get_access_token_managed_identity_generic_exception(monkeypatch):
    auth = FabAuth()
    # Force auth mode to managed_identity
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: (
            "managed_identity" if key == con.IDENTITY_TYPE else "dummy_authority"
        ),
    )

    # Fake app that raises a generic Exception
    class FakeMIApp:
        def acquire_token_for_client(self, *, resource):
            raise Exception("Other failure")

    monkeypatch.setattr(auth, "_get_app", lambda: FakeMIApp())
    with pytest.raises(FabricCLIError) as exc_info:
        auth.get_access_token(["dummy_scope/.default"])
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Failed to acquire token for managed identity" in str(exc_info.value.message)


# -----------------------------
# Environment Variable Tests
# -----------------------------
def test_get_access_token_env_var(monkeypatch):
    auth = FabAuth()
    # Let _get_auth_property return a mode that falls into the env var branch
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: None if key == con.IDENTITY_TYPE else "dummy_authority",
    )
    # Patch _get_access_token_from_env_vars_if_exist to return a token string
    monkeypatch.setattr(
        auth, "_get_access_token_from_env_vars_if_exist", lambda scope: "env_token"
    )
    token = auth.get_access_token(["dummy_scope"])
    assert token == "env_token"


# -----------------------------
# User Mode Tests
# -----------------------------
def test_get_access_token_user_interactive(monkeypatch):
    auth = FabAuth()
    # Force auth mode to user
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: "user" if key == con.IDENTITY_TYPE else "dummy_authority",
    )

    # Fake app that returns empty accounts and fails silent acquisition
    class FakeUserApp:
        def get_accounts(self):
            return []

        def acquire_token_silent(self, *, scopes, account):
            return None

        def acquire_token_interactive(self, *, scopes, prompt, parent_window_handle):
            return {
                "access_token": "user_token_interactive",
                "id_token_claims": {"tid": "new_tenant"},
            }

    monkeypatch.setattr(auth, "_get_app", lambda: FakeUserApp())
    # Patch set_tenant to simply record the tenant (we could override it and check the value)
    tenant_holder = {}

    def fake_set_tenant(tenant_id):
        tenant_holder["tid"] = tenant_id

    monkeypatch.setattr(auth, "set_tenant", fake_set_tenant)
    token = auth.get_access_token(["dummy_scope"], interactive_renew=True)
    assert token == "user_token_interactive"
    assert tenant_holder.get("tid") == "new_tenant"


# -----------------------------
# Failure Cases Tests
# -----------------------------
def test_get_access_token_no_token(monkeypatch):
    auth = FabAuth()
    # Return a mode so that none of the branches produce valid token
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: "user" if key == con.IDENTITY_TYPE else "dummy_authority",
    )

    # Fake app that returns empty accounts and silent returns None, and interactive is disabled.
    class FakeUserApp:
        def get_accounts(self):
            return []

        def acquire_token_silent(self, *, scopes, account):
            return None

    monkeypatch.setattr(auth, "_get_app", lambda: FakeUserApp())
    with pytest.raises(FabricCLIError) as exc_info:
        auth.get_access_token(["dummy_scope"], interactive_renew=False)
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Failed to get access token" in str(exc_info.value)


def test_get_access_token_token_error(monkeypatch):
    auth = FabAuth()
    # Force auth mode to service_principal
    monkeypatch.setattr(
        auth,
        "_get_auth_property",
        lambda key: (
            "service_principal" if key == con.IDENTITY_TYPE else "dummy_authority"
        ),
    )

    # Fake app returns token with an error field
    class FakeApp:
        def acquire_token_for_client(self, *, scopes):
            return {"error": "some_error", "error_description": "failed due to error"}

    monkeypatch.setattr(auth, "_get_app", lambda: FakeApp())
    with pytest.raises(FabricCLIError) as exc_info:
        auth.get_access_token(["dummy_scope"])
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Failed to get access token: failed due to error" in str(exc_info.value)


def test_set_access_mode_success(monkeypatch):
    """Test setting a valid access mode"""
    auth = FabAuth()
    auth.set_access_mode("user")
    assert auth.get_identity_type() == "user"
    auth.set_access_mode("service_principal")
    assert auth.get_identity_type() == "service_principal"


def test_set_access_mode_invalid(monkeypatch):
    """Test setting an invalid access mode"""
    auth = FabAuth()
    with pytest.raises(FabricCLIError) as exc_info:
        auth.set_access_mode("invalid_mode")
    assert exc_info.value.status_code == con.ERROR_INVALID_ACCESS_MODE


def test_set_access_mode_with_tenant(monkeypatch):
    """Test setting access mode with tenant ID"""
    auth = FabAuth()
    tenant_id = str(uuid.uuid4())
    auth.set_access_mode("user", tenant_id=tenant_id)
    assert auth.get_identity_type() == "user"
    assert auth.get_tenant_id() == tenant_id


def test_validate_environment_vars_managed_identity_with_secret(monkeypatch):
    """Test validation fails when managed identity is enabled with client secret"""
    auth = FabAuth()
    monkeypatch.setenv("FAB_MANAGED_IDENTITY", "true")
    monkeypatch.setenv("FAB_SPN_CLIENT_SECRET", "secret")

    with pytest.raises(FabricCLIError) as exc_info:
        auth._validate_environment_variables()
    assert "FAB_MANAGED_IDENTITY enabled is incompatible with" in str(exc_info.value)


def test_validate_environment_vars_spn_without_tenant(monkeypatch):
    """Test validation fails when SPN is set without tenant ID"""
    auth = FabAuth()
    monkeypatch.setenv("FAB_SPN_CLIENT_ID", "client-id")
    monkeypatch.setenv("FAB_SPN_CLIENT_SECRET", "secret")

    with pytest.raises(FabricCLIError) as exc_info:
        auth._validate_environment_variables()
    assert "FAB_TENANT_ID must be set for SPN authentication" in str(exc_info.value)


def test_is_token_defined_fabric(monkeypatch):
    """Test checking if Fabric token is defined"""
    auth = FabAuth()
    auth._auth_info[con.FAB_TOKEN] = "dummy_token"
    assert auth._is_token_defined(con.SCOPE_FABRIC_DEFAULT) is True


def test_is_token_defined_onelake(monkeypatch):
    """Test checking if OneLake token is defined"""
    auth = FabAuth()
    auth._auth_info[con.FAB_TOKEN_ONELAKE] = "dummy_token"
    assert auth._is_token_defined(con.SCOPE_ONELAKE_DEFAULT) is True


def test_is_token_defined_invalid_scope(monkeypatch):
    """Test checking token defined status with invalid scope"""
    auth = FabAuth()
    with pytest.raises(FabricCLIError) as exc_info:
        auth._is_token_defined("invalid_scope")
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert "Invalid scope" in str(exc_info.value)


def test_get_claims_from_token_multiple_claims(monkeypatch):
    """Test getting multiple claims from a token"""
    auth = FabAuth()

    dummy_token = "dummy.token"
    dummy_payload = {"sub": "123", "name": "Test User", "email": "test@example.com"}

    # Mock _decode_jwt_token to return our dummy payload
    monkeypatch.setattr(
        auth, "_decode_jwt_token", lambda token, expected_audience=None: dummy_payload
    )

    claims = auth._get_claims_from_token(dummy_token, ["sub", "name", "email"])
    assert claims == {"sub": "123", "name": "Test User", "email": "test@example.com"}


def test_get_claims_from_token_missing_claims(monkeypatch):
    """Test getting claims when some are missing from the token"""
    auth = FabAuth()

    dummy_token = "dummy.token"
    dummy_payload = {"sub": "123", "name": "Test User"}

    # Mock _decode_jwt_token to return our dummy payload
    monkeypatch.setattr(
        auth, "_decode_jwt_token", lambda token, expected_audience=None: dummy_payload
    )

    claims = auth._get_claims_from_token(dummy_token, ["sub", "name", "email"])
    assert claims == {
        "sub": "123",
        "name": "Test User",
    }


def test_get_claims_from_token_decode_error(monkeypatch):
    """Test getting claims when token decoding fails"""
    auth = FabAuth()

    # Mock _decode_jwt_token to raise an exception
    def mock_decode_error(*args, **kwargs):
        raise FabricCLIError("Failed to decode token", con.ERROR_AUTHENTICATION_FAILED)

    monkeypatch.setattr(auth, "_decode_jwt_token", mock_decode_error)

    with pytest.raises(FabricCLIError) as exc_info:
        auth._get_claims_from_token("dummy.token", ["sub"])
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED
    assert exc_info.value.status_code == con.ERROR_AUTHENTICATION_FAILED


def test_auth_file_cleanup_on_logout(monkeypatch):
    """Test that auth.json file is cleaned up properly on logout"""
    # Clear environment variables
    _clear_environment_variables(monkeypatch)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Path the config.config_location to the temp_dir
        monkeypatch.setattr(
            "fabric_cli.core.fab_state_config.config_location", lambda: temp_dir
        )

        auth = FabAuth()

        # Create mock auth file with old IDENTITY_TYPE configuration
        auth.auth_file = os.path.join(temp_dir, "auth.json")
        test_auth_data = {
            con.FAB_TENANT_ID: "test-tenant-id",
            con.IDENTITY_TYPE: "user",
        }

        with open(auth.auth_file, "w") as f:
            json.dump(test_auth_data, f)

        # Verify auth file has content
        with open(auth.auth_file, "r") as f:
            file_content = json.load(f)
        assert file_content == test_auth_data

        # Call logout
        auth.logout()

        # Verify auth file is empty
        with open(auth.auth_file, "r") as f:
            file_content = json.load(f)
        assert file_content == {}, "Auth file should be empty after logout"


def test_get_authority_url(monkeypatch):
    """Test that _get_authority_url returns correct URL based on tenant_id presence"""
    # Clear environment variables
    _clear_environment_variables(monkeypatch)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Path the config.config_location to the temp_dir
        monkeypatch.setattr(
            "fabric_cli.core.fab_state_config.config_location", lambda: temp_dir
        )

        auth = FabAuth()

        auth_file = os.path.join(temp_dir, "auth.json")
        auth.auth_file = auth_file

        # Test when no tenant_id is set
        assert (
            auth._get_authority_url() == con.AUTH_DEFAULT_AUTHORITY
        ), "Should return default authority URL when no tenant_id"

        # Test with tenant_id set
        test_tenant_id = "test-tenant-id"
        auth.set_tenant(test_tenant_id)
        expected_url = f"{con.AUTH_TENANT_AUTHORITY}{test_tenant_id}"
        assert (
            auth._get_authority_url() == expected_url
        ), "Should return URL with tenant_id when tenant is set"


def test_authority_url_migration(tmp_path):
    auth_tenant_id = "test-tenant-id"
    auth_data = {
        con.FAB_AUTHORITY: con.AUTH_DEFAULT_AUTHORITY,
        con.FAB_TENANT_ID: auth_tenant_id,
    }

    with open(os.path.join(tmp_path, "auth.json"), "w") as f:
        json.dump(auth_data, f)

    auth = FabAuth()
    auth.auth_file = os.path.join(tmp_path, "auth.json")
    auth._load_auth()

    updated_auth_data = auth._auth_info
    assert (
        updated_auth_data[con.FAB_TENANT_ID] == auth_tenant_id
    ), "FAB_TENANT_ID removed after migration"
    assert (
        con.FAB_AUTHORITY not in updated_auth_data
    ), "FAB_AUTHORITY not removed after migration"


def test_auth_mode_migration(tmp_path):
    auth_data = {
        con.FAB_AUTHORITY: con.AUTH_DEFAULT_AUTHORITY,
        con.FAB_AUTH_MODE: "user",
    }

    with open(os.path.join(tmp_path, "auth.json"), "w") as f:
        json.dump(auth_data, f)

    auth = FabAuth()
    auth.auth_file = os.path.join(tmp_path, "auth.json")
    auth._load_auth()

    updated_auth_data = auth._auth_info

    assert (
        con.IDENTITY_TYPE in updated_auth_data
    ), "IDENTITY_TYPE missing after migration"
    assert updated_auth_data[con.IDENTITY_TYPE] == "user", "Wrong value migrated"
    assert (
        con.FAB_AUTH_MODE not in updated_auth_data
    ), "FAB_AUTH_MODE not removed after migration"
    assert (
        auth.get_identity_type() == "user"
    ), "get_identity_type returns wrong value after migration"
