# `export` Command

Export an item.

!!! warning "When exporting an item, the item definition is exported without its sensitivity label"

**Supported Types:**

- All workspace item types that support definition export (e.g., `.Notebook`, `.Report`, etc.)

**Usage:**

```
fab export <path> -o <output_path> [-a] [-f]
```

**Parameters:**

- `<path>`: Path to the item to export.
- `-o, --output <output_path>`: Output directory path.
- `-a, --all`: Export all items. Optional.
- `-f, --force`: Force export without confirmation. Optional.

**Example:**

```
fab export ws1.Workspace/nb1.Notebook -o C:\Users\myuser
```

