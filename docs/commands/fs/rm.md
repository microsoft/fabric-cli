# `rm` / `del` Command

Delete a workspace, item, or file.

!!! info "Deleting a domain requires tenant-level Fabric Administrator privileges"

**Usage:**

```
fab rm <path> [-f] [--purge]
```

**Parameters:**

- `<path>`: Path to delete.
- `-f, --force`: Force deletion without confirmation. Optional.
- `--purge`: Permanently delete items (when applicable). Cannot be recovered. Ignored for workspace force deletion. Optional.

**Example:**

```
# Soft delete
fab rm ws1.Workspace/nb1.Notebook

# Force delete without confirmation
fab rm ws1.Workspace/nb1.Notebook --force

# Purge delete (permanent removal)
fab rm ws1.Workspace/nb1.Notebook --purge --force
```