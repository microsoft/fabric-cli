# Authentication Commands

The `auth` commands manage how you authenticate with the Fabric CLI. The CLI supports multiple authentication methods for both interactive and automated scenarios.

**Supported Types:**

Not resource-specific; applies to CLI authentication context.

## Available Commands

| Command        | Description                | Usage                                                                 |
|----------------|---------------------------|-----------------------------------------------------------------------|
| `auth login`   | Log in to Fabric CLI      | `auth login [parameters]`                                                |
| `auth logout`  | Log out of current session| `auth logout`                                                         |
| `auth status`  | Show authentication status| `auth status`                                                         |

---

### login

Authenticate with Fabric CLI.

**Usage:**

```
fab auth login [-u <client_id>] [-p <client_secret>] [--federated-token <token>] [--certificate </path/to/certificate.[pem|p12|pfx]>] [--azure-cli] [--tenant <tenant_id>]
```

**Parameters:**

- `-u, --user`: Client ID for service principal. Optional.
- `-p, --password`: Client secret for service principal. Optional.
- `--federated-token`: Federated token for workload identity. Optional.
- `--certificate`: Path to certificate file. Optional.
- `--azure-cli`: Use an existing Azure CLI login session as the token provider. Requires Azure CLI to be installed and logged in (`az login`). Optional.
- `--tenant`: Tenant ID. Optional. When used with `--azure-cli`, pins Fabric CLI to the specified tenant.

---

### logout

End the current authentication session.

**Usage:**

```
fab auth logout
```

---

### status

Display current authentication state.

**Usage:**

```
fab auth status
```

---

For more examples and detailed scenarios, see [Authentication Examples](../../examples/auth_examples.md).
