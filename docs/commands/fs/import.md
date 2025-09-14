# `import` Command

Import an item (create/modify).

!!! warning "When importing, the item definition is imported without its sensitivity label"

**Supported Types:**

- All workspace item types that support definition import (e.g., `.Notebook`, `.Report`, etc.)

**Usage:**

```
fab import <path> -i <input_path> [--format <format>] [-f]
```

**Parameters:**

- `<path>`: Path to import to.
- `-i, --input <input_path>`: Input path.
- `--format <format>`: Format of the input. Supported only for Notebooks (`.ipynb`, `.py`). Optional.
- `-f, --force`: Force import without confirmation. Optional.

**Example:**

```
fab import ws2.Workspace -i C:\Users\myuser\nb1.Notebook
```
