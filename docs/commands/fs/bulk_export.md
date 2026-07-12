# `bulk-export` Command

Export a workspace or folder in bulk while preserving folder structure and item bindings.

The `bulk-export` command exports all supported items from a workspace or folder in a single bulk API request, preserving the folder hierarchy and item bindings (logical IDs) in the exported definitions.

!!! warning "When exporting items, the item definitions are exported without their sensitivity labels"

!!! note "Permissions"
    - **Workspace export**: Only items that the caller has both read and write permissions for are exported.
    - **Folder export**: The caller must have read and write permissions for all folder items.

!!! note "Differences from `export`"
    - **Folder structure**: `bulk-export` preserves the workspace folder hierarchy in the output. `export` exports items flat.
    - **Item bindings**: `bulk-export` preserves item logical IDs, enabling round-trip import/update. `export` uses nil UUIDs.
    - **Format**: `bulk-export` does not support the `--format` flag. Items are exported in their default format only.
    - **Target scope**: `bulk-export` operates on workspaces and folders. `export` operates on individual items or workspaces.

**Supported Targets:**

- `.Workspace` — exports all supported items in the workspace
- `.Folder` — exports all supported items in the folder and its sub-folders

**Supported Item Types:**

`CopyJob`, `CosmosDBDatabase`, `Dataflow`, `DataPipeline`, `DigitalTwinBuilder`, `Environment`, `Eventhouse`, `Eventstream`, `GraphQLApi`, `GraphQuerySet`, `KQLDashboard`, `KQLDatabase`, `KQLQueryset`, `Lakehouse`, `Map`, `MirroredDatabase`, `MLExperiment`, `MLModel`, `MountedDataFactory`, `Notebook`, `Reflex`, `Report`, `SemanticModel`, `SparkJobDefinition`, `SQLDatabase`, `UserDataFunction`, `VariableLibrary`

Unsupported item types are automatically skipped and reported in the output summary.

**Usage:**

```
fab bulk-export <path> -o <output_path> --recursive [-f]
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `<path>` | Path to the workspace or folder to export. |
| `-o, --output <output_path>` | Output directory path. Required. |
| `--recursive` | Recursively export folder contents. Required for workspace and folder targets. |
| `-f, --force` | Skip confirmation prompts. Exports without sensitivity label confirmation and proceeds when the output folder is not empty. Optional. |

**Examples:**

```bash
# Bulk-export an entire workspace to a local directory
fab bulk-export ws1.Workspace -o /tmp --recursive --force

# Bulk-export a specific folder
fab bulk-export ws1.Workspace/folder1.Folder -o /tmp --recursive --force
```

**Output:**

On success, the command prints a summary with the number of exported and skipped items:

```
Exported 15 items to '/tmp'. Skipped 1 items due to unsupported item types: Dashboard (1)
```

When using `--output-format json`, the output includes structured data:

```json
{
  "exported": 15,
  "exported_types": {
    "SemanticModel": 5,
    "Report": 4,
    "Notebook": 3,
    "DataPipeline": 3
  },
  "skipped": 1,
  "skipped_types": {
    "Dashboard": 1
  },
  "output": "/tmp"
}
```

**Output Directory Structure:**

The exported output mirrors the workspace folder structure:

```
<output_path>/
├── Folder1/
│   ├── notebook1.Notebook/
│   │   ├── .platform
│   │   └── notebook-content.ipynb
│   └── report1.Report/
│       ├── .platform
│       ├── definition.pbir
│       └── StaticResources/
│           └── ...
└── Folder2/
    └── model1.SemanticModel/
        ├── .platform
        └── definition/
            ├── model.tmdl
            └── ...
```
