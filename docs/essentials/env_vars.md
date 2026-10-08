
# Environment Variables

The CLI supports multiple authentication methods through environment variables. When environment variables are properly configured, authentication happens using these environment variables without requiring an explicit login. It is important to choose one authentication method at a time and to provide all **required** variables for that method.


!!! tip "With `Authentication Tokens` method, you must refresh authentication tokens before they expire, as the CLI does not automatically refresh them."

| Method | Environment Variable | Description |
|--------|---------------------|-------------|
| Authentication Tokens | `FAB_TOKEN` | Authentication token for Fabric |
|  | `FAB_TOKEN_ONELAKE` | Authentication token for OneLake |
|  | `FAB_TOKEN_AZURE` | Authentication token for Azure |
|  | `FAB_TENANT_ID` | Tenant ID |
| Service Principal with Secret | `FAB_SPN_CLIENT_ID` | Service principal client ID |
|  | `FAB_SPN_CLIENT_SECRET` | Service principal client secret |
|  | `FAB_TENANT_ID` | Tenant ID |
| Service Principal with Certificate | `FAB_SPN_CLIENT_ID` | Service principal client ID |
|  | `FAB_SPN_CERT_PATH` | Certificate path |
|| `FAB_SPN_CERT_PASSWORD` | Certificate password (optional) |
| | `FAB_TENANT_ID` | Tenant ID |
| Service Principal with Federated Token | `FAB_SPN_CLIENT_ID` | Service principal client ID |
|  | `FAB_SPN_FEDERATED_TOKEN` | Federated token |
|  | `FAB_TENANT_ID` | Tenant ID |
| Managed Identity | `FAB_MANAGED_IDENTITY` | Enable Managed Identity auth (values: `true`, `1`) |
| | `FAB_SPN_CLIENT_ID` | **Optional**. Service principal client ID for User Assigned |

## Identity drift with authentication tokens

When authentication tokens are used, the CLI detects identity drift in any of
the following situations:

- The configured `FAB_TOKEN`, `FAB_TOKEN_ONELAKE`, and `FAB_TOKEN_AZURE`
  values do not belong to the same user or service principal and tenant.
- A token's tenant differs from `FAB_TENANT_ID`.
- The token identity differs from the identity established by an earlier
  interactive sign-in or set of authentication tokens.

!!! note
    Authentication token environment variables are ignored when the CLI uses
    Azure CLI, service principal, or managed identity authentication.

When identity drift is detected, the CLI logs out of the current session and
the command fails.

To continue, resolve the cause of the error and run the command again:

- If the configured tokens belong to different identities or tenants, replace
  the inconsistent tokens so that they all belong to the same user or service
  principal and tenant.
- If `FAB_TENANT_ID` is set and a token's tenant differs from it, update the
  token or `FAB_TENANT_ID` so that the tenants match.
- If the token identity differs from the previous session, run the command
  again to use the new token identity. To keep using the previous identity,
  replace the tokens before running the command again.