# `mv` / `move` Command

Move an item, a folder or a file.
The behavior of the `mv` command varies depending on the source (item or folder) and the destination path.

!!! warning "When moving an item, the item definition is moved without its sensitivity label"

**Supported Types:**

- All workspace item types that support definition export/import (e.g., `.Notebook`, `.Report`, etc.)
- OneLake files and folders

**Usage:**

```
fab mv <from_path> <to_path> [-r] [-f]
```

**Parameters:**

- `<from_path>`: Source path.
- `<to_path>`: Destination path.
- `-r, --recursive`: Moves all items in the source path, including subfolders and their contents (only applicable for workspaces and folders). Optional.
- `-f, --force`: Force move without confirmation. Optional.

## Limitations

- Moving items within the same workspace between different folders is not yet supported.
- When moving a folder containing items that do not support the move operation:
    - A prompt will be provided to proceed unless the `--force` flag is used.
    - Only supported items are moved; unsupported items are skipped.
    - The source folder is only deleted if it is **completely** empty after the move operation.

**Example:**

```
fab mv ws1.Workspace/nb1.Notebook ws2.Workspace
```

