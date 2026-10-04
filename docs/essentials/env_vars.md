
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

## Direct access token identity consistency

When direct access tokens are used, the CLI verifies that all configured token
variables contain the same tenant (`tid`) and principal (`oid`) claims. The
token tenant must also match `FAB_TENANT_ID`. If a claim is missing or the
identities differ, the CLI logs out, clears its authentication and resource
caches, resets the current context, and fails the command.

The token identity must also match the identity of an already authenticated
session. If you are signed in (for example, in user or Azure CLI mode) and then
set direct access token variables for a different tenant or principal, the CLI
treats this as identity drift, logs out, and fails the command instead of
silently switching identity.

When no prior session exists, the CLI records the direct access token identity
on first use. Any later change to a different tenant or principal — including
swapping to another direct access token — is then detected as drift, logs out,
and fails the command, consistent with Azure CLI authentication mode.

This validation applies only to direct access token environment variables. It
does not apply when Azure CLI authentication mode is active.
