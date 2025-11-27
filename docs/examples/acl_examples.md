# Access Control (ACL) Examples

This page demonstrates how to manage access control and permissions for Microsoft Fabric resources using the CLI. 
The ACL commands support three main resource types:

- **Workspaces**: Manage permissions at the workspace level
- **Items**: Control access to individual items within workspaces (e.g., Lakehouses, Notebooks)
- **OneLake**: Manage storage-level RBAC permissions for data access

To explore all ACL commands and their parameters, run:

```
fab acl -h
```

**[Workspace Roles](https://learn.microsoft.com/en-us/fabric/fundamentals/roles-workspaces):** `Admin`, `Member`, `Contributor`, `Viewer`

---

## Manage Permissions

### Add Workspace Permissions

Grant workspace permission to a user, service principal or security group using the object ID with `-I`.

```
fab acl set ws1.Workspace -I 00000000-0000-0000-0000-000000000000 -R contributor
```


### List Permissions

#### List Workspace Permissions

```py
# List basic workspace permissions
fab acl ls ws1.Workspace

# List detailed workspace permissions
fab acl ls ws1.Workspace -l

# List specific columns using query parameter
fab acl ls ws1.Workspace -q identity           # Show only identity column
fab acl ls ws1.Workspace -q [].[identity,type]    # Show identity and name columns
```

#### List Item Permissions
```py
# List basic item permissions
fab acl ls ws1.Workspace/lh1.Lakehouse

# List detailed item permissions
fab acl ls ws1.Workspace/lh1.Lakehouse -l

# List specific columns for item permissions
fab acl ls ws1.Workspace/lh1.Lakehouse -q [].type     # Show only type column
fab acl ls ws1.Workspace/lh1.Lakehouse -q '[].{name: name, type: type}'   # Show type and name columns
```

#### List OneLake RBAC Permissions
```py
# List basic OneLake permissions
fab acl ls ws1.Workspace/lh1.Lakehouse/Files

# List detailed OneLake permissions
fab acl ls ws1.Workspace/lh1.Lakehouse/Files -l
```

### Get Permission Details

#### Get Workspace Permissions
```py
# Get complete workspace permissions (JSON format)
fab acl get ws1.Workspace

# Query workspace permission principals
fab acl get ws1.Workspace -q "[*].principal"

# Export workspace permissions to local directory
fab acl get ws1.Workspace -q "[*].principal" -o /tmp
```

#### Get Item Permissions
```py
# Get complete item permissions (JSON format)
fab acl get ws1.Workspace/lh1.Lakehouse

# Query item permission principals
fab acl get ws1.Workspace/lh1.Lakehouse -q "[*].principal"

# Export to local directory
fab acl get ws1.Workspace/lh1.Lakehouse -o /tmp

# Export to Lakehouse Files
fab acl get ws1.Workspace/lh1.Lakehouse -o /ws1.Workspace/lh1.Lakehouse/Files
```

#### Get OneLake RBAC Permissions
```py
# Get complete OneLake permissions (JSON format)
fab acl get ws1.Workspace/lh1.Lakehouse/Files

# Query OneLake permission members
fab acl get ws1.Workspace/lh1.Lakehouse/Files -q "[].members"

# Export OneLake permissions to local directory
fab acl get ws1.Workspace/lh1.Lakehouse/Files -q "[].members" -o /tmp
```

### Remove Workspace Permissions

```py
# Remove a security group from workspace permissions using the group name.
fab acl rm ws1.Workspace -I 00000000-0000-0000-0000-000000000000

# Remove a user from workspace permissions using their email address.
fab acl rm ws1.Workspace -I fabcli@microsoft.com

#Remove a service principal using its client ID or object ID.
fab acl rm ws1.Workspace -I 00000000-0000-0000-0000-000000000000
```