# `set` Command

Set a workspace or item property.

!!! info "Setting domain properties requires tenant-level Fabric Administrator privileges"

!!! warning "When setting an item definition, it is set without its sensitivity label"

**Usage:**

```
fab set <path> -q <jmespath_query> -i <input_value> [--raw-string] [-f]
```

**Parameters:**

- `<path>`: Path to the resource.
- `-q, --query <jmespath_query>`: JMESPath query to the property.
- `-i, --input <input_value>`: Input value to set.
- `--raw-string`: Keep input as literal string without JSON parsing. Use when setting item definition properties that expect JSON-encoded strings. Only relevant for set item command. Optional.
- `-f, --force`: Force set without confirmation. Optional.

**Example:**

```bash
fab set ws1.Workspace -q displayName -i "New Name" -f
```

## Setting Item Properties

The `set` command supports updating properties in two categories for items:

### 1. Item Metadata

- `displayName` - The display name of the item (all item types)
- `description` - The description of the item (all item types)
- `properties` - Custom properties (`.VariableLibrary` only)

### 2. Item Definition

Any explicit path (specified via the `-q` / `--query` command argument) to properties within the item's `definition` structure according to [Microsoft Fabric item definitions](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions).

### Limitations

- Only one property path can be specified per `-query` argument
- Paths must map directly to JSON paths without filters or wildcards
- Only paths already present in the item definition can be updated. Properties with default values may not appear when retrieved via `get` unless explicitly set previously.

### Common Item-Specific Definition Property Paths

These are friendly names that map to specific paths in the item's definition structure. When using the `set` command, you can use these names directly (as the `-query` / `--q` argument value) as they map to the correct definition paths:

- **Notebook**: `lakehouse`, `environment`, `warehouse`
- **Report**: `semanticModelId` (applies only to [Report definition.pbir version 1](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report?tabs=v1%2Cdesktop#definitionpbir). For other versions, check the correct property path in the Report definition documentation)
- **SparkJobDefinition**: `payload`
