
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