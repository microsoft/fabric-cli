# Access Control List (ACL) Commands

The access control list (`acl`) commands let you manage permissions and security settings for workspaces, items, and OneLake resources.

**Supported Types:**

- `.Workspace` (workspace-level ACLs)
- All workspace item types (item-level ACLs)
- OneLake storage sections (RBAC)

## Available Commands

| Command         | Description             | Usage                                              |
|-----------------|------------------------|----------------------------------------------------|
| `acl ls` (dir)  | List ACLs              | `acl ls <path> [-l]`                               |
| `acl set`       | Set access controls     | `acl set <path> [-I <identity>] [-R <role>] [-f]`  |
| `acl rm` (del)  | Remove an ACL          | `acl rm <path> [-I <identity>] [-f]`               |
| `acl get`       | Get ACL details        | `acl get <path> [-q <query>] [-o <output_path>]`   |

---

### ls (dir)

List access control entries for a workspace, item, or OneLake resource.

!!! info "Listing ACLs for a workspace or item requires tenant-level Fabric Administrator"

**Usage:**

```
fab acl ls <path> [-l]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-l, --long`: Show detailed output. Optional.

**Examples:**

```
fab acl ls workspace1.workspace
fab acl ls lh1.lakehouse -l
fab acl ls /Files/data -l
```

---

### set

Set access control permissions for a resource.

**Usage:**

```
fab acl set <path> [-I <identity>] [-R <role>] [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-I, --identity`: Object ID of the Microsoft Entra identity to set or update.
- `-R, --role`: ACL role (admin, member, contributor, viewer).
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```
fab acl set ws1.Workspace/lh1.Lakehouse -I 11111111-2222-3333-4444-555555555555 -R viewer
```

---

### rm (del)

Remove access permissions for an identity.

**Usage:**

```
fab acl rm <path> [-I <identity>] [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-I, --identity`: Object ID of the Microsoft Entra identity to remove.
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```
fab acl rm ws1.Workspace/lh1.Lakehouse -I 11111111-2222-3333-4444-555555555555
```

---

### get

Get detailed ACL information with optional filtering.

**Usage:**

```
fab acl get <path> [-q <query>] [-o <output_path>]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-q, --query`: JMESPath query to filter results. Optional.
- `-o, --output`: Output path for results. Optional.

**Examples:**

```
fab acl get ws1.Workspace
```

---

For more examples and detailed scenarios, see [ACLs Examples](../../examples/acl_examples.md).
