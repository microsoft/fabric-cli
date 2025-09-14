# `unassign` Command

Unassign a resource from a workspace.

!!! info "Unassigning a domain from a workspace requires tenant-level Fabric Administrator privileges"

**Supported Types:**

- `.Capacity`
- `.Domain`

**Usage:**

```
fab unassign <path> -W <workspace> [-f]
```

**Parameters:**

- `<path>`: Path to the resource to unassign.
- `-W, --workspace <workspace>`: Target workspace name.
- `-f, --force`: Force unassignment without confirmation. Optional.

**Example:**

```
fab unassign .capacities/cap.Capacity -W ws1.Workspace
```
