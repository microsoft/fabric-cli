# `cp` / `copy` Command

Copy an item, a folder or a file.
The behavior of the `cp` command varies depending on the source (item or folder) and the destination path.

!!! warning "When copying an item, the item definition is copied without its sensitivity label"

**Supported Types:**

- All workspace item types that support definition export/import (e.g., `.Notebook`, `.Report`, etc.)
- OneLake files and folders

**Usage:**

```
fab cp <from_path> <to_path> [-r] [-f]
```

**Parameters:**

- `<from_path>`: Source path.
- `<to_path>`: Destination path.
- `-r, --recursive`: Copies all items in the source path, including subfolders and their contents (only applicable for workspaces and folders). Optional.
- `-f, --force`: Force copy without confirmation. Optional.


## Limitations

- When copying a folder, items that do not support the copy operation are skipped. Only supported items will be copied.
- When copying an item to the same workspace, `_copy` is automatically appended to the item name to avoid conflicts.

**Example:**

```
fab cp ws1.Workspace/nb1.Notebook ws2.Workspace
```
