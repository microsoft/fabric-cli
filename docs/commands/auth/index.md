# Authentication Commands

The `auth` commands manage how you authenticate with the Fabric CLI. The CLI supports multiple authentication methods for both interactive and automated scenarios.

**Supported Types:**

Not resource-specific; applies to CLI authentication context.

## Available Commands

| Command        | Description                | Usage                                                                 |
|----------------|---------------------------|-----------------------------------------------------------------------|
| `auth login`   | Log in to Fabric CLI      | `auth login [parameters]`                                                |
| `auth logout`  | Log out of current session| `auth logout`                                                         |
| `auth list`    | List stored user sessions | `auth list`                                                           |
| `auth status`  | Show authentication status| `auth status`                                                         |
| `auth switch`  | Switch stored user session| `auth switch [parameters]`                                            |

---

### login

Authenticate with Fabric CLI.

**Usage:**

```
fab auth login [-u <client_id>] [-p <client_secret>] [--federated-token <token>] [--certificate </path/to/certificate.[pem|p12|pfx]>] [--tenant <tenant_id>]
```

**Parameters:**

- `-u, --user`: Client ID for service principal. Optional.
- `-p, --password`: Client secret for service principal. Optional.
- `--federated-token`: Federated token for workload identity. Optional.
- `--certificate`: Path to certificate file. Optional.
- `--tenant`: Tenant ID. Optional.

---

### logout

End the current authentication session. When multiple user sessions are stored you can target a specific session by account name and/or tenant.

**Usage:**

```
fab auth logout [-u <account_name>] [-t <tenant_id>] [--all]
```

**Parameters:**

- `-u, --username`: Account name of the session to log out. Case-insensitive. Optional.
- `-t, --tenant`: Tenant ID to disambiguate when the same account exists in multiple tenants. Optional.
- `--all`: Clear all stored authentication sessions. Optional.

When neither `-u` nor `--all` is provided, the CLI removes the current active session. If other sessions remain, the next most recently used session becomes active.

---

### list

List stored user authentication sessions. Each row shows whether the session is active, the account name, tenant, token validity, and the last used timestamp.

**Usage:**

```
fab auth list
```

---

### status

Display current authentication state.

**Usage:**

```
fab auth status
```

---

### switch

Switch the active stored user authentication session. You can specify the target account directly to avoid interactive selection.

**Usage:**

```
fab auth switch [-u <account_name>] [-t <tenant_id>]
```

**Parameters:**

- `-u, --username`: Account name to switch to. Case-insensitive. Optional.
- `-t, --tenant`: Tenant ID to disambiguate when the same account exists in multiple tenants. Optional.

**Behavior:**

- With `-u` (and optionally `-t`): switches directly to the matching session.
- With two stored sessions and no flags: automatically toggles to the other session.
- With three or more sessions and no flags: presents an interactive prompt.

---

For more examples and detailed scenarios, see [Authentication Examples](../../examples/auth_examples.md).
