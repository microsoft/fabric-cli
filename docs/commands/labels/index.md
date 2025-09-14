# Sensitivity Labels Commands

The `label` commands provide tools for managing sensitivity labels on workspaces, items, and data. These labels help protect and classify your data according to its sensitivity level.

!!! info
    - All label management commands requires tenant-level Fabric Administrator privileges
    - Labels must be defined in a local JSON file.
    - Set the path using: `config set local_definition_labels <json_path>`
    - File should map label IDs to friendly names.

**Label definition file example:**
```json
{
  "labels": {
    "1234-5678-90ab-cdef": {
      "name": "Confidential",
      "description": "Internal use only"
    },
    "9876-5432-10fe-dcba": {
      "name": "Public",
      "description": "No restrictions"
    }
  }
}
```

## Available Commands

| Command           | Description                   | Usage                                         |
|-------------------|------------------------------|-----------------------------------------------|
| `label list-local`| List labels from local config | `label list-local`                            |
| `label set`       | Set a sensitivity label       | `label set <path> -n <label_name> [-f]`       |
| `label rm` (del)  | Remove a sensitivity label    | `label rm <path> [-f]`                        |

---

### list-local

List available sensitivity labels defined in your local configuration.

**Usage:**

```
fab label list-local
```

**Examples:**

```
fab label list-local
```

---

### set

Apply a sensitivity label to a resource.

!!! note "Label must exist in local definitions"

**Usage:**

```
fab label set <path> -n <label_name> [-f]
```


**Parameters:**

- `<path>`: Path to the resource.
- `-n, --name`: Sensitivity label name.
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```
fab label set notebook1.notebook -n Confidential
fab label set lh1.lakehouse -n "Highly Confidential" -f
fab label set workspace1.workspace -n Internal
```


---

### rm (del)

Remove a sensitivity label from a resource.

**Usage:**

```
fab label rm <path> [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-f, --force`: Skip confirmation prompt. Optional.

**Examples:**

```
fab label rm notebook1.notebook
fab label rm lh1.lakehouse -f
```

---

For more examples and detailed scenarios, see [Label Management Examples](../../examples/label_examples.md).
