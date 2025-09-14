# `ls` / `dir` Command

List workspaces, items, and files.

!!! info "Listing domains requires tenant-level Fabric Administrator privileges"

**Usage:**

```
fab ls <path> [-l] [-a]
```

**Parameters:**

- `<path>`: Path to list. Optional.
- `-l, --long`: Show detailed output. Optional.
- `-a, --all`: Show hidden entities. Optional.

**Example:**

```
fab ls ws1.Workspace
```