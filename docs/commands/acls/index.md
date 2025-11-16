# ACL Commands

The `acl` commands manage access control lists (ACLs) for Fabric resources. Use these commands to view, set, and manage access permissions.

## Available Commands

| Command    | Description                    | Usage                                             |
|------------|--------------------------------|---------------------------------------------------|
| `acl get`  | Get ACL entries for a resource | `acl get <path> [-q QUERY]`                      |
| `acl ls`   | List ACL entries              | `acl ls <path> [-l] [-q QUERY]`                  |
| `acl set`  | Set ACL entry                 | `acl set <path> --identity ID --role ROLE [-f]`  |
| `acl rm`   | Remove ACL entry              | `acl rm <path> --identity ID [-f]`               |

---

### ls (dir)

List ACL entries for a resource.

!!! info "Listing ACLs for a workspace or item requires tenant-level Fabric Administrator"

**Usage:**

```
fab acl ls <path> [-l] [-q QUERY]
```

**Parameters:**

- `<path>`: Resource path
- `-l, --long`: Show detailed output including object IDs and names. Optional.
- `-q, --query`: JMESPath query to filter and project fields. Optional.

**Examples:**

```bash
# List basic ACL entries
fab acl ls ws1.Workspace

# List detailed ACL information
fab acl ls ws1.Workspace -l

# Project single field using array projection
fab acl ls ws1.Workspace -q "[*].identity"

# Project multiple fields using array syntax  
fab acl ls ws1.Workspace -q "[identity, type]"

# Project and rename fields using object syntax
fab acl ls ws1.Workspace -q "{principalInfo: identity, accessLevel: role}"

# Filter specific roles and project fields
fab acl ls ws1.Workspace -q "[?role=='Member'].{id: identity, role: role}"
```

**Notes:**

- The `-q` parameter accepts JMESPath query expressions (https://jmespath.org)
- Array projection `[*].field` returns an array of values
- Array syntax `[field1, field2]` selects multiple fields 
- Object syntax `{newName: field}` renames fields in output
- Filter expressions `[?field=='value']` filter results
- Query projection takes precedence over `-l` flag field selection

---

### get

Get ACL entries for a resource.

**Usage:**

```
fab acl get <path> [-q QUERY]
```

**Parameters:**

- `<path>`: Resource path
- `-q, --query`: JMESPath query to filter and project fields. Optional.

**Examples:**

```bash
# Get all ACL entries
fab acl get ws1.Workspace

# Query specific roles
fab acl get ws1.Workspace -q "[?role=='Admin']"

# Project role information
fab acl get ws1.Workspace -q "[].role"
```

---

### set

Set an ACL entry for a resource.

**Usage:**

```
fab acl set <path> --identity ID --role ROLE [-f]
```

**Parameters:**

- `<path>`: Resource path
- `--identity`: Principal ID (user ID, service principal ID, or security group ID)
- `--role`: Role to assign (e.g., Admin, Member, Viewer)
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```bash
# Set member role for a user
fab acl set ws1.Workspace --identity "user@contoso.com" --role Member

# Set admin role for a service principal (force)
fab acl set ws1.Workspace --identity "00000000-0000-0000-0000-000000000000" --role Admin -f
```

---

### rm

Remove an ACL entry from a resource.

**Usage:**

```
fab acl rm <path> --identity ID [-f]
```

**Parameters:**

- `<path>`: Resource path
- `--identity`: Principal ID to remove
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```bash
# Remove ACL entry for a user
fab acl rm ws1.Workspace --identity "user@contoso.com"

# Force remove ACL entry
fab acl rm ws1.Workspace --identity "00000000-0000-0000-0000-000000000000" -f
