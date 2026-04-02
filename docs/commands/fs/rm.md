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
- `--purge`: Permanently delete the item. Cannot be recovered. When not specified, item is soft-deleted if the item type supports it. Optional.

**Example:**

```
# Soft delete
fab rm ws1.Workspace/nb1.Notebook

# Force delete without confirmation
fab rm ws1.Workspace/nb1.Notebook --force

# Purge delete (permanent removal)
fab rm ws1.Workspace/nb1.Notebook --purge --force
```