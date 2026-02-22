# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
MSAL-Azure Identity Bridge Module

This module provides a bridge between MSAL (Microsoft Authentication Library) 
and Azure Identity by implementing the TokenCredential interface. This allows 
existing MSAL authentication flows to be used with Azure SDKs that expect 
TokenCredential objects.

Key Features:
- Supports all authentication types: user, service principal, managed identity
- Handles refresh token management automatically via MSAL's silent acquisition
- Provides proper error handling for headless scenarios
- Ensures scope compatibility with Azure SDKs (.default scopes)
"""

import os
from typing import Optional
from datetime import datetime, timezone

from azure.core.credentials import AccessToken, TokenCredential
from azure.core.exceptions import ClientAuthenticationError

from fabric_cli.core import fab_constant as con
from fabric_cli.core import fab_logger
from fabric_cli.core.fab_auth import FabAuth


class MsalTokenCredential(TokenCredential):
    """
    A TokenCredential implementation that wraps the existing Fabric CLI MSAL authentication.
    
    This bridge uses the CLI user's existing authentication and provides it through
    the Azure Identity TokenCredential interface. It handles refresh token management
    automatically via MSAL's silent acquisition flow.
    
    The credential will use whatever authentication the CLI user has already configured:
    - User authentication (from fab auth login)
    - Service principal (from environment variables)
    - Managed identity (when running in Azure)
    - Environment tokens (pre-acquired tokens)
    
    Args:
        fab_auth: FabAuth instance containing the authentication configuration.
    """

    def __init__(self, fab_auth: FabAuth):
        self._fab_auth = fab_auth

    def get_token(
        self,
        *scopes: str,
        claims: Optional[str] = None,
        tenant_id: Optional[str] = None,
        enable_cae: bool = False,
        **kwargs
    ) -> AccessToken:
        """
        Get an access token for the specified scopes.
        
        Args:
            scopes: The scopes for which to request the token
            claims: Optional claims challenge
            tenant_id: Optional tenant ID (not used in this implementation)
            enable_cae: Whether to enable Continuous Access Evaluation (not used)
            **kwargs: Additional keyword arguments
            
        Returns:
            AccessToken object containing the token and expiration time
            
        Raises:
            ClientAuthenticationError: When authentication is not available
        """
        # Bridge-specific security validations
        fab_logger.log_info(f"Token requested for deployment, scopes: {list(scopes)}")
        
        # Bridge-specific: strict .default scope validation
        valid_default_scopes = {
            con.SCOPE_FABRIC_DEFAULT[0],
        }
        
        for scope in scopes:
            if scope not in valid_default_scopes:
                fab_logger.log_info(f"Invalid scope rejected: {scope}")
                raise ClientAuthenticationError(
                    f"Security validation failed: Only .default scopes are allowed. "
                    f"Invalid scope: {scope}. "
                    f"Allowed scopes: {', '.join(valid_default_scopes)}"
                )
        
        fab_logger.log_debug(f"Requesting token for scopes: {list(scopes)}")
        
        try:
            # Delegate to shared authentication logic
            msal_result = self._fab_auth.acquire_token(
                list(scopes),
                interactive_renew=False  # Bridge is always headless
            )
            
            # Bridge-specific: Convert to AccessToken for Azure SDK compatibility
            return self._create_access_token(msal_result)
            
        except Exception as e:
            fab_logger.log_debug(f"Token acquisition failed: {e}")
            raise ClientAuthenticationError(
                f"\n{str(e)}"
            ) from e

    def _create_access_token(self, msal_result: dict) -> AccessToken:
        """Convert MSAL result to AccessToken object."""
        access_token = msal_result["access_token"]
        
        # Handle expires_on - MSAL returns Unix timestamp as string or int
        expires_on = msal_result.get("expires_on")
        if expires_on:
            if isinstance(expires_on, str):
                expires_on = int(expires_on)
        else:
            # Fallback: calculate from expires_in if available
            expires_in = msal_result.get("expires_in")
            if expires_in:
                import time
                expires_on = int(time.time() + expires_in)
            else:
                # Default to 1 hour from now if no expiration info
                import time
                expires_on = int(time.time() + 3600)
        
        fab_logger.log_debug(f"Token acquired, expires at: {datetime.fromtimestamp(expires_on, tz=timezone.utc)}")
        
        return AccessToken(access_token, expires_on)

    def close(self) -> None:
        """Close the credential (no-op for this implementation)."""
        pass


def create_fabric_token_credential(fab_auth: Optional[FabAuth] = None) -> TokenCredential:
    """
    Create a TokenCredential that uses the current Fabric CLI authentication.
    
    This function creates a TokenCredential that wraps the existing MSAL authentication
    from the Fabric CLI. It will use whatever authentication the user has already
    configured (user login, service principal, managed identity, or environment tokens).
    
    Args:
        fab_auth: Optional FabAuth instance. If None, uses the singleton instance.
        
    Returns:
        TokenCredential that can be used with Azure SDKs
        
    Raises:
        ClientAuthenticationError: When no authentication is configured
    """
    if fab_auth is None:
        fab_auth = FabAuth()  # Uses singleton
    
    identity_type = fab_auth.get_identity_type()
    
    fab_logger.log_debug(f"Creating TokenCredential for identity type: {identity_type}")
    return MsalTokenCredential(fab_auth)

