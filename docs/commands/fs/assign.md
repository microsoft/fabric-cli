# `assign` Command

Assign a resource to a workspace.

!!! info "Assigning a domain to a workspace requires tenant-level Fabric Administrator privileges"

**Supported Types:**

- `.Capacity`
- `.Domain`


**Usage:**

```
fab assign <path> -W <workspace> [-f]
```

**Parameters:**

- `<path>`: Path to the resource to assign.
- `-W, --workspace <workspace>`: Target workspace name.
- `-f, --force`: Force assignment without confirmation. Optional.

**Example:**

```
fab assign .capacities/cap.Capacity -W ws1.Workspace
```

