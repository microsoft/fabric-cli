# `rm` / `del` Command

Delete a workspace, item, or file.

!!! info "Deleting a domain requires tenant-level Fabric Administrator privileges"

**Usage:**

```
fab rm <path> [-f]
```

**Parameters:**

- `<path>`: Path to delete.
- `-f, --force`: Force deletion without confirmation. Optional.

**Example:**

```
fab rm ws1.Workspace/nb1.Notebook
```