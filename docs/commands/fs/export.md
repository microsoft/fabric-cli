# `export` Command

Export an item.

!!! warning "When exporting an item, the item definition is exported without its sensitivity label"

**Supported Types:**

- All workspace item types that support definition export (e.g., `.Notebook`, `.Report`, etc.)

**Usage:**

```
fab export <path> -o <output_path> [-a] [--format <format>] [-f]
```

**Parameters:**

- `<path>`: Path to the item to export.
- `-o, --output <output_path>`: Output directory path.
- `-a, --all`: Export all items. Optional.
- `--format <format>`: Format of the export. Supported for items allowing multiple export formats, currently only Notebooks (`.ipynb`, `.py`), Semantic Models (`TMDL`, `TMSL`) and Spark Job Definition (`SparkJobDefinitionV1`, `SparkJobDefinitionV2`). Optional.
- `-f, --force`: Force export without confirmation. Optional.

**Example:**

```
fab export ws1.Workspace/nb1.Notebook -o C:\Users\myuser
```

