# Access Control List (ACL) Commands

The access control list (`acl`) commands let you manage permissions and security settings for workspaces, items, and OneLake resources.

**Supported Types:**

- `.Workspace` (workspace-level ACLs)
- `.Connection`
- `.Gateway`
- All workspace item types (item-level ACLs)
- OneLake storage sections (RBAC)

## Available Commands

| Command         | Description             | Usage                                              |
|-----------------|------------------------|----------------------------------------------------|
| `acl ls` (dir)  | List ACLs              | `acl ls <path> [-l]`                               |
| `acl get`       | Get ACL details        | `acl get <path> [-q <query>] [-o <output_path>]`   |
| `acl set`       | Set access controls     | `acl set <path> -I <identity> -R <role> [-f]`  |
| `acl rm` (del)  | Remove an ACL          | `acl rm <path> -I <identity> [-f]`               |

---

### ls (dir)

List access control entries for a workspace, item, gateway, connection or OneLake resource.

!!! info "Listing ACLs for an item requires tenant-level Fabric Administrator"

**Usage:**

```
fab acl ls <path> [-l] [-q <query>]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-l, --long`: Show detailed output. Optional.
- `-q, --query`: JMESPath query to filter results. Optional.

**Examples:**

```
# List workspace acls
fab acl ls ws1.workspace

# List workspace admins acls
fab acl ls ws1.workspace -q [].[?role=='Admin']

# List lakehouse item acls
fab acl ls ws1.workspace/lh1.lakehouse
fab acl ls ws1.workspace/lh1.lakehouse/Files/data
```

---

### get

Get detailed ACL information with optional filtering for workspace, item, gateway, connection or OneLake resource.


!!! info "Retrieving ACLs for an item requires tenant-level Fabric Administrator"

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
# Get workspace acl
fab acl get ws1.Workspace

# Get item acl
fab acl get ws1.Workspace/lh1.Lakehouse
```

---

### set

Set access control permissions for a workspace, gateway or connection.

**Usage:**

```
fab acl set <path> -I <identity> -R <role> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-I, --identity`: Object ID of the Microsoft Entra identity to set or update.
- `-R, --role`: ACL role (admin, member, contributor, viewer).
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```
fab acl set ws1.Workspace -I 11111111-2222-3333-4444-555555555555 -R viewer
```

---

### rm (del)

Remove access permissions for an identity from a workspace, gateway or connection.

**Usage:**

```
fab acl rm <path> -I <identity> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-I, --identity`: Object ID of the Microsoft Entra identity to remove.
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```
fab acl rm ws1.Workspace -I 11111111-2222-3333-4444-555555555555
```



---

For more examples and detailed scenarios, see [ACLs Examples](../../examples/acl_examples.md).
